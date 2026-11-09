"""Mapa de localização dos biomas brasileiros e dos pontos de amostragem do experimento.

Lê os limites dos biomas (`configs/regions/br_biomes.geojson`) e as regiões do experimento:
os produtos e biomas de `configs/experiment.yaml`, com os pontos que o `download` de cada
produto cobre (tabela `points_file` e filtros de `configs/datasets.yaml`). A figura segue o
estilo das figuras do `compare` (fonte serifada, largura de página dupla) e tem:
  - (a) os biomas do experimento, os estados e os pontos de amostragem marcados por critério,
    com grade de coordenadas, escala, norte e mapa de localização no Brasil;
  - (b) quando o experimento tem produtos em grade (GOES, OISST), os recortes deles em escala;
  - a legenda dos critérios, dos produtos em grade e, com todos os biomas, dos biomas.

Os países vizinhos vêm do Natural Earth (domínio público), baixado uma vez para
`data_basemap/`; sem rede e sem o arquivo, o fundo cai para tiles da Esri.

Uso:
    python scripts/generate_biomes_location_map.py
    python scripts/generate_biomes_location_map.py --output artifacts/figures/mapa_biomas.png
    python scripts/generate_biomes_location_map.py --output artifacts/figures/mapa_biomas.pdf
    python scripts/generate_biomes_location_map.py --biome all
    python scripts/generate_biomes_location_map.py --points configs/regions/br_biomes_points.csv
"""

from __future__ import annotations

import argparse
import logging
import math
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEOJSON_PATH = REPO_ROOT / "configs" / "regions" / "br_biomes.geojson"
DEFAULT_EXPERIMENT_PATH = REPO_ROOT / "configs" / "experiment.yaml"
DEFAULT_DATASETS_PATH = REPO_ROOT / "configs" / "datasets.yaml"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "artifacts" / "figures" / "mapa_localizacao_biomas.png"
DEFAULT_COUNTRIES_PATH = REPO_ROOT / "data_basemap" / "ne_50m_admin_0_countries.geojson"
# Versão fixa do Natural Earth: o contorno dos vizinhos não muda entre execuções.
NATURAL_EARTH_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/"
    "ne_50m_admin_0_countries.geojson"
)

# CRS equal-area apropriado para o território brasileiro (SIRGAS 2000 / Brazil Polyconic).
CRS_EQUAL_AREA = "EPSG:5880"
# Janela (lon/lat) em que os países são recortados antes de projetar: fora dela a policônica
# distorce demais e geometrias que cruzam o antimeridiano viram faixas espúrias.
COUNTRIES_WINDOW = (-100.0, -60.0, -10.0, 20.0)

# Largura de página dupla (pol.): a figura entra no artigo sem reescala, com as fontes no
# tamanho final.
FIGURE_WIDTH_IN = 7.2
MAX_MAP_HEIGHT_IN = 5.0

BIOME_COLORS = {
    "Amazônia": "#2a6f4d",
    "Caatinga": "#c98a3a",
    "Cerrado": "#d9b23c",
    "Mata Atlântica": "#3f7d3f",
    "Pampa": "#8fae5c",
    "Pantanal": "#4f9dc4",
}

CRITERION_LABELS = {
    "deforestation": "Desmatamento",
    "crop": "Agricultura",
    "native_vegetation": "Vegetação nativa",
    "fire": "Fogo",
    "pasture": "Pastagem",
    "silviculture": "Silvicultura",
    "urban": "Urbano",
    "mining": "Mineração",
}

# Paleta Okabe-Ito (distinguível com daltonismo) e um marcador por critério, para a figura
# continuar legível em escala de cinza.
CRITERION_STYLES = {
    "deforestation": {"color": "#D55E00", "marker": "o"},
    "crop": {"color": "#E69F00", "marker": "s"},
    "native_vegetation": {"color": "#009E73", "marker": "^"},
    "fire": {"color": "#CC79A7", "marker": "D"},
    "pasture": {"color": "#F0E442", "marker": "v"},
    "silviculture": {"color": "#56B4E9", "marker": "P"},
    "urban": {"color": "#000000", "marker": "X"},
    "mining": {"color": "#0072B2", "marker": "h"},
}

BIOME_SLUG_TO_NAME = {
    "amazonia": "Amazônia",
    "caatinga": "Caatinga",
    "cerrado": "Cerrado",
    "mata_atlantica": "Mata Atlântica",
    "pampa": "Pampa",
    "pantanal": "Pantanal",
}

GRID_PRODUCT_LABELS = {
    "goes_abi": "GOES-16 ABI",
    "noaa_oisst": "NOAA OISST",
}

# Cores fora da paleta dos critérios, para o recorte de um produto em grade nunca ser lido
# como um critério de amostragem.
GRID_PRODUCT_STYLES = [
    {"color": "#332288", "marker": "s"},
    {"color": "#882255", "marker": "o"},
    {"color": "#117733", "marker": "D"},
    {"color": "#AA4499", "marker": "^"},
]

REGIME_LABELS = {
    "amazonia_convectiva": "Amazônia convectiva",
    "cerrado_convectivo": "Cerrado convectivo",
    "atlantico_nordeste": "Atlântico Nordeste",
    "atlantico_sudeste": "Atlântico Sudeste",
    "atlantico_sul": "Atlântico Sul",
}

# Rótulo de território que o Natural Earth junta a outro país.
COUNTRY_LABEL_OVERRIDES = {"FRA": "Guiana Francesa"}

TEXT_COLOR = "#1f1f1f"
MUTED_TEXT = "#5f5f5f"
OCEAN_COLOR = "#dfe9f1"
OCEAN_TEXT = "#55708c"
NEIGHBOR_FILL = "#ebebe8"
NEIGHBOR_EDGE = "#a9a9a4"
BRAZIL_FILL = "#fbfbf9"
BRAZIL_EDGE = "#3a3a3a"
STATE_EDGE = "#8f8f8f"

FONT_TITLE = 9.0
FONT_LEGEND = 7.5
FONT_MAP = 7.0
FONT_SMALL = 6.3


def _fix_biome_encoding(gdf, column: str = "bioma"):
    def _fix(value):
        try:
            return str(value).encode("latin1").decode("utf-8")
        except Exception:
            return str(value)

    gdf[column] = gdf[column].apply(_fix)
    return gdf


def _pale(color: str, weight: float = 0.28) -> tuple[float, float, float]:
    """Mistura `color` com branco: preenchimento claro que deixa os pontos em evidência."""
    from matplotlib.colors import to_rgb

    r, g, b = to_rgb(color)
    return (1 - weight + weight * r, 1 - weight + weight * g, 1 - weight + weight * b)


def _halo(width: float = 2.2):
    import matplotlib.patheffects as pe

    return [pe.withStroke(linewidth=width, foreground="white")]


def _label_point(geom, obstacles: list, min_distance: float, inner=None):
    """Ponto dentro de `geom` para um rótulo, o mais central possível sem encostar em `obstacles`.

    Os candidatos são o polo de inacessibilidade e uma grade de pontos internos, em ordem de
    distância a ele; vale o primeiro a pelo menos `min_distance` de todos os obstáculos (pontos
    amostrais e rótulos já postos). `inner` restringe os candidatos (ex.: o quadro sem a margem,
    para o texto não sair do mapa). Sem candidato livre, devolve None e o rótulo é omitido.
    """
    import numpy as np
    from shapely.geometry import Point
    from shapely.ops import polylabel

    if inner is not None:
        geom = geom.intersection(inner)
    if geom.is_empty:
        return None
    largest = max(getattr(geom, "geoms", [geom]), key=lambda part: part.area)
    if largest.geom_type != "Polygon":
        return None
    center = polylabel(largest, tolerance=max(largest.length / 500, 1.0))
    xmin, ymin, xmax, ymax = largest.bounds
    grid = [Point(x, y) for x in np.linspace(xmin, xmax, 14) for y in np.linspace(ymin, ymax, 14)]
    candidates = [center] + sorted((pt for pt in grid if largest.contains(pt)), key=center.distance)
    for candidate in candidates:
        if all(candidate.distance(obstacle) >= min_distance for obstacle in obstacles):
            return candidate
    return None


def load_countries(path: Path):
    """Países da janela sul-americana no CRS do mapa; None se o arquivo não existe e não baixa."""
    import geopandas as gpd
    from shapely.geometry import box

    if not path.exists():
        import urllib.request

        logger.info("Baixando os limites de países do Natural Earth para %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix + ".part")
        try:
            urllib.request.urlretrieve(NATURAL_EARTH_URL, partial)
            partial.replace(path)
        except Exception as error:
            partial.unlink(missing_ok=True)
            logger.warning("Natural Earth indisponível (%s); o fundo usa tiles da Esri.", error)
            return None
    countries = gpd.read_file(path)[["NAME_PT", "ADM0_A3", "geometry"]]
    countries = gpd.clip(countries, box(*COUNTRIES_WINDOW))
    countries = countries[~countries.geometry.is_empty]
    return countries.to_crs(CRS_EQUAL_AREA)


def draw_base(ax, countries, brazil, extent, *, label_countries: bool, obstacles: list | None = None,
              reserved=None, min_label_share: float = 0.012) -> list:
    """Oceano, países vizinhos com nome em português e o território brasileiro.

    Devolve os pontos dos rótulos postos, para os rótulos seguintes desviarem deles.
    """
    from shapely.geometry import box

    x0, y0, x1, y1 = extent
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)
        spine.set_color("#333333")

    if countries is None:
        try:
            import contextily as ctx

            ctx.add_basemap(ax, crs=CRS_EQUAL_AREA, source=ctx.providers.Esri.WorldGrayCanvas, zorder=0,
                            attribution_size=4)
        except Exception:
            logger.warning("Não foi possível carregar o basemap; seguindo sem ele.")
        brazil.plot(ax=ax, facecolor=BRAZIL_FILL, edgecolor="none", zorder=1)
        return []

    ax.set_facecolor(OCEAN_COLOR)
    neighbors = countries[countries["ADM0_A3"] != "BRA"]
    neighbors.plot(ax=ax, facecolor=NEIGHBOR_FILL, edgecolor=NEIGHBOR_EDGE, linewidth=0.4, zorder=1)
    brazil.plot(ax=ax, facecolor=BRAZIL_FILL, edgecolor="none", zorder=1)
    if not label_countries:
        return []

    frame = box(x0, y0, x1, y1)
    inner = box(x0 + 0.06 * (x1 - x0), y0 + 0.04 * (y1 - y0), x1 - 0.06 * (x1 - x0), y1 - 0.04 * (y1 - y0))
    if reserved is not None:
        inner = inner.difference(reserved)
    placed: list = []
    min_distance = 0.07 * (x1 - x0)
    for _, row in neighbors.iterrows():
        piece = row.geometry.intersection(frame)
        if piece.is_empty or piece.area < min_label_share * frame.area:
            continue
        point = _label_point(piece, [*(obstacles or []), *placed], min_distance, inner)
        if point is None:
            continue
        name = COUNTRY_LABEL_OVERRIDES.get(row["ADM0_A3"], row["NAME_PT"])
        ax.text(point.x, point.y, name, fontsize=FONT_SMALL, style="italic", color=MUTED_TEXT,
                ha="center", va="center", zorder=6, path_effects=_halo(1.6))
        placed.append(point)
    ocean = frame.difference(countries.union_all().union(brazil.union_all()))
    if not ocean.is_empty and ocean.area > 0.05 * frame.area:
        point = _label_point(ocean, [*(obstacles or []), *placed], min_distance, inner)
        if point is not None:
            ax.text(point.x, point.y, "Oceano\nAtlântico", fontsize=FONT_SMALL, style="italic", color=OCEAN_TEXT,
                    ha="center", va="center", zorder=6, linespacing=1.0)
            placed.append(point)
    return placed


def _degree_label(value: float, axis: str) -> str:
    if abs(value) < 1e-9:
        return "0°"
    hemisphere = ("L" if value > 0 else "O") if axis == "lon" else ("N" if value > 0 else "S")
    return f"{abs(value):g}°{hemisphere}"


def add_graticule(ax, step: float) -> None:
    """Meridianos e paralelos a cada `step` graus, rotulados na base e à esquerda do quadro."""
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import LineString

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    lon_min, lat_min, lon_max, lat_max = COUNTRIES_WINDOW
    bottom = LineString([(x0, y0), (x1, y0)])
    left = LineString([(x0, y0), (x0, y1)])
    margin_x, margin_y = 0.04 * (x1 - x0), 0.04 * (y1 - y0)

    def projected(points):
        return gpd.GeoSeries([LineString(points)], crs="EPSG:4326").to_crs(CRS_EQUAL_AREA).iloc[0]

    for lon in np.arange(math.ceil(lon_min / step) * step, lon_max + 1e-9, step):
        line = projected([(lon, lat) for lat in np.linspace(lat_min, lat_max, 160)])
        ax.plot(*line.xy, color="#7a7a7a", linewidth=0.3, linestyle=(0, (2, 2)), zorder=2.5)
        hit = line.intersection(bottom)
        if not hit.is_empty and x0 + margin_x < hit.centroid.x < x1 - margin_x:
            ax.annotate(_degree_label(lon, "lon"), (hit.centroid.x, y0), xytext=(0, -2.5), textcoords="offset points",
                        ha="center", va="top", fontsize=FONT_SMALL, color=TEXT_COLOR, annotation_clip=False)
    for lat in np.arange(math.ceil(lat_min / step) * step, lat_max + 1e-9, step):
        line = projected([(lon, lat) for lon in np.linspace(lon_min, lon_max, 160)])
        ax.plot(*line.xy, color="#7a7a7a", linewidth=0.3, linestyle=(0, (2, 2)), zorder=2.5)
        hit = line.intersection(left)
        if not hit.is_empty and y0 + margin_y < hit.centroid.y < y1 - margin_y:
            ax.annotate(_degree_label(lat, "lat"), (x0, hit.centroid.y), xytext=(-2.5, 0), textcoords="offset points",
                        ha="right", va="center", rotation=90, fontsize=FONT_SMALL, color=TEXT_COLOR,
                        annotation_clip=False)


def add_north_arrow(ax, x: float = 0.955, y: float = 0.80, length: float = 0.10) -> None:
    ax.annotate("", xy=(x, y + length), xytext=(x, y), xycoords="axes fraction",
                arrowprops=dict(facecolor=TEXT_COLOR, edgecolor=TEXT_COLOR, width=1.4, headwidth=6.5,
                                headlength=7), zorder=12)
    ax.text(x, y + length + 0.012, "N", transform=ax.transAxes, ha="center", va="bottom", fontsize=FONT_MAP + 1,
            fontweight="bold", color=TEXT_COLOR, zorder=12)


def add_scale_bar(ax, x_right: float = 0.90, y: float = 0.045) -> None:
    """Barra de dois segmentos com comprimento redondo perto de 1/5 da largura do quadro."""
    import matplotlib.patches as mpatches

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    width_km = (x1 - x0) / 1000
    length_km = min((50, 100, 200, 250, 500, 1000, 2000), key=lambda km: abs(km - width_km / 5))
    end = x0 + x_right * (x1 - x0)
    start = end - length_km * 1000
    base = y0 + y * (y1 - y0)
    height = 0.012 * (y1 - y0)
    margin_x, margin_y = 0.02 * (x1 - x0), 0.02 * (y1 - y0)
    unit_width = 0.045 * (x1 - x0)
    ax.add_patch(mpatches.FancyBboxPatch(
        (start - margin_x, base - margin_y), end - start + 2 * margin_x + unit_width, height + 0.075 * (y1 - y0),
        boxstyle=f"round,pad=0,rounding_size={0.01 * (x1 - x0)}", facecolor="white", edgecolor="#9a9a9a",
        linewidth=0.4, alpha=0.9, zorder=11))
    for index, color in enumerate((TEXT_COLOR, "white")):
        ax.add_patch(mpatches.Rectangle((start + index * (end - start) / 2, base), (end - start) / 2, height,
                                        facecolor=color, edgecolor=TEXT_COLOR, linewidth=0.6, zorder=12))
    for fraction, text in ((0.0, "0"), (0.5, f"{length_km / 2:g}"), (1.0, f"{length_km:g}")):
        ax.text(start + fraction * (end - start), base + height + 0.008 * (y1 - y0), text, ha="center", va="bottom",
                fontsize=FONT_SMALL, color=TEXT_COLOR, zorder=12)
    ax.text(end + 0.012 * (x1 - x0), base + height / 2, "km", ha="left", va="center", fontsize=FONT_SMALL,
            color=TEXT_COLOR, zorder=12)


def add_locator(ax, countries, biomas_all, brazil, biome_names: list[str], bounds) -> None:
    """Mapa de localização no canto inferior esquerdo: o Brasil com os biomas do mapa em destaque."""
    inset = ax.inset_axes(bounds)
    xmin, ymin, xmax, ymax = biomas_all.total_bounds
    pad = 0.05 * max(xmax - xmin, ymax - ymin)
    extent = (xmin - pad, ymin - pad, xmax + pad, ymax + pad)
    draw_base(inset, countries, brazil, extent, label_countries=False)
    biomas_all.plot(ax=inset, facecolor="#d9d9d4", edgecolor="white", linewidth=0.25, zorder=2)
    highlight = biomas_all[biomas_all["bioma"].isin(biome_names)]
    for biome, subset in highlight.groupby("bioma"):
        subset.plot(ax=inset, facecolor=BIOME_COLORS.get(biome, "#555555"), edgecolor="none", zorder=3)
    brazil.boundary.plot(ax=inset, linewidth=0.5, edgecolor=BRAZIL_EDGE, zorder=4)
    for spine in inset.spines.values():
        spine.set_linewidth(0.6)


def _footprint_text(product: dict) -> str:
    patch_px = product["patch_px"]
    if product["resolution_deg"] is not None:
        res = product["resolution_deg"]
        return f"{patch_px} px × {res:g}° = {patch_px * res:g}°"
    res_km = product["resolution_m"] / 1000
    return f"{patch_px} px × {res_km:g} km = {patch_px * res_km:g} km"


def grid_footprints(products: list[dict]):
    """Recorte de cada ponto dos produtos em grade, em escala, no CRS do mapa.

    O recorte é aproximado: um quadrado de `patch_px` células centrado no ponto (em graus quando
    a grade é em graus; em metros no CRS equal-area quando é em metros).
    """
    import geopandas as gpd
    from shapely.geometry import box

    rows = []
    for index, product in enumerate(products):
        style = GRID_PRODUCT_STYLES[index % len(GRID_PRODUCT_STYLES)]
        table = product["points"]
        if product["resolution_deg"] is not None:
            half = product["patch_px"] * product["resolution_deg"] / 2
            shapes = gpd.GeoSeries(
                [box(lon - half, lat - half, lon + half, lat + half) for lon, lat in zip(table["lon"], table["lat"])],
                crs="EPSG:4326",
            ).segmentize(0.25).to_crs(CRS_EQUAL_AREA)
        else:
            half = product["patch_px"] * product["resolution_m"] / 2
            centers = gpd.GeoSeries(gpd.points_from_xy(table["lon"], table["lat"]), crs="EPSG:4326").to_crs(CRS_EQUAL_AREA)
            shapes = gpd.GeoSeries([box(p.x - half, p.y - half, p.x + half, p.y + half) for p in centers], crs=CRS_EQUAL_AREA)
        for shape, regime in zip(shapes, table["biome"]):
            rows.append({"product": product["name"], "regime": regime, **style, "geometry": shape})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS_EQUAL_AREA)


def grid_panel_extent(biomas_all, footprints) -> tuple[float, float, float, float]:
    """Brasil inteiro mais os recortes dos produtos em grade, com margem (maior à direita, onde
    ficam os rótulos dos regimes no mar)."""
    xmin, ymin, xmax, ymax = biomas_all.total_bounds
    fxmin, fymin, fxmax, fymax = footprints.total_bounds
    xmin, ymin, xmax, ymax = min(xmin, fxmin), min(ymin, fymin), max(xmax, fxmax), max(ymax, fymax)
    pad = max(xmax - xmin, ymax - ymin) * 0.04
    return xmin - pad, ymin - pad, xmax + pad + (xmax - xmin) * 0.20, ymax + pad


def draw_grid_products_panel(ax, countries, biomas_all, brazil, highlight_names: list[str], footprints,
                             extent) -> None:
    """Produtos em grade (pontos fora dos biomas) com o recorte de cada ponto em escala."""
    draw_base(ax, countries, brazil, extent, label_countries=False)
    for biome in highlight_names:
        subset = biomas_all[biomas_all["bioma"] == biome]
        subset.plot(ax=ax, facecolor=_pale(BIOME_COLORS[biome]), edgecolor="none", zorder=2)
    brazil.boundary.plot(ax=ax, linewidth=0.6, edgecolor=BRAZIL_EDGE, zorder=3)
    add_graticule(ax, step=10)
    land = brazil.geometry.iloc[0]
    x0, y0, x1, y1 = extent
    pad = 0.02 * max(x1 - x0, y1 - y0)

    for (_, color), group in footprints.groupby(["product", "color"], sort=False):
        group.plot(ax=ax, facecolor=color, edgecolor="none", alpha=0.18, zorder=4)
        group.boundary.plot(ax=ax, edgecolor=color, linewidth=0.7, zorder=5)
        centers = group.geometry.centroid
        ax.scatter(centers.x, centers.y, s=10, marker=group["marker"].iloc[0], c=color, edgecolors="white",
                   linewidths=0.4, zorder=6)

    # Em terra o rótulo vai abaixo do grupo, para não cobrir os recortes no mar, que ficam à direita
    # da costa; no mar ele vai à direita, longe do continente.
    for (_, regime), group in footprints.groupby(["product", "regime"], sort=False):
        gxmin, gymin, gxmax, gymax = group.total_bounds
        label = REGIME_LABELS.get(regime, regime.replace("_", " "))
        if land.contains(group.geometry.union_all().centroid):
            position = {"x": (gxmin + gxmax) / 2, "y": gymin - pad * 0.4, "ha": "center", "va": "top"}
        else:
            position = {"x": gxmax + pad * 0.4, "y": (gymin + gymax) / 2, "ha": "left", "va": "center"}
        ax.text(position["x"], position["y"], label.replace(" ", "\n", 1), ha=position["ha"], va=position["va"],
                fontsize=FONT_SMALL, color=TEXT_COLOR, zorder=7, linespacing=1.0, path_effects=_halo(1.8))


def experiment_points(experiment_path: Path, datasets_path: Path, biome_slugs: list[str] | None):
    """Pontos que o `download` dos produtos do experimento cobre nos biomas pedidos.

    Usa a tabela `points_file` e os filtros de `datasets.yaml` (`max_regions_per_biome`,
    `strata_target_filter`) de cada produto, como o `download`; um ponto presente em vários
    produtos aparece uma vez. Sem `biome_slugs`, valem os `biomes` de `experiment.yaml`.
    Produtos cuja tabela tem outros grupos (regime convectivo, regime oceânico) voltam à parte,
    com os grupos que o experimento roda, para o mapa auxiliar.
    """
    import pandas as pd

    from sits_forecasting.data.dataset_registry import DatasetRegistry
    from sits_forecasting.data.downloaders import _limit_points_per_biome, _load_points_table
    from sits_forecasting.utils.config import load_experiment_config

    config = load_experiment_config(experiment_path)
    registry = DatasetRegistry(datasets_path, config.patch_size_px)
    wanted = biome_slugs or config.biomes or sorted(BIOME_SLUG_TO_NAME)
    unknown = sorted(set(wanted) - set(BIOME_SLUG_TO_NAME))
    if unknown:
        raise ValueError(f"biomas sem limite no mapa: {unknown}. Opções: {sorted(BIOME_SLUG_TO_NAME)}")

    frames, grid_products, skipped = [], [], []
    for name in config.datasets:
        dataset_config = registry.get_dataset_config(name)
        if not registry.has_biome_splits(name):
            skipped.append(name)
            continue
        points = _limit_points_per_biome(_load_points_table(dataset_config), dataset_config)
        if not points["biome"].isin(list(BIOME_SLUG_TO_NAME)).any():
            groups = registry.resolve_splits(name, config.biomes)
            grid_products.append({
                "name": name,
                "label": GRID_PRODUCT_LABELS.get(name, name),
                "points": points[points["biome"].isin(groups)].reset_index(drop=True),
                "patch_px": int(dataset_config["patch_size_px"]),
                "resolution_deg": dataset_config.get("resolution_deg"),
                "resolution_m": dataset_config.get("resolution_m"),
            })
            continue
        points = points[points["biome"].isin(wanted)]
        if points.empty:
            skipped.append(name)
            continue
        frames.append(points.assign(dataset=name))
    if skipped:
        logger.info("Produtos sem pontos nos biomas %s (fora do mapa): %s", wanted, ", ".join(skipped))
    if grid_products:
        logger.info("Produtos em grade no mapa auxiliar: %s", ", ".join(p["name"] for p in grid_products))
    if not frames:
        raise SystemExit(f"Nenhum produto de {experiment_path} tem pontos nos biomas {wanted}.")

    table = pd.concat(frames, ignore_index=True)
    points = table.drop_duplicates(["biome", "point_id", "lat", "lon", "criterion"]).drop(columns="dataset")
    points = points.sort_values(["biome", "point_id"], kind="stable").reset_index(drop=True)

    for biome, count in points.groupby("biome").size().items():
        if config.max_regions and count > config.max_regions:
            logger.warning(
                "%s: %d pontos, mas o prepare usa no máximo %d regiões por cenário (max_regions); "
                "o mapa mostra todos os pontos baixados.", biome, count, config.max_regions,
            )
    logger.info(
        "%d pontos de %d produto(s) em %s.", len(points), len(frames), ", ".join(sorted(points["biome"].unique()))
    )
    return points, wanted, grid_products


def table_points(points_path: Path, biome_slugs: list[str] | None):
    """Pontos lidos direto de uma tabela, nos biomas pedidos (todos, sem `biome_slugs`)."""
    import pandas as pd

    points = pd.read_csv(points_path)
    wanted = biome_slugs or sorted(points["biome"].dropna().unique())
    return points[points["biome"].isin(wanted)].reset_index(drop=True), wanted


def _padded(bounds, fraction: float) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bounds
    pad = fraction * max(xmax - xmin, ymax - ymin)
    return xmin - pad, ymin - pad, xmax + pad, ymax + pad


def _aspect(extent) -> float:
    x0, y0, x1, y1 = extent
    return (x1 - x0) / (y1 - y0)


def _panel_title(ax, letter: str, text: str) -> None:
    ax.set_title(rf"$\mathbf{{({letter})}}$ {text}", loc="left", fontsize=FONT_TITLE, color=TEXT_COLOR, pad=4)


def _legends(fig, points, grid_products, criterion_counts, biome_counts, all_biomes: bool, anchors) -> None:
    """Legenda abaixo dos painéis: critérios sob (a); produtos em grade sob (b)."""
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D

    common = dict(frameon=False, fontsize=FONT_LEGEND, title_fontsize=FONT_LEGEND + 0.5, loc="upper left",
                  handletextpad=0.4, columnspacing=1.1, labelspacing=0.45, borderaxespad=0.0, alignment="left")
    criteria = [c for c in CRITERION_STYLES if criterion_counts.get(c, 0) > 0]
    handles = [
        Line2D([], [], linestyle="", marker=CRITERION_STYLES[c]["marker"], markersize=5.5,
               markerfacecolor=CRITERION_STYLES[c]["color"], markeredgecolor="#1a1a1a", markeredgewidth=0.5,
               label=f"{CRITERION_LABELS.get(c, c)} ({criterion_counts[c]})")
        for c in criteria
    ]
    if all_biomes:
        handles += [
            mpatches.Patch(facecolor=_pale(color, 0.55), edgecolor=color, linewidth=0.6,
                           label=f"{biome} ({biome_counts.get(biome, 0)})")
            for biome, color in BIOME_COLORS.items()
        ]
    n_cols = 3 if len(handles) > 6 else 2
    fig.legend(handles=handles, ncol=n_cols, bbox_to_anchor=anchors[0],
               title=f"Critério de amostragem ({len(points)} regiões)", **common)
    if grid_products:
        grid_handles = [
            Line2D([], [], linestyle="", marker=style["marker"], markersize=5.5, markerfacecolor=style["color"],
                   markeredgecolor="white", markeredgewidth=0.4,
                   label=f"{product['label']}: {len(product['points'])} pontos, recorte {_footprint_text(product)}")
            for product, style in zip(grid_products, GRID_PRODUCT_STYLES * len(grid_products))
        ]
        fig.legend(handles=grid_handles, ncol=1, bbox_to_anchor=anchors[1], title="Produtos em grade", **common)


def build_map(
    geojson_path: Path,
    points_df,
    output_path: Path,
    biome_slugs: list[str],
    grid_products: list[dict] | None = None,
    countries_path: Path = DEFAULT_COUNTRIES_PATH,
) -> None:
    warnings.filterwarnings("ignore")

    import geobr
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import box

    from sits_forecasting.comparison.figures import STYLE

    biomas = gpd.read_file(geojson_path)
    _fix_biome_encoding(biomas, "bioma")
    biomas = biomas.to_crs(CRS_EQUAL_AREA)
    biomas_all = biomas.copy()

    points = gpd.GeoDataFrame(
        points_df,
        geometry=gpd.points_from_xy(points_df["lon"], points_df["lat"]),
        crs="EPSG:4326",
    ).to_crs(CRS_EQUAL_AREA)
    points["bioma"] = points["biome"].map(BIOME_SLUG_TO_NAME)

    biome_names = [BIOME_SLUG_TO_NAME[slug] for slug in biome_slugs]
    all_biomes = set(biome_slugs) == set(BIOME_SLUG_TO_NAME)
    if not all_biomes:
        biomas = biomas[biomas["bioma"].isin(biome_names)].copy()

    countries = load_countries(countries_path)
    estados = geobr.read_state(year=2020, show_progress=False).to_crs(CRS_EQUAL_AREA)
    # Contorno do país só com os anéis externos: entre os polígonos simplificados dos estados (e
    # dos biomas) sobram buracos de poucos pixels que apareceriam como pontos pretos no interior.
    from shapely.geometry import MultiPolygon, Polygon

    union = estados.union_all()
    shell = MultiPolygon([Polygon(part.exterior) for part in getattr(union, "geoms", [union])])
    brazil_land = gpd.GeoDataFrame(geometry=[shell], crs=CRS_EQUAL_AREA)

    main_extent = _padded(biomas.total_bounds, 0.035)
    grid_products = [product for product in grid_products or [] if not product["points"].empty]
    footprints = grid_footprints(grid_products) if grid_products else None
    grid_extent = grid_panel_extent(biomas_all, footprints) if grid_products else None

    # Painéis com a mesma altura e larguras proporcionais ao aspecto de cada mapa: o quadro do
    # mapa ocupa o eixo inteiro, sem faixas brancas. Medidas em polegadas.
    left, right, gap, top, bottom_labels = 0.22, 0.04, 0.34, 0.24, 0.16
    legend_height = 0.95 if (grid_products or all_biomes or len(points["criterion"].unique()) > 4) else 0.7
    aspects = [_aspect(main_extent)] + ([_aspect(grid_extent)] if grid_products else [])
    available = FIGURE_WIDTH_IN - left - right - gap * (len(aspects) - 1)
    map_height = min(available / sum(aspects), MAX_MAP_HEIGHT_IN)
    widths = [map_height * aspect for aspect in aspects]
    fig_width = left + right + gap * (len(aspects) - 1) + sum(widths)
    fig_height = top + map_height + bottom_labels + legend_height

    def frac_box(x_in: float, width_in: float) -> list[float]:
        return [x_in / fig_width, (bottom_labels + legend_height) / fig_height, width_in / fig_width,
                map_height / fig_height]

    with plt.rc_context({**STYLE, "mathtext.fontset": "stix"}):
        fig = plt.figure(figsize=(fig_width, fig_height), facecolor="white")
        ax = fig.add_axes(frac_box(left, widths[0]))
        point_obstacles = list(points.geometry)
        x0, y0, x1, y1 = main_extent

        def axes_box(fx0: float, fy0: float, fx1: float, fy1: float):
            return box(x0 + fx0 * (x1 - x0), y0 + fy0 * (y1 - y0), x0 + fx1 * (x1 - x0), y0 + fy1 * (y1 - y0))

        # Áreas do mapa de localização, da escala e do norte: nenhum rótulo cai embaixo delas.
        locator_bounds = [0.0, 0.0, 0.22, 0.26]
        reserved = axes_box(0.0, 0.0, 0.25, 0.30).union(axes_box(0.62, 0.0, 1.0, 0.16)).union(
            axes_box(0.90, 0.74, 1.0, 1.0))
        placed = draw_base(ax, countries, brazil_land, main_extent, label_countries=True, obstacles=point_obstacles,
                           reserved=None if all_biomes else reserved)

        for biome, color in BIOME_COLORS.items():
            subset = biomas[biomas["bioma"] == biome]
            if not subset.empty:
                subset.plot(ax=ax, facecolor=_pale(color), edgecolor="none", zorder=2)
        estados.boundary.plot(ax=ax, linewidth=0.35, edgecolor=STATE_EDGE, zorder=3)
        for biome, color in BIOME_COLORS.items():
            subset = biomas[biomas["bioma"] == biome]
            if not subset.empty:
                subset.boundary.plot(ax=ax, linewidth=0.8, edgecolor=color, zorder=3.5)
        brazil_land.boundary.plot(ax=ax, linewidth=0.7, edgecolor=BRAZIL_EDGE, zorder=4)
        add_graticule(ax, step=5 if not all_biomes else 10)

        inner = axes_box(0.03, 0.03, 0.97, 0.97).difference(
            reserved if not all_biomes else axes_box(0.62, 0.0, 1.0, 0.16).union(axes_box(0.90, 0.74, 1.0, 1.0)))
        for _, row in estados.iterrows():
            point = _label_point(row.geometry, [*point_obstacles, *placed], 0.035 * (x1 - x0), inner)
            if point is not None:
                ax.text(point.x, point.y, row["abbrev_state"], fontsize=FONT_SMALL, color="#6e6e6e",
                        ha="center", va="center", zorder=5, path_effects=_halo(1.6))
                placed.append(point)

        for criterion, style in CRITERION_STYLES.items():
            subset = points[points["criterion"] == criterion]
            if subset.empty:
                continue
            ax.scatter(subset.geometry.x, subset.geometry.y, s=34, marker=style["marker"], c=style["color"],
                       edgecolors="#1a1a1a", linewidths=0.55, zorder=10)

        add_north_arrow(ax)
        add_scale_bar(ax)
        if not all_biomes:
            add_locator(ax, countries, biomas_all, brazil_land, biome_names, bounds=locator_bounds)

        biome_counts = points.groupby("bioma").size().to_dict()
        criterion_counts = points.groupby("criterion").size().to_dict()
        region = "biomas brasileiros" if all_biomes else ", ".join(biome_names)
        _panel_title(ax, "a", f"Pontos de amostragem: {region}")

        legend_top = (legend_height + 0.02) / fig_height
        anchors = [(left / fig_width, legend_top)]
        if grid_products:
            x_grid = left + widths[0] + gap
            ax_grid = fig.add_axes(frac_box(x_grid, widths[1]))
            draw_grid_products_panel(ax_grid, countries, biomas_all, brazil_land, biome_names, footprints,
                                     grid_extent)
            _panel_title(ax_grid, "b", "Produtos em grade (recortes em escala)")
            anchors.append((x_grid / fig_width, legend_top))
        _legends(fig, points, grid_products, criterion_counts, biome_counts, all_biomes, anchors)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        plt.close(fig)
    logger.info("Mapa salvo em: %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--geojson", type=Path, default=DEFAULT_GEOJSON_PATH, help="Limites dos biomas (GeoJSON).")
    parser.add_argument("--config", type=Path, default=DEFAULT_EXPERIMENT_PATH,
                        help="experiment.yaml: produtos (datasets) e biomas do mapa.")
    parser.add_argument("--datasets-config", type=Path, default=DEFAULT_DATASETS_PATH,
                        help="datasets.yaml: tabela de pontos e filtros de cada produto.")
    parser.add_argument("--points", type=Path, default=None,
                        help="Usa esta tabela de pontos (CSV) em vez dos produtos do experimento.")
    parser.add_argument("--countries", type=Path, default=DEFAULT_COUNTRIES_PATH,
                        help="Limites de países do Natural Earth (GeoJSON); baixado na primeira vez se não existir.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH,
                        help="Arquivo de saída; a extensão escolhe o formato (.png a 300 dpi, .pdf, .svg).")
    parser.add_argument(
        "--biome",
        nargs="+",
        choices=[*sorted(BIOME_SLUG_TO_NAME), "all"],
        default=None,
        help="Biomas do mapa (padrão: os de experiment.yaml; com --points, todos os da tabela); "
             "'all' = os seis.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    biome_slugs = sorted(BIOME_SLUG_TO_NAME) if args.biome and "all" in args.biome else args.biome
    grid_products: list[dict] = []
    if args.points is not None:
        points, biome_slugs = table_points(args.points, biome_slugs)
    else:
        points, biome_slugs, grid_products = experiment_points(args.config, args.datasets_config, biome_slugs)
    biome_slugs = [slug for slug in biome_slugs if slug in BIOME_SLUG_TO_NAME]
    output = args.output
    if set(biome_slugs) != set(BIOME_SLUG_TO_NAME) and output == DEFAULT_OUTPUT_PATH:
        output = output.with_stem(f"{output.stem}_{'_'.join(biome_slugs)}")
    build_map(args.geojson, points, output, biome_slugs, grid_products, args.countries)


if __name__ == "__main__":
    main()
