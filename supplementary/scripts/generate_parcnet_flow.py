"""Figura 2 - Fluxo horizontal do PARC-Net (tons de cinza), pronta para artigo.

A figura e gerada no tamanho real de impressao (largura FIG_W polegadas), de
modo que os tamanhos de fonte abaixo correspondem aos pontos impressos.
Inclua no LaTeX com \\includegraphics[width=\\textwidth]{...pdf} (ou largura
igual a FIG_W) para manter as fontes no tamanho indicado.

Dependencias: numpy, matplotlib (>= 3.5).
Execucao: python 02_gerar_fluxo_parcnet.py
Saida (mesma pasta): figura_parcnet_fluxo_horizontal_v4.{pdf,svg,png}
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon

# --------------------------------------------------------------------------
# Tipografia: texto e matematica na mesma familia serifada (STIX, estilo Times,
# incluida no matplotlib). Para Computer Modern, troque por 'cm' / 'cmr10'.
# --------------------------------------------------------------------------
FIG_W = 7.0                      # largura impressa (pol.) ~ texto em 2 colunas
plt.rcParams.update({
    'font.family': 'STIXGeneral',
    'mathtext.fontset': 'stix',
    'font.size': 8,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'svg.fonttype': 'none',
    'axes.unicode_minus': False,
})
FS_TITLE = 8.0      # titulos dos paineis
FS_MATH = 8.5       # equacoes
FS_TEXT = 7.5       # rotulos
FS_NOTE = 7.0       # notas e indices de tempo (minimo recomendado)

INK = '0.08'; SUB = '0.25'; NOTE = '0.30'

XMAX, YMAX = 15.9, 5.75
S = FIG_W / 16.0    # escala em relacao ao desenho original (para linhas)


def lw(v):
    return max(0.3, v * S * 1.35)


fig = plt.figure(figsize=(FIG_W, FIG_W * YMAX / XMAX))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, XMAX)
ax.set_ylim(0, YMAX)
ax.set_aspect('equal', adjustable='box')
ax.axis('off')


def add_box(x, y, w, h, title):
    ax.add_patch(Rectangle((x, y), w, h, facecolor='0.975', edgecolor='0.35',
                           linewidth=lw(1.1)))
    ax.text(x + w / 2, y + h - 0.17, title, ha='center', va='top',
            fontsize=FS_TITLE, color=INK, fontweight='bold')


def add_arrow(p0, p1, rad=0.0, width=1.45, ms=13, color='0.28', style='arc3'):
    cs = f'arc3,rad={rad}' if style == 'arc3' else style
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>',
                                 mutation_scale=ms * S * 1.5, linewidth=lw(width),
                                 color=color, connectionstyle=cs,
                                 shrinkA=0, shrinkB=0, zorder=5))


def txt(x, y, s, fs=FS_TEXT, color=SUB, **kw):
    kw.setdefault('ha', 'center'); kw.setdefault('va', 'center')
    return ax.text(x, y, s, fontsize=fs, color=color, **kw)


def draw_cube(x, y, w=1.15, dx=0.34, dy=0.19, layers=4, gap=0.30):
    for i in range(layers):
        yy = y + i * gap
        pts = np.array([[x, yy], [x + w, yy], [x + w + dx, yy + dy], [x + dx, yy + dy]])
        ax.add_patch(Polygon(pts, closed=True, facecolor=str(0.90 - 0.08 * i),
                             edgecolor='0.38', linewidth=lw(1.0)))
    top = (layers - 1) * gap
    for xx, yy in [(x, y), (x + w, y), (x + dx, y + dy), (x + w + dx, y + dy)]:
        ax.plot([xx, xx], [yy, yy + top], color='0.42', lw=lw(1.0))
    ap = dict(arrowstyle='-|>', lw=lw(1.1), color='0.20', mutation_scale=7)
    ax.annotate('', xy=(x - 0.22, y + top + dy + 0.03), xytext=(x - 0.22, y + 0.02), arrowprops=ap)
    txt(x - 0.40, y + top / 2 + dy / 2, r'$T_r$', fs=FS_MATH, color='0.2')
    ax.annotate('', xy=(x + w + 0.10, y - 0.08), xytext=(x + 0.05, y - 0.08), arrowprops=ap)
    txt(x + w / 2 + 0.05, y - 0.28, r'$W_r$', fs=FS_MATH, color='0.2')
    ax.annotate('', xy=(x + w + dx + 0.16, y + dy + 0.02), xytext=(x + w + 0.12, y - 0.10),
                arrowprops=ap)
    txt(x + w + dx + 0.18, y + 0.0, r'$H_r$', fs=FS_MATH, color='0.2', ha='left')


def draw_mask(x, y, rows=2, cols=8, size=0.17):
    ax.add_patch(Rectangle((x, y), cols * size, rows * size, facecolor='1.0',
                           edgecolor='0.45', lw=lw(0.9)))
    for i in range(1, cols):
        ax.plot([x + i * size] * 2, [y, y + rows * size], color='0.62', lw=lw(0.65))
    for j in range(1, rows):
        ax.plot([x, x + cols * size], [y + j * size] * 2, color='0.62', lw=lw(0.65))
    for cx, cy in [(0, 0), (2, 1), (5, 0), (6, 1)]:
        ax.add_patch(Rectangle((x + cx * size, y + cy * size), size, size,
                               facecolor='0.70', edgecolor='none'))


def draw_small_map(x, y, w=0.32, h=0.32, mask=False):
    n = 4
    cw, ch = w / n, h / n
    for i in range(n):
        for j in range(n):
            if mask:
                shade = 0.70 if (i * 3 + j * 5) % 7 == 0 else 0.98
            else:
                shade = min(0.90, max(0.57, 0.84 - 0.03 * i - 0.04 * j + 0.01 * ((i + j) % 2)))
            ax.add_patch(Rectangle((x + j * cw, y + i * ch), cw, ch, facecolor=str(shade),
                                   edgecolor='0.74', linewidth=lw(0.25)))
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor='0.42', linewidth=lw(0.8)))


# ------------------------------ paineis ------------------------------------
Y0, H = 0.62, 4.85                      # base e altura dos paineis altos
P1 = (0.15, Y0, 2.45, H)
P2 = (3.00, 1.45, 2.30, 3.40)
P3 = (5.70, Y0, 3.90, H)
P4 = (10.00, 1.65, 1.95, 2.85)
P5 = (12.35, Y0, 3.45, H)
TITLES = ['dados de entrada', 'ARIMA pooled', 'resíduos prequenciais',
          'CNN residual', 'composição híbrida']
for p, t in zip([P1, P2, P3, P4, P5], TITLES):
    add_box(*p, t)

YF = 3.20                               # altura do fluxo principal
for a, b in [(P1, P2), (P2, P3), (P3, P4), (P4, P5)]:
    add_arrow((a[0] + a[2], YF), (b[0], YF))

# 1. dados de entrada ----------------------------------------------------------
cx1 = P1[0] + P1[2] / 2
txt(cx1, 4.72, r'$Y^{(r)} \in \mathbb{R}^{T_r \times H_r \times W_r}$', fs=FS_MATH + 0.5, color=INK)
draw_cube(0.68, 2.75)
txt(cx1, 1.88, 'máscara de validade')
draw_mask(cx1 - 0.68, 1.30)
txt(cx1, 0.98, r'$y_t^{(i,j)} \rightarrow x_t^{(i,j)}$', fs=FS_MATH, color=INK)

# 2. ARIMA pooled ----------------------------------------------------------------
for yy, dy in zip([3.80, 3.18, 2.56],
                  [[0, .04, .03, .09, .08, .14, .18],
                   [0, .05, .10, .08, .13, .17, .15],
                   [0, .04, .03, .08, .11, .09, .15]]):
    ax.plot([3.25, 4.00], [yy, yy], color='0.25', lw=lw(1.0))
    ax.plot([3.25, 3.25], [yy, yy + 0.40], color='0.25', lw=lw(1.0))
    xs = np.linspace(3.35, 3.95, 7)
    ax.plot(xs, np.array(dy) + yy + 0.10, color='0.15', lw=lw(1.15),
            marker='o', ms=1.6, markeredgewidth=0)
ax.add_patch(Rectangle((4.32, 2.89), 0.75, 0.62, facecolor='0.90',
                       edgecolor='0.3', lw=lw(1.0)))
txt(4.695, 3.20, r'$\widehat{\theta}_{\tau}$', fs=FS_MATH + 0.5, color=INK)
add_arrow((4.03, 3.20), (4.32, 3.20), width=1.2, ms=10)
add_arrow((4.695, 2.89), (4.695, 2.36), width=1.2, ms=10)
txt(4.695, 2.05, r'$\widehat{x}^{B,(i,j)}_{t+1\mid t}$', fs=FS_MATH, color=INK)

# 3. residuos prequenciais ---------------------------------------------------------
cx3 = P3[0] + P3[2] / 2
txt(cx3, 4.68, r'$r_t^{(i,j)} = x_t^{(i,j)} - \widehat{x}^{B,(i,j)}_{t\mid t-1;\,\widehat{\theta}_{\tau}}$',
    fs=FS_MATH, color=INK)
txt(cx3, 4.22, r'com $\tau < t$', fs=FS_NOTE, color=NOTE)
txt(cx3, 3.82, '6 mapas residuais históricos')
xs0 = cx3 - (5 * 0.56 + 0.36) / 2
for k in range(6):
    draw_small_map(xs0 + 0.56 * k, 3.06, w=0.36, h=0.36)
for k, lab in enumerate([r'$t-5$', r'$t-4$', r'$t-3$', r'$t-2$', r'$t-1$', r'$t$']):
    txt(xs0 + 0.18 + 0.56 * k, 2.86, lab, fs=FS_NOTE, color=NOTE)
txt(cx3, 2.50, '+ máscaras de validade')
for k in range(6):
    draw_small_map(xs0 + 0.56 * k, 1.86, w=0.36, h=0.36, mask=True)
txt(cx3, 1.15, 'ajuste em prefixo temporal e previsão\n'
               'sequencial, sem usar o alvo para estimar\n'
               'seus próprios parâmetros',
    fs=FS_NOTE, color=NOTE, linespacing=1.25)

# 4. CNN residual -----------------------------------------------------------------
cx4 = P4[0] + P4[2] / 2
for i in range(4):
    ax.add_patch(Rectangle((cx4 - 0.53 + i * 0.22, 3.30 - i * 0.16), 0.40, 0.40,
                           facecolor='0.88', edgecolor='0.45', lw=lw(0.85)))
txt(cx4, 2.48, r'$\widehat{r}^{C,(i,j)}_{t+1\mid t}$', fs=FS_MATH, color=INK)
txt(cx4, 2.03, 'mapa de erro\nprevisto', linespacing=1.15)

# 5. composicao hibrida -------------------------------------------------------------
cx5 = P5[0] + P5[2] / 2
txt(cx5, 4.70, r'$\widehat{x}^{H,(i,j)}_{t+1\mid t} =$', fs=FS_MATH, color=INK)
txt(cx5, 4.22, r'$\widehat{x}^{B,(i,j)}_{t+1\mid t} + \alpha\,\widehat{r}^{C,(i,j)}_{t+1\mid t}$',
    fs=FS_MATH, color=INK)
txt(cx5, 3.72, r'$\alpha = 1$', fs=FS_MATH, color='0.2')
txt(cx5, 2.88, r'$\widehat{y}^{H,(i,j)}_{t+1\mid t} = g_r^{-1}\!\left(\widehat{x}^{H,(i,j)}_{t+1\mid t}\right)$',
    fs=FS_MATH, color=INK)
draw_small_map(cx5 - 0.62, 1.40, w=1.24, h=0.80)
txt(cx5, 1.05, 'previsão final no próximo instante', fs=FS_NOTE, color=NOTE)

# atalho da previsao-base (contorna os paineis por baixo, sem passar pela CNN)
YB = 0.30
xb = 4.695
ax.plot([xb, xb, 12.05, 12.05], [1.70, YB, YB, 2.45], color='0.40',
        lw=lw(1.3), ls=(0, (4, 2)), zorder=4, solid_joinstyle='miter')
add_arrow((12.05, 2.45), (P5[0], 2.45), width=1.3, ms=11, color='0.40')
txt((P4[0] + P4[0] + P4[2]) / 2, YB, 'previsão-base', fs=FS_NOTE, color=NOTE,
    bbox=dict(facecolor='white', edgecolor='none', pad=1.2), zorder=6)

# ------------------------------- exportacao --------------------------------
out = Path(__file__).resolve().parent
for ext in ('pdf', 'svg', 'png'):
    f = out / f'figura_parcnet_fluxo_horizontal_v4.{ext}'
    fig.savefig(f, dpi=600, facecolor='white', bbox_inches='tight', pad_inches=0.02)
    print(f)
plt.close(fig)
