# SecOps Codemark

**Integridade de arquivos, assinaturas híbridas e procedência local.**

[English](README.md) · [Documentação](https://codemark.securityops.co/pt-br/docs/) · [Wiki](https://codemark.securityops.co/pt-br/wiki/) · [Evidências da versão](https://codemark.securityops.co/pt-br/evidence/)

Versão **0.4.0** · **GPL-3.0-or-later** · [Licença completa](COPYING)

SecOps Codemark registra SHA-256 e SHA-512 de arquivos regulares de qualquer formato, autentica a referência com **ML-DSA-87 + Ed25519** e encadeia atestações num histórico local verificável. Uma exportação privada explícita pode usar criptografia **Zupt ML-KEM-768 + X25519** para destinatário. Comentários reversíveis de fontes e análise de possíveis cópias continuam separados.

A CLI funciona localmente com Python 3.10+ e biblioteca padrão. Assinatura híbrida também requer **OpenSSL 3.5+ com provider padrão**; bundles privados precisam de **Zupt nativo 5.2.10+**. Não exige serviço de rede. O módulo e o portátil continuam `codemark` e `codemark.pyz`; o site permanece `codemark.securityops.co`.

Assinatura não oculta conteúdo, comprova titularidade jurídica nem estabelece data confiável. Detectar substituição por histórico antigo válido exige checkpoint esperado independente. Padrões de algoritmos não constituem certificação FIPS 140 do aplicativo. Leia [Segurança](docs/pt-BR/security.md).

## Começar pelo snapshot

Baixe `codemark.pyz` ou os fontes públicos em **`secops-codemark-0.4.0.zupt` genuíno sem criptografia** em [Downloads](https://codemark.securityops.co/pt-br/downloads/). Confira SHA-256 contra referência independente confiável. Extraia fontes com Zupt; o portátil Python não precisa de extração.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
python3 codemark.pyz snapshot /projeto --json
python3 codemark.pyz snapshot /projeto --apply --json
python3 codemark.pyz verify /projeto --json
```

`snapshot` mostra prévia sem `--apply`. Lê arquivos regulares em blocos, incluindo JSON, ocultos, sem extensão, documentação, binários, compactados e ISOs, sem mudar conteúdo. Registra exclusões explícitas para `.codemark`, `.git`, `.hg` e `.svn`. Recusa links, arquivos especiais e mudanças simultâneas detectadas. Cobre arquivos, não diretórios vazios ou imagem completa de filesystem.

Os tetos são **100 GiB por arquivo, 1 TiB no total e 100.000 arquivos regulares**, além de limites de metadados e enumeração. São capacidades de aceitação, não benchmarks. Use árvore estável e confira a cobertura. Veja [Integridade](docs/pt-BR/integrity.md).

No Windows, use `py -3` e caminhos nativos entre aspas. No checkout, também pode usar `python3 -m codemark`. Leia cada `skip` e as [evidências de plataforma](https://codemark.securityops.co/pt-br/evidence/).

## Autenticar com duas chaves

Use chaves privadas PEM existentes ML-DSA-87 e Ed25519 fora do projeto. Ambas as assinaturas são obrigatórias; a verificação exige os dois fingerprints públicos completos e confiáveis independentemente.

```sh
python3 codemark.pyz sign /projeto --pq-key /fora/chaves/mldsa87.pem --classical-key /fora/chaves/ed25519.pem --json
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --json
```

O exemplo usa chaves sem criptografia protegidas pela sua política local. Chaves criptografadas exigem `--passphrase-file` compartilhado; não há prompt interativo. Veja [Assinaturas](docs/pt-BR/signing.md) para fingerprints DER SPKI e tratamento de chaves.

Os bytes exatos de `.codemark/integrity.json` são vinculados pelos digests SHA-256 e SHA-512 no payload canônico assinado. `.codemark/attestations.json` guarda os registros encadeados. Salve o checkpoint mais recente fora da árvore e informe `--checkpoint SHA512_COMPLETO_MINUSCULO` para detectar rollback para uma cadeia antiga válida. Veja [Rastreabilidade](docs/pt-BR/traceability.md).

`verify` escolhe o snapshot quando presente; sem dois fingerprints, confere integridade sem autenticação. `audit` exige snapshot, histórico e dois fingerprints. Opções GPG/OpenSSH legadas autenticam só o manifesto de comentários e não autenticam um snapshot completo selecionado.

## Criptografar uma exportação privada

```sh
python3 codemark.pyz bundle /projeto --recipient-key /confiavel/recipient.pub --recipient-fingerprint 'SHA256:SEU_FINGERPRINT_DESTINATARIO' --archive /exportacoes/privado.zupt --json
python3 codemark.pyz bundle /projeto --recipient-key /confiavel/recipient.pub --recipient-fingerprint 'SHA256:SEU_FINGERPRINT_DESTINATARIO' --archive /exportacoes/privado.zupt --apply --json
```

É uma operação separada de confidencialidade. Inclui regulares da árvore escolhida, inclusive histórico VCS e metadados `.codemark`. Mantenha chaves privadas, arquivos de senha e segredos sem relação fora da árvore, confira a prévia e use destino externo novo. O destinatário lê o conteúdo após descriptografar. Fontes públicos continuam sem criptografia. Veja [Criptografia](docs/pt-BR/encryption.md) para preparar destinatário, fingerprint e restauração.

A extração pelo Zupt nativo 5.2.10 usa a umask atual e não restaura modos POSIX. Leia a [orientação de restauração](docs/pt-BR/encryption.md#restaurar-e-verificar) antes de auditar a árvore extraída.

## Comentários e comparação de fontes

```sh
python3 codemark.pyz mark /modulo-proprio --owner "Seu nome ou organização"
python3 codemark.pyz mark /modulo-proprio --owner "Seu nome ou organização" --apply
python3 codemark.pyz compare /modulo-proprio /suspeito --threshold 0.80 --json
python3 codemark.pyz unmark /modulo-proprio --apply
```

`mark` continua operando comentários de formatos cobertos, com exclusões de dependências e tetos menores. Não marca JSON, binários nem ISOs. Execute testes do projeto após marcar. Comentários são removíveis e não mudam a licença. Similaridade é pontuação de sketches limitados, não conclusão de plágio ou porcentagem de linhas copiadas.

A GUI Tkinter opcional atende o fluxo legado de comentários. Use a CLI para snapshots completos e atestações híbridas. Ao combinar fluxos, conclua as edições antes do snapshot que será assinado.

## Documentação e evidências

| Tema | Português brasileiro | English |
| --- | --- | --- |
| Início | [Primeiros passos](docs/pt-BR/getting-started.md) | [Get started](docs/en/getting-started.md) |
| Cobertura de arquivos | [Integridade](docs/pt-BR/integrity.md) | [Integrity](docs/en/integrity.md) |
| Comandos | [Referência da CLI](docs/pt-BR/cli.md) | [CLI reference](docs/en/cli.md) |
| Chaves híbridas e legadas | [Assinaturas](docs/pt-BR/signing.md) | [Signing](docs/en/signing.md) |
| Histórico e rollback | [Rastreabilidade](docs/pt-BR/traceability.md) | [Traceability](docs/en/traceability.md) |
| Exportação privada | [Criptografia](docs/pt-BR/encryption.md) | [Encryption](docs/en/encryption.md) |
| CI e manutenção | [Integração](docs/pt-BR/integration.md) | [Integration](docs/en/integration.md) |
| Exemplos e avaliação | [Evidências](docs/pt-BR/evidence.md) | [Evidence](docs/en/evidence.md) |
| Escopo e testes | [Validação](docs/pt-BR/validation.md) | [Validation](docs/en/validation.md) |
| Confiança | [Segurança](docs/pt-BR/security.md) | [Security](docs/en/security.md) |
| Wiki | [Arquitetura](docs/pt-BR/wiki/architecture.md) | [Architecture](docs/en/wiki/architecture.md) |

Relatórios históricos 0.2.0 e 0.3.0 permanecem inalterados e identificados por versão. Não qualificam fontes alterados nem caminhos criptográficos novos. Resultados, ausências, datas e escopos atuais ficam na [página de evidências](https://codemark.securityops.co/pt-br/evidence/). Em uso nos projetos do mantenedor.

## Desenvolver

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

O build gera portátil, árvore de fontes e manifesto SHA-256; `--archive` usa Zupt instalado para `.zupt` público genuíno. Teste e compare a extração com a revisão pretendida. Leia [Contribuição](CONTRIBUTING.md) e [Política de segurança](SECURITY.md).

O site usa HTML, CSS e SVG locais, sem JavaScript, rastreamento ou fontes remotas. Instruções em [website/README.md](website/README.md).

## Repositórios

- [GitHub · cristiancmoises/secops-codemark](https://github.com/cristiancmoises/secops-codemark)
- [Codeberg · berkeley/secops-codemark](https://codeberg.org/berkeley/secops-codemark)
- [Security Ops Forgejo · git.securityops.co](https://git.securityops.co/cristiancmoises/secops-codemark)
- [Security Ops Forgejo · git.securityops.com.br](https://git.securityops.com.br/cristiancmoises/secops-codemark)

Copyright (C) 2026 SecOps Codemark contributors. GPL-3.0-or-later, sem garantia. As licenças existentes dos projetos marcados continuam aplicáveis.
