# Referência da CLI

Execute `python3 codemark.pyz --help` e `python3 codemark.pyz COMANDO --help` para consultar o parser do seu artefato. Checkouts também aceitam `python3 -m codemark`.

## Comandos

| Comando | Função | Opções principais |
| --- | --- | --- |
| `mark RAIZ` | Mostrar prévia ou aplicar comentários e atualizar o manifesto | `--owner`, `--project`, `--apply` |
| `verify RAIZ` | Comparar a árvore com o manifesto | Opções de verificação GPG ou OpenSSH |
| `compare RAIZ SUSPEITO` | Localizar marcas, conteúdo exato e similaridade de tokens | `--threshold` |
| `unmark RAIZ` | Mostrar prévia ou remover comentários deste projeto | `--apply` |
| `sign RAIZ` | Assinar manifesto íntegro com chave existente | `--ssh-key` ou `--key` |
| `doctor` | Mostrar ambiente e ferramentas opcionais disponíveis | `--json` |
| `self-test` | Executar fixtures temporárias neste host | `--json` |
| `gui` | Abrir interface Tkinter opcional | Requer sessão gráfica |

`--owner` é obrigatório na primeira aplicação. Informe o titular correto. O nome do projeto usa o nome da pasta por padrão. O comentário não muda a licença do fonte nem impede sua remoção.

## Relatórios para automação

Todos os comandos, exceto `gui`, aceitam `--json` e `--output ARQUIVO_NOVO`. O destino precisa ser novo e externo às árvores de referência e de suspeita.

```sh
python3 codemark.pyz verify /projeto --json --output /relatorios/nova-verificacao.json
python3 codemark.pyz compare /projeto /suspeito --threshold 0.80 --json
```

O limiar padrão de comparação é `0.65`. Ele representa Jaccard entre sketches limitados de fingerprints de tokens, não uma porcentagem de linhas copiadas. Os candidatos precisam de análise manual.

O relatório é reservado, gravado, descarregado, sincronizado e fechado antes de confirmar uma alteração. Se a transação do projeto falhar, o relatório é removido. Consuma o arquivo somente após o processo terminar e confira o código de saída.

## Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Operação concluída; integridade preservada; comparação sem candidatos; ou autoteste sem falhas |
| `1` | Divergências, candidatos de comparação ou falha no autoteste |
| `2` | Entrada inválida, ferramenta necessária ausente, falha de acesso ou interrupção |

Um autoteste bem-sucedido pode conter resultados `skip`. Leia os checks estruturados; o código de saída sozinho não comprova cobertura das ferramentas opcionais.

## Limites de recursos

| Recurso | Limite por operação |
| --- | --- |
| Fontes cobertos | 5.000 |
| Bytes por fonte | 2 MiB |
| Soma dos fontes | 64 MiB, sem contar as marcas |
| Entradas de diretório | 20.000 |
| Profundidade | 64 níveis |
| Pares de comparação | 2.000.000 |
| Candidatos | 10.000 |
| Metadados | 64 MiB |

Ultrapassar um teto gera erro. Uma busca parcial não é apresentada como completa. Escolha um módulo próprio menor quando necessário. Consulte [formatos e cobertura](wiki/formats.md).
