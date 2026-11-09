# Auditoria das figuras — etapa 1 (2026-11-09)

## Fontes conferidas
- `sits-forecasting-v2`: `configs/experiment.yaml`, `configs/datasets.yaml`, `configs/regions/br_biomes_points.csv`, `atmospheric_points.csv`, `ocean_points.csv`, `br_biomes.geojson` e `scripts/generate_biomes_location_map.py`.
- Script do diagrama `generate_parcnet_flow.py` fornecido pelo autor.
- Manuscrito v7 de seis páginas e arquivo do mapa de dois painéis.

## Validações geográficas e numéricas
- O experimento aponta `biomes: [amazonia]` e `max_regions: 14`.
- A tabela de centros contém **14 pontos amazônicos**, distribuídos em **7 critérios com 2 centros por critério** (desmatamento, agricultura, vegetação nativa, fogo, pastagem, expansão urbana e mineração).
- A verificação geométrica com o GeoJSON da pesquisa confirmou **14/14 centros dentro do polígono Amazônia**.
- Os complementos possuem **4 pontos GOES-16** em dois regimes e **6 pontos OISST** em três regimes.
- As configurações de recorte são **64 px × 2 km = 128 km** para GOES e **32 px × 0,25° = 8°** para OISST. As extensões cartográficas são aproximadas, não limites exatos de imagens adquiridas.

**Atenção:** a configuração genérica `sampling_strata` inclui oito nomes, inclusive silvicultura; a tabela efetiva na Amazônia usa sete estratos e não inclui silvicultura. Para o manuscrito, prevalecem os sete estratos observados.

As contagens não comprovam a preparação ou execução de 150 cubos, nem os ganhos preliminares.

## Figuras geradas e decisão editorial
Foram geradas e inspecionadas três figuras, localmente em PDF/SVG/PNG:
1. **Mapa compacto**: 14 centros amazônicos e critérios (artigo).
2. **Mapa completo**: 14 centros mais quatro pontos GOES e seis OISST, com extensões aproximadas (complemento).
3. **Diagrama de fluxo**: ARIMA pooled, resíduos prequenciais, CNN residual e combinação híbrida (complemento).

Duas variantes do artigo v7 foram compiladas **com seis páginas**, sem alterar margens, fontes, equações e resultados. **A (recomendada)** mantém apenas o mapa compacto e desloca o fluxo aos complementos; **B** mantém o fluxo e o mapa compacto. Na A, a conclusão está na página 5; na B, parte dela avança para a página 6.

Os PDF/SVG/PNG gerados ainda requerem revisão final de atribuições cartográficas e estão disponíveis no pacote de auditoria entregue separadamente. Não afirmar que esses binários já estão publicados neste repositório.

## Fonte dos pontos
As tabelas de coordenadas foram copiadas da configuração do projeto original, sem interpolação ou pontos sintéticos. Este repositório permanece privado. Antes de disponibilizá-lo publicamente, conferir a edição e os termos de redistribuição das geometrias do IBGE e as regras de anonimização do evento.

## Próxima etapa
Depois de aprovar a opção A e consolidar as figuras, revisar introdução, fundamentos e metodologia; preservar o protocolo formalizado, hipóteses e 6 páginas. DOI do Zenodo ficará pendente até fornecimento e verificação pelo autor.
