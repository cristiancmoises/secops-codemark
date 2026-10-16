# Validação da versão 0.2.0

Veredito: **apta para produção no escopo CLI em GNU/Linux**, como ferramenta
local de procedência, integridade e triagem de cópias. Assinatura OpenSSH
Ed25519 qualificada no ambiente abaixo. A qualificação não afirma impedir
REA nem constitui certificação de segurança.

## Comandos reproduzíveis

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -I dist/codemark.pyz self-test --json
```

## Evidência

- Suíte: **71 testes**, sem falhas ou erros. Uma classe de integração GPG
  suspensa explicitamente porque o ambiente bloqueia sockets do gpg-agent.
- **13 testes reais OpenSSH**, com chaves Ed25519 efêmeras: chave/fingerprint
  errados, namespace diferente, adulteração, par de chaves incompatível,
  árvore desatualizada, CLI autenticada e falha ao publicar relatório.
- Erros reais de limite de tamanho de arquivo (2.048 bytes) em escrita e
  flush de relatórios não marcam nem desmarcam fontes, não publicam assinatura
  e removem o arquivo parcial. Falha posterior no projeto também reverte
  fontes e remove o relatório concluído.
- Autoteste portátil em Python isolado, fora do repositório: marcação,
  verificação, execução de fixtures Python/JavaScript, assinatura SSH,
  detecção de adulteração, comparação e remoção passaram.
- Fixture Scheme: preservação coberta, execução Guile explicitamente suspensa
  porque a ferramenta não está disponível neste host.
- Round-trip byte a byte preserva BOM, CRLF, shebang, encoding, modos,
  prologues e strings que contêm marcas semelhantes.
- Portátil e ZIP determinísticos em duas construções no mesmo ambiente;
  hashes internos conferidos. O teste de empacotamento executa o portátil
  fora do repositório em modo isolado.
- Limites de 5.000 fontes, 2 MiB por fonte, 64 MiB total, 20.000 entradas e
  10.000 candidatos incluem testes de regressão dos limites modificados.
- Revisão independente inicial e re-revisão das correções concluídas;
  detalhes em `REVIEW_0.2.0.md`.

## Ambiente e limites

GNU/Linux x86_64, Python 3.12.14, Node e OpenSSH instalados. A versão exata do
interpretador e o hash do portátil acompanham `QUALIFICATION.json`.
Tkinter pode ser importado, sem sessão gráfica para validar sua renderização.
Windows, Guix completo e Guile não foram executados neste host.

Não foi executado REA, código real de terceiros ou fonte do usuário. Nenhuma
chave pessoal foi usada. Não houve deploy ou publicação em GitHub. Nenhum
benchmark novo de velocidade é alegado para esta versão.

Antes de aplicar no seu host, execute `self-test`, confira todos os `skip` e
rode os testes do seu projeto após a marcação. Guarde o commit anterior para
rollback. O autoteste não certifica programas arbitrários nem outros sistemas.

A validação anterior de 0.1.0 permanece no histórico Git e no pacote daquela
versão. Consulte `CHANGELOG.md` para as alterações da 0.2.0.
