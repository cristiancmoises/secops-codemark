# CODEMARK

**Procedência local de fontes, verificação de integridade e análise de possíveis cópias.**

[English](README.md) · [Documentação](https://codemark.securityops.co/pt-br/docs/) · [Wiki](https://codemark.securityops.co/pt-br/wiki/) · [Evidências](https://codemark.securityops.co/pt-br/evidence/)

CodeMark adiciona comentários reversíveis de procedência aos seus fontes, registra um manifesto SHA-256, permite assinar essa referência e procura possíveis cópias em outra árvore. A CLI funciona offline com **Python 3.10+ e biblioteca padrão**. Não exige modelo de IA, telemetria, servidor ou dependências pip.

Versão **0.3.0** · **GPL-3.0-or-later** · [Licença completa](COPYING)

Uma marca pode ser removida ou forjada. Uma assinatura vincula o manifesto à chave fixada; não comprova data confiável, originalidade ou titularidade jurídica. Relatórios de similaridade orientam revisão manual. A marcação não muda a licença do projeto nem impede engenharia reversa.

## Começar

Baixe o portátil `codemark.pyz` ou o lançamento de fontes em `.zupt` na [página de downloads](https://codemark.securityops.co/pt-br/downloads/). Confira os checksums SHA-256 contra referência confiável. Extraia os fontes com `zupt`; o portátil precisa apenas de Python.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

Leia cada `skip`: uma ferramenta opcional ausente não foi validada. O autoteste usa fixtures temporárias e chaves efêmeras, sem usar seus fontes ou chaves pessoais. Consulte as [evidências atuais](https://codemark.securityops.co/pt-br/evidence/) para escopo medido e limitações.

Comece com módulo próprio versionado, limpo e com testes passando. Confira a prévia antes de aplicar:

```sh
python3 codemark.pyz mark /caminho/do/projeto --owner "Seu nome ou organização"
python3 codemark.pyz mark /caminho/do/projeto --owner "Seu nome ou organização" --apply
python3 codemark.pyz verify /caminho/do/projeto --json
```

Execute os testes do projeto novamente. Versione os fontes pretendidos e `.codemark/project.json` e `.codemark/manifest.json`. Não versione `.codemark/lock`. Preserve uma referência independente. Aplicações posteriores podem omitir `--owner`.

No checkout, use `python3 -m codemark` no lugar de `python3 codemark.pyz`. No Windows, substitua `python3` por `py -3`.

## Comparar e remover

```sh
python3 codemark.pyz compare /projeto /suspeito --threshold 0.80 --json
python3 codemark.pyz unmark /projeto
python3 codemark.pyz unmark /projeto --apply
```

A comparação encontra identificadores, conteúdo idêntico sem marca e fingerprints aproximados de tokens. Pode encontrar arquivos renomeados e alguns identificadores alterados. A pontuação descreve sketches limitados, não porcentagens de linhas copiadas. Falsos positivos e negativos são possíveis.

`unmark` mostra prévia por padrão e preserva edições posteriores quando aplicado. O manifesto anterior permanece; `verify` acusa as marcas removidas. Use Git ou backups para recuperar versões anteriores.

## Autenticar a referência

A assinatura opcional OpenSSH Ed25519 precisa de `ssh-keygen` local com `-Y`. Use uma chave existente fora do projeto, com `.pub` adjacente:

```sh
python3 codemark.pyz sign /projeto --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /projeto --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_COMPLETO'
```

Substitua o exemplo pelo seu fingerprint completo e confiável. CodeMark fixa chave e namespace `codemark-manifest-v1`. OpenPGP opcional também está disponível. Leia [Assinaturas](docs/pt-BR/signing.md) e seus limites de confiança e revogação.

## Automação e cobertura

| Código | Significado |
| --- | --- |
| `0` | Concluído; íntegro; sem candidatos; ou autoteste sem falhas |
| `1` | Divergências, candidatos de comparação ou falhas no autoteste |
| `2` | Erro de entrada, acesso, ferramenta necessária ou interrupção |

Use `--json --output /relatorios/NOVO.json` para relatório novo externo às árvores. Consuma o arquivo após o término e confira o código de saída. No CI, verifique a referência revisada; executar `mark --apply` antes aceitaria as mudanças atuais como referência.

Os estilos cobrem Python, shell, Scheme/Lisp, JavaScript/TypeScript, C/C++, Rust, Go, Java, CSS, HTML/XML, SQL, Lua, YAML, TOML e outros. É cobertura de comentário, não qualificação por compilação de cada linguagem. UTF-8/BOM e CRLF cobertos são preservados. JSON, PHP, binários, pacotes minificados e formatos com assinaturas especiais ficam fora. Leia `skipped` no JSON.

Diretórios conhecidos de dependências e builds são excluídos. Links e arquivos especiais são recusados. Os limites incluem 5.000 fontes, 2 MiB por fonte, 64 MiB total, 20.000 entradas e comparações limitadas. Use árvore estável; rollback comum não oferece recuperação após queda de energia ou encerramento forçado. Consulte [Formatos](docs/pt-BR/wiki/formats.md) e [Segurança](docs/pt-BR/security.md).

A GUI Tkinter opcional abre com `python3 codemark.pyz gui` e precisa de sessão gráfica. A qualificação de componentes opcionais e plataformas é informada separadamente.

## Documentação

| Tema | Português brasileiro | English |
| --- | --- | --- |
| Início | [Primeiros passos](docs/pt-BR/getting-started.md) | [Get started](docs/en/getting-started.md) |
| Comandos | [Referência da CLI](docs/pt-BR/cli.md) | [CLI reference](docs/en/cli.md) |
| Assinaturas | [Assinaturas](docs/pt-BR/signing.md) | [Signing](docs/en/signing.md) |
| CI e lançamentos | [Integração](docs/pt-BR/integration.md) | [Integration](docs/en/integration.md) |
| Segurança | [Modelo de segurança](docs/pt-BR/security.md) | [Threat model](docs/en/security.md) |
| Resultados medidos | [Validação](docs/pt-BR/validation.md) | [Validation](docs/en/validation.md) |
| Wiki | [Arquitetura](docs/pt-BR/wiki/architecture.md) | [Architecture](docs/en/wiki/architecture.md) |

A qualificação e revisão da 0.2.0 permanecem como registros históricos versionados. Não qualificam fontes alterados de outra versão. Resultados atuais, ausências, datas e escopos são publicados na [página de evidências](https://codemark.securityops.co/pt-br/evidence/).

## Desenvolver

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

O build gera portátil determinístico, árvore de fontes e manifesto SHA-256. `python3 scripts/build.py --archive` usa `zupt` instalado para criar um arquivo `.zupt` genuíno. Leia [Contribuição](CONTRIBUTING.md) e [Segurança](SECURITY.md).

O site usa HTML, CSS e SVG locais, sem JavaScript. A biblioteca padrão do Python gera os arquivos; veja [website/README.md](website/README.md).

## Repositórios

- [GitHub · cristiancmoises/codemark](https://github.com/cristiancmoises/codemark)
- [Codeberg · berkeley/codemark](https://codeberg.org/berkeley/codemark)
- [Security Ops Forgejo · git.securityops.co](https://git.securityops.co/cristiancmoises/codemark)
- [Security Ops Forgejo · git.securityops.com.br](https://git.securityops.com.br/cristiancmoises/codemark)

Copyright (C) 2026 CodeMark contributors. Software livre sob a GNU GPL versão 3 ou posterior, distribuído sem garantia. As licenças existentes dos projetos marcados continuam válidas.
