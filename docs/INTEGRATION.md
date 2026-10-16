# Integração simples

## Fluxo recomendado

Marque uma vez, rode os testes do projeto e guarde os arquivos fontes junto
com `.codemark/project.json` e `.codemark/manifest.json` no controle de versão.
Se assinou, guarde também `manifest.json.asc`. Não versione `.codemark/lock`.
Mantenha uma cópia independente dos metadados do lançamento.

Depois de uma edição legítima, atualize a referência com `mark --apply`.
Sem isso, a verificação acusa a mudança, como esperado. Em CI, use **verify**;
usar mark automaticamente antes de verificar aceitaria as alterações como
uma nova referência. Uma assinatura antiga não se atualiza sozinha.

```sh
python3 /caminho/codemark.pyz mark . --owner "Seu nome ou organização" --apply
python3 /caminho/codemark.pyz verify . --json
```

Evite armazenar o código da ferramenta dentro da raiz tratada, para não
marcar também a ferramenta e seus exemplos. Prefira a raiz de um módulo
first-party quando o monorepo mistura código próprio e dependências.

## CI e hooks locais

O processo retorna 0 se íntegro, 1 para divergências/candidatos e 2 para erro.
Um hook local opt-in pode executar:

```sh
#!/bin/sh
exec python3 /caminho/confiavel/codemark.pyz verify /caminho/do/projeto
```

Ele verifica a árvore atual, não o snapshot do índice Git. Em pipelines, faça
checkout da revisão pretendida. Verificação local sem assinatura não detecta
quem maliciosamente modifica fontes e manifesto juntos. Para conferir uma
chave confiável, use todos estes argumentos:

```sh
python3 codemark.pyz verify . --require-signature --keyring /chaves/public.gpg --fingerprint SEU_FINGERPRINT_COMPLETO --json
```

O keyring e o fingerprint precisam vir de uma referência confiável, não da
mesma contribuição não confiável que você pretende validar. Assegure a
procedência do próprio executável CodeMark e do runner de CI.

Não há hooks instalados automaticamente, alteração de configuração de agentes,
publicação em GitHub/Forgejo ou ações na sua infraestrutura.

## GNU Guix

Para a CLI, use o Python do seu perfil. Exemplo de ambiente temporário:

```sh
guix shell python -- python3 codemark.pyz doctor --json
guix shell python -- python3 codemark.pyz mark /projeto --owner "Security Ops" --apply
```

Assinatura opcional: disponibilize GnuPG no ambiente e configure sua chave e
agente. A GUI precisa de uma instalação Python com Tkinter e sessão gráfica;
use a CLI se o módulo não estiver presente. Esses comandos não foram
executados em Guix neste ambiente; nenhuma receita de pacote é alegada validada.

## Windows e GNU/Linux

No Windows com Python instalado, `py -3 codemark.pyz gui`. Na CLI, substitua
`python3` por `py -3` e use caminhos entre aspas. No GNU/Linux,
`python3 codemark.pyz gui`. Não exige Docker, servidor web ou administrador.

## Cobertura e rollback

Confira o campo `skipped` do JSON. Ele informa diretórios excluídos e arquivos
sem marca; os testes não validam compilação de todas as linguagens suportadas.
O rollback reverte gravações desta operação em falhas comuns. Não recupera
edições anteriores e não substitui Git ou backups. Evite escritores simultâneos.
