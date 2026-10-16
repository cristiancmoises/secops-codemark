# Inventariar todos os arquivos regulares

`snapshot` registra bytes sem inserir comentários nem mudar o conteúdo dos arquivos. Calcula SHA-256 e SHA-512 por leitura em blocos, independentemente da extensão: fontes, JSON, documentação, ocultos, arquivos sem extensão, imagens, executáveis, compactados e ISOs.

## Conferir e salvar

```sh
python3 codemark.pyz snapshot /projeto --json
python3 codemark.pyz snapshot /projeto --apply --json
```

Sem `--apply`, o comando mostra a prévia. A aplicação grava `.codemark/integrity.json`. Mantenha o projeto estável durante a leitura. Confira quantidade de arquivos, bytes, exclusões e digests do manifesto antes de adotar o snapshot como referência.

O inventário exclui componentes de caminho chamados `.codemark`, `.git`, `.hg` e `.svn`, com os motivos registrados. Assim, metadados próprios e internos do controle de versão ficam fora da referência. Outros diretórios, inclusive builds e dependências, entram quando contêm arquivos regulares. Escolha a raiz deliberadamente.

## Limites do filesystem

Links simbólicos e arquivos especiais são recusados. A leitura confere identidade e metadados ao abrir, calcular e concluir o hash; uma mudança simultânea detectada faz a operação falhar. Isso não torna confiável um sistema operacional local hostil. Pare editores, builds e sincronizadores antes de inventariar ou verificar.

O snapshot cobre arquivos, não diretórios vazios. Não é backup nem imagem de filesystem. Registra caminhos relativos, tamanhos, hashes e modos de permissão; restaurar conteúdo equivalente em outra plataforma ainda pode expor diferenças de modo.

## Verificar a referência

```sh
python3 codemark.pyz verify /projeto --json
```

Leia o modo de cobertura no relatório. No modo de todos os arquivos regulares, as divergências incluem bytes alterados, arquivos ausentes ou novos e modos de permissão alterados. Uma referência local sem assinatura pode ser editada por quem consegue gravá-la.

Para autenticar a referência, use [assinatura híbrida](signing.md) com os dois fingerprints confiáveis independentes. Preserve os bytes exatos do manifesto: reformatar seu JSON muda a referência assinada mesmo quando os valores parecem equivalentes.

## Tetos de capacidade

| Recurso | Limite do snapshot |
| --- | --- |
| Um arquivo regular | 100 GiB |
| Soma dos arquivos regulares | 1 TiB |
| Arquivos regulares | 100.000 |
| Entradas de diretório | 200.000 |
| Manifesto serializado | 64 MiB |

A operação falha ao exceder um teto; não apresenta inventário parcial como completo. A leitura em blocos evita carregar um arquivo grande inteiro na memória. Os limites descrevem tetos de aceitação, não desempenho medido nem promessa de que qualquer host processa uma árvore no tamanho máximo.

## Distinguir a marcação

`mark` continua sendo uma operação de comentários reversíveis para formatos de fonte cobertos, com exclusões e limites menores próprios. Não marca JSON, binários nem ISOs. Você pode marcar um módulo próprio e depois inventariar a árvore maior do lançamento. Conclua as edições antes de gerar a referência que será assinada.

Veja [formatos](wiki/formats.md), [rastreabilidade](traceability.md) e [segurança](security.md).

## Metadados do sistema de arquivos

Snapshots incluem bits de permissão dos arquivos. A verificação em outro sistema operacional ou sistema de arquivos pode indicar `mode_changed` mesmo com bytes idênticos. Prepare e verifique a referência no sistema de arquivos previsto para o release; investigue as diferenças sem aceitá-las silenciosamente. Bits POSIX não representam ACLs do Windows, atributos estendidos, proprietário ou toda a política de acesso do sistema.
