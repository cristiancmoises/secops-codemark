# Validação e evidências

Uma decisão de lançamento precisa identificar versão, revisão de fonte, data, ambiente, comandos, resultados brutos e componentes excluídos. Fixtures que passam são evidência sobre aquelas fixtures naquele ambiente.

## Versão atual

A página de Evidências do site é gerada por `website/data/release.json`. Resultados ficam como `pending` até o operador registrar medições. Esse arquivo é um resumo publicado; os relatórios vinculados preservam escopo e limitações reais.

Não reutilize contagens ou qualificação de uma versão anterior como evidência de fontes modificados. Ausências opcionais continuam visíveis. Revisão por agente é identificada como tal e não afirma auditoria profissional externa ou certificação.

## Reproduzir localmente

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -I dist/codemark.pyz self-test --json
python3 scripts/build_site.py --check
```

Use as dependências reais do build e leia erros de ferramentas ausentes. Execute o portátil fora do repositório ao testar isolamento. Reprodutibilidade se aplica ao mesmo fonte e ambiente declarado; não implica igualdade binária entre plataformas.

## O que os testes exercitam

O repositório tem testes de marcação reversível, divergências de integridade, comparação de tokens, prologues e preservação de bytes, validação de metadados, falhas de relatórios, CLI, limites, isolamento de pacote e backends de assinatura.

O autoteste cria fixtures temporárias e chaves efêmeras. Executa linguagens apenas quando suas ferramentas estão disponíveis. Não exercita projetos arbitrários, todas as linguagens, sistema operacional hostil, renderização da GUI ou alegações jurídicas.

## Registro histórico da 0.2.0

Estes arquivos foram preservados como evidência histórica da versão 0.2.0, datada de **2026-10-16 UTC**. Seus números e pareceres valem para o escopo declarado, sem transferência automática a outra versão.

- [JSON de qualificação](../QUALIFICATION.json)
- [Revisão por agente após correções](../REVIEW_0.2.0.md)
- [Narrativa histórica de validação](../VALIDATION.md)
- [Escopo operacional histórico](../PRODUCTION.md)

O registro original relata 71 testes e exclui componentes opcionais e plataformas. Leia o registro completo antes de usá-lo. Uma versão posterior precisa publicar seu próprio resultado.
