# Referência da CLI

Use `python3 codemark.pyz --help` e `python3 codemark.pyz COMANDO --help` para consultar seu artefato. O módulo continua `codemark`; checkouts aceitam `python3 -m codemark`. No Windows, use `py -3` e caminhos nativos entre aspas.

## Comandos

| Comando | Função | Opções principais |
| --- | --- | --- |
| `snapshot RAIZ` | Mostrar prévia ou salvar hashes de todos os regulares | `--apply` |
| `sign RAIZ` | Assinar referência revisada | Híbrido `--pq-key` e `--classical-key`; `--passphrase-file` opcional; ou um backend legado |
| `verify RAIZ` | Comparar árvore com referência salva | Dois fingerprints híbridos para autenticação |
| `audit RAIZ` | Autenticar snapshot e cadeia contra a árvore atual | Dois fingerprints híbridos; `--checkpoint` esperado opcional |
| `bundle RAIZ` | Mostrar prévia ou gerar pacote privado criptografado | `--recipient-key`, `--recipient-fingerprint`, `--archive`, `--apply` |
| `mark RAIZ` | Prévia ou aplicação de comentários e manifesto de fontes | `--owner`, `--project`, `--apply` |
| `unmark RAIZ` | Prévia ou remoção dos comentários deste projeto | `--apply` |
| `compare RAIZ SUSPEITO` | Procurar possíveis cópias de fontes | `--threshold` |
| `doctor` | Mostrar ambiente e ferramentas disponíveis | `--json` |
| `self-test` | Exercitar fixtures temporárias neste host | `--json` |
| `gui` | Abrir interface legada de comentários | Tkinter e sessão gráfica |

## Modos de integridade e autenticação

Se `.codemark/integrity.json` existe, `verify` escolhe a referência de todos os arquivos regulares. Sem os dois fingerprints, o resultado é integridade não autenticada. `audit` exige snapshot, histórico de atestações e os dois fingerprints completos confiáveis.

```sh
python3 codemark.pyz verify /projeto --json
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --checkpoint SEU_CHECKPOINT_SHA512_COMPLETO_MINUSCULO --json
```

Troque os três exemplos pelos valores completos confiáveis. O checkpoint é opcional na sintaxe, mas necessário para detectar substituição por cadeia antiga válida. Leia [Rastreabilidade](traceability.md).

As opções legadas OpenSSH/GPG autenticam somente o manifesto de comentários e são recusadas quando há snapshot completo selecionado. Não combine backends. Veja [Assinaturas](signing.md).

## Relatórios e códigos de saída

Comandos sem GUI aceitam `--json` e relatório externo novo por `--output`. O pacote usa destino próprio `--archive`. Mantenha relatórios e pacotes fora das árvores tratadas e não sobrescreva evidências anteriores.

| Código | Significado |
| --- | --- |
| `0` | Operação concluída; integridade preservada; comparação sem candidatos; ou autoteste sem falhas |
| `1` | Divergências, candidatos ou falha de autoteste |
| `2` | Entrada inválida, erro de ferramenta/autenticação, falha de acesso ou interrupção |

Confira campos de integridade e autenticação. O autoteste pode conter `skip`; código 0 sozinho não qualifica uma ferramenta ausente. Consuma relatórios após o término e confira o código de saída.

## Tetos separados

| Recurso | Snapshot de todos os arquivos | Comentários e comparação |
| --- | --- | --- |
| Arquivos | 100.000 regulares | 5.000 fontes cobertos |
| Um arquivo | 100 GiB | 2 MiB |
| Soma dos bytes | 1 TiB | 64 MiB sem as marcas |
| Entradas de diretório | 200.000 | 20.000 |
| Metadados | 64 MiB | 64 MiB |
| Comparação | Não se aplica | 2.000.000 pares e 10.000 candidatos |

São tetos de aceitação, não benchmarks. Exceder limite gera falha em vez de cobertura incompleta apresentada como completa. O histórico híbrido tem tetos próprios: 1.000 registros, 32 MiB por cadeia e 32 KiB por registro canônico. Chaves têm teto de 1 MiB e arquivo de senha de 32 KiB.

A comparação usa `--threshold 0.65` por padrão. A pontuação é Jaccard entre sketches de tokens limitados, não porcentagem de linhas copiadas. Veja [Formatos](wiki/formats.md).
