# Materiais complementares: detalhes do protocolo

Complemento do artigo "Protocolo experimental de avaliação do PARC-Net em séries temporais de imagens de
satélite". Reúne detalhes retirados do corpo do artigo para respeitar o limite de 6 páginas. Todo o
conteúdo vem do próprio texto do artigo; nada aqui acrescenta resultado.

## S1. Alvos, produtos e períodos

Cubos previstos: até 150, sendo 140 terrestres (dez alvos por centro), quatro recortes GOES-16 na Amazônia
e no Cerrado e seis OISST no Atlântico.

Alvos terrestres por centro (dez):

1. NDVI de HLS (Landsat e Sentinel-2 harmonizados).
2. NDVI de Sentinel-2.
3. NDVI de CBERS.
4. NDVI de Amazônia-1.
5. NDVI de MODIS.
6. LST do MODIS.
7. GPP do MODIS.
8. LAI do MODIS.
9. Retroespalhamento γ⁰ VH do Sentinel-1 RTC.
10. Razão VH/VV do Sentinel-1 RTC, em decibéis: 10 log10(VH/VV).

Períodos, conforme a disponibilidade: séries terrestres principalmente 2019 a 2024; GOES-16, 2023; OISST,
2015 a 2024.

## S2. Preparo e métricas sobre alvos observados

O preparo compreende controle de qualidade, composição temporal e preenchimento causal pela última
observação válida (LOCF), sem acesso a valores futuros. A suavização é definida antes do teste, mas as
métricas são calculadas sobre alvos observados, sem imputação ou suavização, exceto pelo tratamento de
*speckle* no radar.

## S3. Seleção de ordens ARIMA e busca de hiperparâmetros

- As ordens ARIMA são selecionadas pelo critério de Akaike corrigido (AICc), que pondera ajuste e
  complexidade, em 25% fixos dos pixels por região.
- Quando aplicável, Optuna/TPE realiza até 30 tentativas em no máximo 32 pixels; a influência desses
  limites é examinada por sensibilidade.
- Os preditores diretos usam 12 observações; a CNN usa janelas de resíduos prequenciais para treino,
  parada e calibração.

## S4. Bootstrap em blocos

A dependência temporal é tratada por *bootstrap* em blocos (Künsch, 1989), com
L = max(2, ⌈n_val^(1/3)⌉), em que n_val é o número de origens elegíveis da seleção interna. O comprimento
e o uso dos centros como grupos são fixados antes do teste e avaliados por sensibilidade, com blocos
idênticos nos modelos pareados.

## S5. Medidas adicionais e registro para auditoria

Além do MASE, são medidos MAE, ganho em relação à persistência, falhas, tempos de seleção, ajuste e
inferência, pico de memória e custo da geração residual. Partições, máscaras, origens, hiperparâmetros,
sementes (42, 52 e 62), previsões, falhas, custos e ambiente são registrados para auditoria.

## S6. Modelos comparados (QP1 a QP3)

Persistência preparada e observada (referências com e sem suavização); ARIMA local (referência local) e *pooled* (base de QP1); PARC-Net e ablação 1×1; LightGBM, SVR, KNN, MLP,
LSTM e DLinear (preditores diretos, 12 observações); CorrDiff e Earthformer adaptados. As referências
originais de cada modelo estão no arquivo `references.bib` do artigo.
