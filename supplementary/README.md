# Materiais complementares — PARC-Net

Estes materiais documentam a geração das figuras associadas ao estudo **Avaliação experimental do PARC-Net em séries temporais de imagens de satélite**.

## 1. Diagrama do fluxo

Fonte: [`figures/parcnet-flow/generate_parcnet_flow.py`](figures/parcnet-flow/generate_parcnet_flow.py).

O script utiliza NumPy e Matplotlib (>= 3.5), desenha os cinco componentes do fluxo (entrada, ARIMA pooled, resíduos prequenciais, CNN residual e combinação híbrida) e gera três formatos na pasta onde é executado:

```bash
python supplementary/figures/parcnet-flow/generate_parcnet_flow.py
```

Saídas esperadas: `figura_parcnet_fluxo_horizontal_v4.pdf`, `.svg` e `.png`. O desenho é uma representação esquemática; não constitui resultado experimental.

## 2. Mapa das áreas de estudo

Fonte: [`figures/study-areas/generate_biomes_location_map.py`](figures/study-areas/generate_biomes_location_map.py), recuperada de `scripts/generate_biomes_location_map.py` do projeto `sits-forecasting-v2` no Google Drive, em 9 de novembro de 2026.

O script contém duas representações: pontos de amostragem por critério e recortes em grade de GOES/OISST. Ele **não é independente**: importa módulos internos `sits_forecasting`, utiliza configurações `configs/experiment.yaml` e `configs/datasets.yaml`, geometrias de `configs/regions/br_biomes.geojson` e tabelas de pontos. Não foram incluídos esses arquivos nesta publicação inicial.

No projeto original, após instalação das dependências e presença dos dados, o comando previsto é:

```bash
python scripts/generate_biomes_location_map.py --output artifacts/figures/mapa_biomas.pdf
```

As camadas de fundo mencionadas pelo script incluem Natural Earth e, na ausência deste, Esri. Antes da publicação aberta das imagens definitivas, conferir atribuição, licença e integridade das fontes geográficas. Conferir também a quantidade de centros/recortes com a configuração efetivamente executada, pois o script pode mostrar pontos baixados mesmo quando o preparo usa um subconjunto.

## 3. Escopo e limitações

Os scripts e a documentação são materiais complementares. Os arquivos de figuras finais e os metadados geográficos de entrada ainda precisam de validação e serão adicionados numa etapa posterior. Nenhuma medida de ganho, hipótese confirmatória ou replicabilidade integral é atestada por estas fontes isoladas.

As informações indispensáveis sobre objetivo, desenho experimental, hipóteses, métricas e ameaças à validade permanecem no artigo. Não foram publicados dados raster brutos, credenciais, arquivos `.env` ou resultados de pilotos não auditados.

## 4. Próximas etapas

1. Conferir localização e contagem dos centros e recortes com as configurações reais.
2. Gerar, inspecionar e adicionar figuras finais (PDF/SVG/PNG) e, se permitido, tabelas geográficas não sensíveis.
3. Concluir a comparação de diagramação do artigo (mapa versus mapa + fluxo).
4. Revisar o texto de seis páginas com foco em fluidez e formalidade.
5. Após o autor fornecer e conferir o DOI do Zenodo, acrescentar a citação da versão arquivada ao repositório e ao manuscrito.

**Estado:** material inicial de apoio à revisão, ainda não é um pacote completo de replicação nem um depósito Zenodo.
