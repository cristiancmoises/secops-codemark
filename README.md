# SecOps CodeMark

Uma marca d'água de procedência para código-fonte, com verificação de integridade
e busca de cópias por similaridade. Local, sem IA, sem rede e sem pacotes pip.
Licença da ferramenta: **GPL-3.0-or-later**. Versão 0.2.0.

## Ativação da CLI

Consulte o [roteiro de produção e escopo validado](docs/PRODUCTION.md).
Extraia o pacote e execute o autoteste na sua máquina:

```sh
python3 codemark.pyz self-test
```

Ele cria e apaga fixtures e chaves efêmeras, sem usar seus fontes ou chaves.
Verifica marcação, integridade, adulteração, comparação e remoção; executa as
fixtures em Python e, se disponíveis, Node e Guile; testa OpenSSH quando instalado.
Ausências são listadas como `skip`. O resultado não certifica seu projeto.
GUI e GPG continuam componentes opcionais fora da qualificação desta entrega.

CodeMark ajuda a registrar e comparar fontes. A marca pode ser removida ou
forjada, e não impede REA, descompilação, estudo ou cópia de código público.
O manifesto assinado vincula uma referência a uma chave; não prova data,
originalidade ou titularidade legal. Projetos tratados conservam sua licença.

## Começar

Extraia o ZIP e abra um terminal na pasta extraída. Requer Python 3.10 ou
superior. A interface opcional usa Tkinter, normalmente incluído no Python
para Windows e disponível como componente do Python em GNU/Linux.

```sh
python3 codemark.pyz gui
```

No Windows: abra `Iniciar.bat`, ou use `py -3 codemark.pyz gui`.
Em GNU/Linux: `sh iniciar.sh`. Se não houver sessão gráfica ou Tkinter, use a CLI.

Na janela: escolha a pasta de **código de sua autoria**, informe o titular,
clique em **Prévia** e depois **Aplicar marca**. Dependências e diretórios de
build conhecidos são excluídos. Bibliotecas de terceiros em outras pastas
precisam ficar fora da raiz escolhida. Não atribua fontes alheios a si mesmo.

Para quem prefere um comando:

```sh
python3 codemark.pyz mark /caminho/do/projeto --owner "Security Ops" --apply
```

Use o titular correto em `--owner`. Sem `--apply`, o comando mostra uma prévia
sem escrever. Depois da primeira aplicação, basta:

```sh
python3 codemark.pyz mark /caminho/do/projeto --apply
```

Cada arquivo recebe uma linha de comentário com este formato:

```scheme
;; CodeMark v1 project=<uuid> file=<id> owner="Security Ops"
```

A ferramenta escolhe a sintaxe de comentário da linguagem. A marca não contém
restrições de uso nem altera a licença do arquivo.

## Verificar e comparar

```sh
python3 codemark.pyz verify /caminho/do/projeto
python3 codemark.pyz compare /caminho/do/projeto /pasta/suspeita
```

`verify` aponta fontes alterados, ausentes, novos e marcas removidas. Compara
com `.codemark/manifest.json`, que precisa ser preservado como referência.
Sem assinatura, essa referência é modificável como qualquer arquivo local.

`compare` procura a marca, conteúdo idêntico sem marca e semelhanças entre
tokens. A comparação aproximada ignora comentários e nomes de variáveis e
funções, mantendo literais, palavras-chave e operações. Nomes de arquivo e
pastas podem ser diferentes. É uma busca de candidatos por arquivo, não uma
prova de plágio, detector universal ou análise semântica.

```sh
python3 codemark.pyz compare /projeto /suspeito --threshold 0.80 --json
```

Use `--json --output /pasta/novo-relatorio.json` para salvar um relatório.
O destino deve ser novo para evitar sobrescrever fontes ou evidências.
O relatório deve ficar fora das pastas do projeto e da comparação. O destino
é reservado e seu conteúdo é gravado, sincronizado e fechado antes de alterar
fontes, manifesto ou assinatura. Falhas de gravação não aplicam a operação;
se a transação do projeto falhar, o relatório é removido. Consuma relatórios
somente depois de o processo terminar e confira seu código de saída.

## Assinar com OpenSSH Ed25519

Backend opcional testado nesta versão, usando `ssh-keygen` do sistema com
suporte a `-Y`. Use uma chave Ed25519 própria e sua chave pública adjacente
`ARQUIVO.pub`. Guarde a chave privada fora da árvore do projeto.

```sh
python3 codemark.pyz sign /projeto --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /projeto --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_COMPLETO'
```

Substitua o exemplo `SHA256:...` pelo fingerprint completo retornado para sua
chave. A senha, quando necessária, é tratada pelo OpenSSH local, nunca por
argumento do CodeMark. Para automação, prepare sua chave/agente previamente.
A árvore precisa estar íntegra antes de assinar; a assinatura é verificada
antes de ser gravada em `.codemark/manifest.json.sshsig`.

A verificação fixa uma única chave Ed25519 e o namespace
`codemark-manifest-v1`. Chaves incorretas, manifesto adulterado e assinaturas de
outro namespace são recusados. Não há consulta de revogação online. Preserve
manifesto, assinatura e chave pública por uma referência confiável.

## Assinar com GPG (opcional, sem qualificação neste ambiente)

Requer `gpg` para assinar e `gpgv` para verificar. Use uma chave que já é sua,
com fingerprint completo. CodeMark não cria chaves e não recebe senhas.
O agente GPG deve estar disponível e a chave desbloqueada quando necessário.

```sh
python3 codemark.pyz sign /projeto --key SEU_FINGERPRINT_COMPLETO
gpg --export SEU_FINGERPRINT_COMPLETO > owner-public.gpg
python3 codemark.pyz verify /projeto --require-signature --keyring owner-public.gpg --fingerprint SEU_FINGERPRINT_COMPLETO
```

Substitua os identificadores de exemplo pelo fingerprint completo, sem espaços.
Guarde uma cópia do manifesto, assinatura e chave pública fora da pasta do
projeto. Verifique o fingerprint por um canal independente. A verificação usa
apenas o keyring indicado e a chave fixada, sem confiar no keyring padrão.
O `gpgv` confia nas chaves desse keyring e não verifica sua expiração ou
revogação; mantenha essa referência atualizada por um canal confiável.
Após mudanças legítimas: execute `mark --apply` e assine novamente. A assinatura
antiga fica inválida até ser refeita, como esperado.

## Remover a marca

```sh
python3 codemark.pyz unmark /projeto
python3 codemark.pyz unmark /projeto --apply
```

A primeira linha mostra a prévia; a segunda remove somente a marca do projeto.
Edições de código posteriores são preservadas. O manifesto permanece como
referência anterior; `verify` passa a apontar as marcas removidas. Não se trata
de restauração de versões. Use seu controle de versão para recuperar históricos.

## Linguagens e cobertura

| Família | Exemplos |
|---|---|
| Python e scripts | Python, shell, fish, Ruby, Perl, PowerShell, Nix |
| Scheme e Lisp | Guile/Scheme, Emacs Lisp, Common Lisp, Clojure, Racket |
| Sintaxe de comentário `//` | JavaScript/TypeScript, C/C++, Rust, Go, Java, C#, Kotlin, Swift, Dart |
| Estilos e marcação | CSS/SCSS, HTML, XML, SVG, Vue, Svelte |
| Outros | SQL, Lua, YAML, TOML, CMake, Makefile |

A marcação usa comentários, sem parser ou compilador de cada linguagem.
Testes semânticos nesta entrega executam fixtures Python e JavaScript; demais
famílias têm testes de preservação e comparação, sem alegar compilação em todas
as toolchains.
Guarde alterações no Git e execute os testes do seu projeto antes de publicar.

UTF-8, BOM UTF-8 e CRLF são aceitos. JSON, PHP, binários, arquivos compactados,
histórico Git, fontes em outros encodings e pacotes minificados não recebem
marca nesta versão. Não é um scanner de segredos.
Cabeçalhos isolados sem quebra de linha, como um arquivo contendo apenas
`# coding: utf-8`, são preservados e listados fora da cobertura. Declarações
XML e CSS `@charset`, cookies do Emacs e diretivas Ruby são mantidos antes da marca.

Exclusões: `.git`, `.hg`, `.svn`, `.codemark`, `.venv`, `venv`, `node_modules`,
`vendor`, `third_party`, `third-party`, `dist`, `build`, `target`, caches Python.
O relatório JSON lista o que ficou fora da cobertura. Diretórios excluídos
não são percorridos. Arquivos assinados PowerShell são preservados e ignorados.
Outros formatos com assinatura especial devem ficar fora da raiz tratada.

Limites por operação: 5.000 fontes, 2 MiB por fonte, 64 MiB somados (sem contar
as marcas do cabeçalho), 20.000 entradas e 64 níveis de diretórios. Comparação:
2.000.000 pares e 10.000 candidatos. Limites excedidos geram erro, sem lista
parcial apresentada como completa. A enumeração é interrompida no teto de
entradas. Selecione um módulo menor.
Metadados gerados e lidos têm teto de 64 MiB; a saída é validada antes de gravar.
Links simbólicos no caminho/árvore tratada e arquivos especiais são recusados.
Trabalhe com a árvore estável, sem editores ou builds escrevendo simultaneamente.

## Integração, testes e licença

- [Integração em CI, GNU Guix e controle de versão](docs/INTEGRATION.md)
- [Modelo de ameaças e limites](docs/THREAT_MODEL.md)
- [Validação e plataformas testadas](docs/VALIDATION.md)
- [Prompt executado para a versão 0.2.0](PROMPT-PRODUCAO-0.2.0.md)
- [Prompt original da versão 0.1.0](PROMPT-GOD-TIER.md)
- [Licença GPL completa](COPYING)

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

A construção gera `dist/codemark.pyz`, ZIP completo e `SHA256SUMS`. É
determinística no mesmo ambiente e conteúdo. O ZIP contém fontes, testes,
documentação e executável portátil. Checksums detectam mudanças contra uma
referência confiável; não autenticam downloads por conta própria.

Copyright (C) 2026 SecOps CodeMark contributors. Este programa é software
livre; você pode redistribuí-lo e/ou modificá-lo sob a GNU GPL versão 3 ou,
a seu critério, qualquer versão posterior. Distribuído sem garantia.
