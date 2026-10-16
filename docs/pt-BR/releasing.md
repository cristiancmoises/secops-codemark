# Preparar e publicar um lançamento

Use um checkout limpo e revisado, com Python 3.10+. O pacote público de fontes também requer Zupt nativo 5.2.10+. Os comandos abaixo usam shell POSIX e diretórios temporários novos; no Windows, adapte os caminhos entre aspas e execute o Python de várias linhas em um arquivo.

## Revisar entradas e escolher saídas novas

Confira `git status --short --untracked-files=all`, os diretórios selecionados e os arquivos que realmente serão distribuídos. Mantenha chaves, credenciais, históricos privados e dados alheios fora deles. Filtros de nomes não provam ausência de segredos dentro de arquivos de fonte comuns.

A versão 0.4.1 recusa raízes de fonte que sejam links e destinos de release conflitantes antes do empacotamento. Use uma saída nova em cada tentativa. Não apague nem substitua um artefato existente apenas para permitir a repetição. Falhas do compressor nativo ou do teste do arquivo podem deixar saídas incompletas; preserve o log e inicie outra tentativa em outro diretório.

## Gerar e exercitar o portátil

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --output /tmp/secops-codemark-release-0.4.1 --archive
python3 -I /tmp/secops-codemark-release-0.4.1/codemark.pyz self-test --json
zupt test /tmp/secops-codemark-release-0.4.1/secops-codemark-0.4.1.zupt
```

Execute o portátil também a partir de um diretório de trabalho fora do checkout. Registre versões das ferramentas, códigos de saída, ausências opcionais e a revisão exata. O pacote público de fontes é `.zupt` genuíno sem criptografia; o executável Python permanece `codemark.pyz`.

Extraia o pacote em um diretório novo de verificação e compare cada arquivo versionado, byte a byte, com a revisão pretendida. Permita somente dois acréscimos gerados: `codemark.pyz` e o `SHA256SUMS` interno. Confira a cobertura dos checksums internos e a igualdade entre o portátil incluído e o artefato separado. Recuse arquivos ausentes, adicionais ou alterados. O Zupt nativo 5.2.10 não restaura modos POSIX nem ACLs; essa comparação qualifica os bytes.

## Preparar downloads antes da verificação estrita do site

O gerador do site cria documentação e links locais de download. Ele não gera arquivos de release. A opção estrita `--check` precisa falhar quando faltar um download local declarado. Gere primeiro um diretório novo do site:

```sh
python3 scripts/build_site.py --output /tmp/secops-codemark-site-0.4.1
```

Confira os dois checksums dos artefatos e copie os três arquivos para um diretório de downloads novo:

```sh
python3 - <<'PY'
import hashlib
import shutil
from pathlib import Path

release = Path('/tmp/secops-codemark-release-0.4.1')
downloads = Path('/tmp/secops-codemark-site-0.4.1/downloads')
rows = [line.split('  ', 1) for line in (release / 'SHA256SUMS').read_text().splitlines()]
checks = {name: digest for digest, name in rows}
assert len(rows) == len(checks) == 2
assert set(checks) == {'codemark.pyz', 'secops-codemark-0.4.1.zupt'}
for name, expected in checks.items():
    assert hashlib.sha256((release / name).read_bytes()).hexdigest() == expected
downloads.mkdir(parents=True, exist_ok=False)
for name in (*checks, 'SHA256SUMS'):
    shutil.copyfile(release / name, downloads / name)
PY
python3 scripts/build_site.py --output /tmp/secops-codemark-site-0.4.1 --check
```

A igualdade de checksums detecta diferenças em relação à lista; não autentica o publicador de forma independente. Guarde revisão e hashes esperados em um registro confiável do lançamento. Como alternativa, um `path` explícito no metadado do site copia arquivo regular de `dist/`; a URL local precisa corresponder ao nome.

O gerador recusa nomes de relatório duplicados e colisões no nome-base das rotas antes de escrever o site. Extensões diferentes não tornam segura a publicação de dois relatórios na mesma rota.

## Etapas obrigatórias de publicação

- Exija a suíte completa, verificações do portátil, revisão dos fontes e a matriz CI final Linux/Windows para a revisão pretendida. Preserve falhas e ausências com precisão.
- Registre evidência nova para fontes modificados. Medições históricas de similaridade e pipeline mantêm versões e hashes originais.
- Confira árvore, conteúdo do pacote e metadados para não publicar instruções privadas de execução ou credenciais. Revise o conteúdo dos fontes, além dos nomes.
- Crie uma tag anotada nova com a identidade Git configurada. Envie commits revisados e a tag às contas verificadas; preserve refs e releases existentes.
- Publique `.zupt` genuíno sem criptografia, `codemark.pyz` e `SHA256SUMS`; baixe e confira o hash de cada artefato público. Assets externos nativos do Forgejo podem apontar a arquivos versionados e verificados de outro remoto; informe essa hospedagem explicitamente.
- Ative somente o site estático verificado, por troca atômica de diretório, preservando a versão anterior. Confira idiomas, relatórios, cabeçalhos HTTPS e bytes dos downloads públicos. Use navegador real para layout, teclado e movimento reduzido.

Consulte [Validação](validation.md), [Integração](integration.md) e a [referência de build do site](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.1/website/README.md).
