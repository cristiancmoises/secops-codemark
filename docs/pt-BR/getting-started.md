# Primeiros passos

SecOps Codemark 0.4.0 inventaria arquivos regulares, autentica a referência com assinaturas híbridas e permite exportação privada criptografada. Comentários reversíveis e comparação de fontes continuam como operações separadas.

A CLI Python usa biblioteca padrão e funciona localmente. Assinatura híbrida também requer OpenSSL 3.5 com provider padrão. Bundles privados precisam de Zupt compatível. Disponibilidade e cobertura medida de plataformas são informadas separadamente.

## Conferir o host

Baixe o portátil `codemark.pyz` ou o lançamento público de fontes em `.zupt` genuíno sem criptografia. Confira o checksum contra referência independente confiável. No checkout, também é possível usar `python3 -m codemark`.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

Leia cada `skip`; uma ferramenta ausente não passou no teste. Fixtures não certificam seu projeto. Consulte [Validação](validation.md).

Os exemplos usam caminhos POSIX. No Windows, troque `python3` por `py -3` e use caminhos nativos entre aspas, como `"C:\Projetos\release"` e `"C:\Chaves\mldsa87.pem"`. OpenSSL e Zupt precisam estar disponíveis para suas operações; um resultado Linux não qualifica Windows.

## Escolher a operação

| Objetivo | Operação | Cobertura |
| --- | --- | --- |
| Registrar integridade sem mudar conteúdo | `snapshot` | Todos os formatos regulares, com exclusões explícitas de metadados/VCS |
| Autenticar referência e histórico | `sign` híbrido, depois `audit` | Snapshot, duas assinaturas e fingerprints confiáveis independentes |
| Exportar dados confidenciais | `bundle` | Arquivo explicitamente criptografado para destinatário da árvore escolhida |
| Adicionar procedência removível | `mark` | Somente formatos de fontes próprios cobertos |
| Procurar possíveis cópias | `compare` | Candidatos por marca, conteúdo exato e sketch de tokens |

## Gerar um snapshot

Use árvore estável. Mantenha chaves privadas, arquivos de senha e pacotes de saída fora dela.

```sh
python3 codemark.pyz snapshot /projeto --json
python3 codemark.pyz snapshot /projeto --apply --json
python3 codemark.pyz verify /projeto --json
```

O primeiro comando mostra a prévia; o segundo salva `.codemark/integrity.json`. JSON, ocultos, arquivos sem extensão, binários e ISOs entram como bytes regulares. Leia exclusões e tetos em [Integridade](integrity.md). Verificar sem assinatura confere divergências sem autenticar a referência.

## Adicionar autenticação

Use chaves PEM existentes ML-DSA-87 e Ed25519 e confira com os dois fingerprints completos confiáveis por canal independente:

```sh
python3 codemark.pyz sign /projeto --pq-key /fora/chaves/mldsa87.pem --classical-key /fora/chaves/ed25519.pem --json
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --json
```

O exemplo usa chaves sem criptografia protegidas pela sua política de armazenamento. Chaves criptografadas exigem `--passphrase-file` compartilhado; não há prompt interativo. Leia [Assinaturas](signing.md). Guarde o checkpoint retornado independentemente quando precisar detectar rollback para cadeia antiga válida; veja [Rastreabilidade](traceability.md).

## Comentários opcionais

Escolha módulo de fontes próprios com testes passando:

```sh
python3 codemark.pyz mark /modulo-proprio --owner "Seu nome ou organização"
python3 codemark.pyz mark /modulo-proprio --owner "Seu nome ou organização" --apply
python3 codemark.pyz unmark /modulo-proprio --apply
```

`mark` e `unmark` mostram prévia sem `--apply`. Comentários são removíveis e não mudam a licença. Rode os testes após marcar. Essa cobertura não se estende a binários ou JSON. Se também precisa de snapshot, gere-o após concluir as edições pretendidas.

A interface Tkinter opcional abre com `python3 codemark.pyz gui` e atende o fluxo legado de comentários. Use a CLI para inventário de todos os arquivos e atestações híbridas.

Continue em [Referência da CLI](cli.md), [exportação criptografada](encryption.md) e [Segurança](security.md).
