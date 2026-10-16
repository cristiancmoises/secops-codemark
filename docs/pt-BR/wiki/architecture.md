# Arquitetura

CodeMark separa tratamento dos fontes, comparação, orquestração da CLI, assinaturas opcionais e interface gráfica opcional. A implementação usa a biblioteca padrão do Python.

## Módulos

| Módulo | Responsabilidade |
| --- | --- |
| `codemark/core.py` | Inventários limitados, marcas, manifestos, verificação, alterações e rollback |
| `codemark/fingerprint.py` | Fingerprints de tokens normalizados e similaridade |
| `codemark/cli.py` | Argumentos, relatórios, códigos de saída e despacho |
| `codemark/ssh_signing.py` | Assinaturas Ed25519 OpenSSH e verificação fixada |
| `codemark/signing.py` | OpenPGP opcional e keyring dedicado |
| `codemark/selftest.py` | Fixtures temporárias e ausências explícitas |
| `codemark/gui.py` | Interface Tkinter opcional |

## Fluxo de dados

```text
Árvore própria selecionada
  -> inventário limitado de fontes
  -> prévia ou comentário reversível de procedência
  -> manifesto SHA-256 e sketches de tokens
  -> assinatura opcional com chave existente

Referência salva + árvore atual -> relatório de integridade
Referência salva + árvore suspeita -> relatório de candidatos
```

A comparação lê fontes suspeitos como dados. Não os executa. O autoteste executa somente suas próprias fixtures temporárias.

## Limite de confiança

Um manifesto sem assinatura é uma referência local. A autenticação precisa de chave pública confiável separada e fingerprint fixado. O operador controla máquina, revisão, chaves e CI.

O projeto não tem backend hospedado em runtime. Este site de documentação é HTML e CSS pré-gerados, sem JavaScript, analytics, fontes externas ou requisições de assets de terceiros.

Veja [formatos](formats.md) para armazenamento e [segurança](../security.md) para limites.
