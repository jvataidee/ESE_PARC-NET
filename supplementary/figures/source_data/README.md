# Localização dos pontos — fontes auditadas

Arquivos copiados das configurações do projeto `sits-forecasting-v2` em 2026-11-09, para documentar a seleção geográfica do PARC-Net.

- `br_biomes_points.csv`: tabela de biomas brasileiros; a amostra do artigo usa **apenas os 14 registros `biome=amazonia`**, dois por sete critérios.
- `atmospheric_points.csv`: quatro centros GOES-16.
- `ocean_points.csv`: seis centros OISST.

As tabelas contêm **coordenadas de centros** e não valores de sensores nem resultados de previsão. O GeoJSON dos biomas está no projeto original no Google Drive e **não foi replicado neste repositório** enquanto sua versão e as condições de redistribuição não forem verificadas. O script original do mapa requer os arquivos de configuração e os módulos `sits_forecasting` correspondentes.

Amostras geográficas podem estar baixadas sem estarem todas preparadas ou avaliadas. Conferir registros de preparo e IDs antes de falar em 150 cubos executados.
