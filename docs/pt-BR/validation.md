# Validação e evidências

Uma decisão de lançamento precisa identificar versão, revisão de fonte, data, ambiente, comandos, resultados brutos e componentes excluídos. Fixtures que passam são evidência sobre aquelas fixtures naquele ambiente.

## Versão atual

A página de Evidências do site é gerada por `website/data/release.json`. Resultados ficam como `pending` até o operador registrar medições. Esse arquivo é um resumo publicado; os relatórios vinculados preservam escopo e limitações reais.

Não reutilize contagens ou qualificação de uma versão anterior como evidência de fontes modificados. Ausências opcionais continuam visíveis. Revisão por agente é identificada como tal e não afirma auditoria profissional externa ou certificação.

A versão 0.4.1 corrige o empacotamento do release e as rotas de relatórios do site, preservando os formatos de runtime da 0.4.0. Há registros próprios de testes, portátil e revisão. Providers nativos e plataformas precisam identificar os fontes realmente medidos.

## Reproduzir localmente

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --output /tmp/codemark-validation-0.4.1
python3 -I /tmp/codemark-validation-0.4.1/codemark.pyz self-test --json
```

Use um diretório de saída novo em cada build. Prepare os downloads antes da verificação estrita do site; consulte o [fluxo de lançamento](releasing.md).

Use as dependências reais do build e leia erros de ferramentas ausentes. Execute o portátil fora do repositório ao testar isolamento. Reprodutibilidade se aplica ao mesmo fonte e ambiente declarado; não implica igualdade binária entre plataformas.

## O que os testes exercitam

O repositório tem testes de comentários reversíveis, bytes, candidatos de tokens, metadados e falhas de relatórios, inventário completo, tetos, isolamento, assinaturas híbridas, chaves fixadas e histórico encadeado. Consulte os logs atuais para casos executados, versões e ausências. Exportação privada e plataformas precisam de registros próprios.

O autoteste cria fixtures temporárias e chaves efêmeras. Executa linguagens apenas quando suas ferramentas estão disponíveis. Não exercita projetos arbitrários, todas as linguagens, sistema operacional hostil, renderização da GUI ou alegações jurídicas.

## Registro histórico da 0.4.0

A [qualificação](../reports/0.4.0-validation.json), o [log de testes](../reports/0.4.0-tests.txt), as [verificações portáteis](../reports/0.4.0-self-test.json) e a [revisão focal](../reports/0.4.0-review.md) da 0.4.0 preservam revisões e escopos originais. Medições de similaridade e pipeline continuam como experimentos históricos, com hashes exatos dos fontes e ferramentas. Não substituem as verificações do release 0.4.1.

## Registro histórico da 0.3.0

Estes registros valem para a versão 0.3.0 e têm data de **2026-10-16 UTC**. A qualificação registrada cobre a CLI local GNU/Linux; Windows e renderização da GUI foram excluídos. Os arquivos permanecem inalterados como evidência histórica.

- [JSON de qualificação](../reports/0.3.0-validation.json)
- [Log completo dos testes](../reports/0.3.0-tests.txt)
- [Verificações portáteis](../reports/0.3.0-self-test.json)
- [Revisão focal dos fontes e empacotamento](../reports/0.3.0-review.md)
- [Validação do site](../reports/0.3.0-website.json)

O registro 0.3.0 relata 81 testes GNU/Linux e nove verificações portáteis. Os resultados valem para os fontes e o ambiente originais, não para fontes de versões posteriores.

## Registro histórico da 0.2.0

Estes arquivos foram preservados como evidência histórica da versão 0.2.0, datada de **2026-10-16 UTC**. Seus números e pareceres valem para o escopo declarado, sem transferência automática a outra versão.

- [JSON de qualificação](../QUALIFICATION.json)
- [Revisão por agente após correções](../REVIEW_0.2.0.md)
- [Narrativa histórica de validação](../VALIDATION.md)
- [Escopo operacional histórico](../PRODUCTION.md)

O registro original relata 71 testes e exclui componentes opcionais e plataformas. Leia o registro completo antes de usá-lo. Uma versão posterior precisa publicar seu próprio resultado.
