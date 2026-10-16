# Primeiros passos

CodeMark adiciona um comentário reversível de procedência aos fontes, registra integridade SHA-256 e procura possíveis cópias de código. Funciona localmente com Python 3.10 ou superior e sua biblioteca padrão. A CLI não precisa de conexão de rede, modelo de IA ou dependência pip.

## Instalar e conferir

Baixe o portátil `codemark.pyz` de uma versão verificada do projeto, ou execute o checkout com `python3 -m codemark`. Confira o artefato contra um checksum obtido por canal confiável. O checksum sozinho não autentica quem publicou o arquivo.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

O autoteste usa fixtures temporárias e chaves efêmeras. Leia cada `skip`: uma ferramenta opcional ausente não passou no teste. O autoteste não certifica seu projeto nem todas as linguagens cobertas.

## Prévia de um módulo próprio

Comece com um checkout limpo, versionado e com os testes do projeto funcionando. Escolha uma pasta de fontes próprios. Mantenha bibliotecas de terceiros, arquivos gerados, formatos assinados e chaves privadas fora dela.

```sh
python3 codemark.pyz mark /caminho/do/projeto --owner "Seu nome ou organização"
```

Sem `--apply`, `mark` só apresenta uma prévia. Confira os arquivos e as entradas `skipped` do JSON antes de continuar.

```sh
python3 codemark.pyz mark /caminho/do/projeto --owner "Seu nome ou organização" --apply
python3 codemark.pyz verify /caminho/do/projeto --json
```

Execute os testes do seu projeto após marcar. Versione os fontes pretendidos e `.codemark/project.json` e `.codemark/manifest.json`. Não versione `.codemark/lock`. Preserve uma referência independente.

## Após edições legítimas

Revise as mudanças, execute `mark /caminho/do/projeto --apply` e rode os testes do projeto novamente. Se usa assinatura, assine o novo manifesto. Uma assinatura antiga não autentica um manifesto substituído.

## Remover comentários

```sh
python3 codemark.pyz unmark /caminho/do/projeto
python3 codemark.pyz unmark /caminho/do/projeto --apply
```

O primeiro comando mostra a prévia. O segundo remove apenas as marcas deste projeto e preserva edições posteriores. O manifesto anterior permanece e a verificação aponta marcas removidas. Use Git ou backup para recuperar uma versão anterior do fonte.

## Interface local opcional

```sh
python3 codemark.pyz gui
```

A interface precisa de Tkinter e sessão gráfica. No Windows, substitua `python3` por `py -3`. A qualificação de plataformas e componentes opcionais está em [Validação](validation.md).

Continue na [referência da CLI](cli.md), no [guia de assinatura](signing.md) e no [modelo de segurança](security.md).
