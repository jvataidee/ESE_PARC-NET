# Checklist — PARC-Net, imagens → texto → Zenodo

**Versão-base do manuscrito:** v7 (seis páginas). **Repositório complementar:** https://github.com/jvataidee/ESE_PARC-NET. **Regra editorial:** manter no artigo as informações essenciais para avaliar os experimentos.

## 1. Figuras e evidências
- [x] Identificar script-fonte do fluxo PARC-Net.
- [x] Localizar o script-fonte do mapa no Google Drive.
- [x] Documentar os scripts no repositório complementar.
- [ ] Validar entradas do mapa (coordenadas, estratos, GOES e OISST) contra a configuração executada.
- [ ] Conferir bases geográficas, autorizações de uso, licenças e atribuições.
- [ ] Gerar e revisar PDF/SVG/PNG finais do mapa e do fluxo no tamanho de impressão.
- [ ] Comparar versão A (mapa no artigo; fluxo no GitHub) e versão B (ambas as figuras), avaliando frases fragmentadas, espaço e legibilidade.
- [ ] Aprovar o conjunto final e a posição das figuras; garantir seis páginas.

## 2. Revisão científica e textual — somente depois do item 1
- [ ] Reescrever a introdução com pontes: relevância SITS → heterogeneidade dos dados → ARIMA compartilhado → lacuna espacial → objetivo.
- [ ] Explicitar a contribuição como **avaliação experimental**, não proposição de arquitetura inédita.
- [ ] Melhorar comparação crítica com trabalhos relacionados.
- [ ] Assegurar GQM, QP1/QP2, hipóteses nula/alternativa, tratamentos, variáveis-resposta, unidade inferencial e controles.
- [ ] Justificar GOES/OISST exploratórios e os limites de generalização; distinguir QP3.
- [ ] Validar a fundamentação das ameaças à validade e a edição bibliográfica citada.
- [ ] Preservar equações, métricas, parâmetros, fontes, declaração de uso de IA e estilo SBC.
- [ ] Recompilar e inspecionar a versão de seis páginas.

## 3. Arquivamento e referência — após o DOI
- [ ] Autor fornecer DOI do Zenodo.
- [ ] Verificar título, autores, versão, data, DOI e arquivos efetivamente arquivados.
- [ ] Associar tag/commit do GitHub à versão depositada.
- [ ] Ajustar README e citação no LaTeX segundo normas da chamada, incluindo regras de anonimização.
- [ ] Conferir integridade e acessibilidade dos complementos antes de fechar a entrega.

## Pendências de integridade científica
- [ ] Documentar métrica, comparador e produtos no ganho preliminar médio de ~15%.
- [ ] Verificar a configuração implementada contra os valores descritos no artigo.
- [ ] Avaliar definições dos grupos espaciais e pressupostos do bootstrap antes de afirmar inferência confirmatória.

**Última decisão:** publicar apenas scripts e documentação inicial até completar a auditoria das imagens; não publicar automaticamente dados raster, credenciais nem arquivos de ambiente.
