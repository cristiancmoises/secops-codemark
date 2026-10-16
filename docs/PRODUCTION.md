# Produção: CodeMark 0.2.0

## Escopo de uso

Esta versão se destina à CLI em GNU/Linux para marcar fontes próprios,
registrar integridade, assinar a referência com OpenSSH Ed25519 e procurar
candidatos a cópia. A ativação é local e pode integrar o pipeline de publicação.

A decisão final de qualificação acompanha `QUALIFICATION.json` e
`REVIEW_0.2.0.md`, incluídos após a revisão. Sem esses registros no pacote,
trate esta compilação como candidata de desenvolvimento.

Não existe bloqueio universal de REA. Marcas são removíveis e relatórios são
indícios técnicos. A assinatura comprova vínculo com a chave, sem provar
anterioridade ou titularidade jurídica.

## Ativação rápida

Extraia o ZIP em `~/Downloads` e abra a pasta `secops-codemark-0.2.0`:

```sh
python3 codemark.pyz self-test
python3 codemark.pyz mark /caminho/do/projeto --owner "Security Ops"
python3 codemark.pyz mark /caminho/do/projeto --owner "Security Ops" --apply
python3 codemark.pyz verify /caminho/do/projeto
```

Troque a pasta e o titular pelos corretos. O primeiro `mark` é uma prévia.
Trabalhe sobre código versionado, com testes do projeto passando. Guarde os
fontes marcados e `.codemark/project.json` + `.codemark/manifest.json` no Git.
A assinatura `.sshsig`, quando usada, também integra a referência do lançamento.
Mantenha `.codemark/lock` fora do controle de versão.

No seu GNU Guix, o autoteste detecta `guile` e executa uma fixture própria
marcada. Se houver falha, não aplique ao projeto até resolver. Se uma ferramenta
não existir, a execução dessa linguagem aparece como `skip`. O autoteste não
valida todos os programas do projeto; execute também os testes dele.

## Referência autenticada

Use uma chave Ed25519 dedicada que já possui ou crie-a nativamente, fora do
projeto. O comando abaixo pergunta a senha no seu terminal; ele não foi
executado com dados do usuário nesta entrega:

```sh
ssh-keygen -t ed25519 -f ~/.ssh/codemark-signing -C "CodeMark Security Ops"
```

Guarde a chave privada com segurança. Para assinar uma árvore íntegra:

```sh
python3 codemark.pyz sign /caminho/do/projeto --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
```

Fixe o fingerprint completo obtido, por exemplo numa configuração confiável
do CI. A chave pública também precisa vir de uma referência confiável:

```sh
python3 codemark.pyz verify /caminho/do/projeto --ssh-public-key /chaves/codemark-signing.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_COMPLETO'
```

Depois de editar legitimamente: execute `mark --apply`, testes do projeto e
`sign` novamente. Uma assinatura antiga sobre manifesto novo deve falhar.
A chave privada nunca deve ficar na árvore marcada nem no pacote público.
Nenhuma consulta de revogação é feita: gerencie a confiança da chave fora do projeto.

## CI

Execute `verify`, com assinatura quando precisar de autenticação. Não rode
`mark --apply` automaticamente antes de verificar, pois isso aceitaria mudanças
como uma nova referência. Confira o checkout pretendido e preserve o keyring,
fingerprint e executável de validação contra mudanças da contribuição analisada.

Retornos: 0 sucesso/íntegro/autoteste sem falhas; 1 divergência, candidatos a
cópia ou falha no autoteste; 2 erro de entrada/acesso/ferramenta. `self-test` com
`skip` não valida o componente ausente. Use JSON para inspecionar cada check.
Relatórios `--output` devem ser externos às árvores tratadas e usar arquivo novo.
Sua gravação, sincronização e fechamento terminam antes das alterações no projeto.
Uma falha posterior na transação remove o relatório. Só consuma o arquivo depois
de o comando terminar; uma reserva ou gravação em andamento não indica sucesso.

## Rollback

Para retirar somente as marcas, preservando edições:

```sh
python3 codemark.pyz unmark /caminho/do/projeto
python3 codemark.pyz unmark /caminho/do/projeto --apply
```

O manifesto anterior continua no lugar e acusará a remoção. Para recuperar
uma versão completa do projeto, use o commit ou backup preparado antes da
aplicação. Interrupção forçada/queda de energia não têm recuperação transacional
de crash nesta versão. O fechamento normal da GUI aguarda o worker concluir.

## Componentes com qualificação separada

- CLI e OpenSSH: evidência desta entrega e revisão final.
- Python/JavaScript: fixtures executadas no ambiente disponível.
- Guile e demais toolchains: preservação de bytes testada; execução nativa
  depende do autoteste e testes do projeto no host de destino.
- GUI, GPG, Windows e Guix como plataforma completa: sem qualificação específica
  neste ambiente. Não dependem do caminho principal da CLI/OpenSSH.

Não há processo de servidor a manter. Para iniciar rapidamente, utilize a CLI,
o autoteste do host e a verificação no seu fluxo de publicação.
