# Assinar e autenticar uma referência

A versão 0.4.0 adiciona atestações híbridas ML-DSA-87 + Ed25519 ao snapshot de todos os arquivos. As duas assinaturas são obrigatórias nesse modo. OpenSSH e OpenPGP legados continuam como opções separadas do manifesto de comentários de fontes.

Uma assinatura autentica a referência contra chaves confiáveis. Não criptografa arquivos, estabelece data confiável nem comprova originalidade ou titularidade jurídica.

## Pré-requisitos híbridos

Use OpenSSL 3.5 ou superior com provider padrão embutido e chaves privadas PEM existentes ML-DSA-87 e Ed25519. `--classical-key` recebe PEM do OpenSSL, não o formato privado OpenSSH usado por `--ssh-key` legado.

```sh
openssl version
python3 codemark.pyz doctor --json
```

Mantenha chaves e arquivo de senha fora do projeto. A assinatura não tem stdin interativo: chaves criptografadas precisam de `--passphrase-file`, e as duas precisam usar a mesma senha desse arquivo. Sem arquivo de senha, use chaves sem criptografia protegidas por sua política local; chaves criptografadas são recusadas sem abrir prompt.

SecOps Codemark não gera essas chaves de assinatura. Consulte a [documentação nativa de geração do OpenSSL](https://docs.openssl.org/3.5/man1/openssl-genpkey/) ao prepará-las no seu ambiente protegido. A implementação usa o provider padrão e não afirma certificação FIPS 140.

## Calcular os dois fingerprints públicos

Exporte cada chave pública em DER SubjectPublicKeyInfo pelo OpenSSL. Comandos OpenSSL nativos podem usar seu próprio prompt de senha; isso é separado da assinatura não interativa do SecOps Codemark.

```sh
openssl pkey -in /fora/chaves/mldsa87.pem -pubout -outform DER -out /confiavel/mldsa87-public.der
openssl pkey -in /fora/chaves/ed25519.pem -pubout -outform DER -out /confiavel/ed25519-public.der
```

O fingerprint é `SHA256:` mais Base64 sem padding do SHA-256 do arquivo DER SPKI inteiro. Calcule sobre os bytes públicos:

```sh
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /confiavel/mldsa87-public.der
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /confiavel/ed25519-public.der
```

Registre ambos os fingerprints completos por canal independente confiável. Não confie numa chave apenas por estar embutida numa atestação não confiável. Hash de texto PEM e fingerprint do arquivo público de destinatário Zupt usam entradas diferentes.

## Assinar um snapshot íntegro

```sh
python3 codemark.pyz snapshot /projeto --apply --json
python3 codemark.pyz sign /projeto --pq-key /fora/chaves/mldsa87.pem --classical-key /fora/chaves/ed25519.pem --passphrase-file /fora/chaves/senha-assinatura --json
```

Omita `--passphrase-file` apenas com chaves privadas sem criptografia. Não coloque a senha em argumentos ou histórico do shell. Trate seu arquivo como segredo e proteja as permissões.

As duas assinaturas cobrem payload canônico que vincula SHA-256 e SHA-512 dos bytes exatos de `.codemark/integrity.json`, identidade, fingerprints, sequência, horário local e hash anterior. O registro fica em `.codemark/attestations.json`. Reformatar o snapshot muda a referência autenticada.

## Autenticar e conferir o histórico

```sh
python3 codemark.pyz verify /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --json
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --json
```

As duas chaves fixadas são obrigatórias para autenticar. Confira o resultado de integridade e o de autenticação. Para detectar substituição por histórico antigo válido, forneça também um `--checkpoint` esperado independente; veja [Rastreabilidade](traceability.md).

## OpenSSH Ed25519 legado

O manifesto de comentários aceita o backend OpenSSH existente. Requer `ssh-keygen` local com `-Y`, chave Ed25519 fora do projeto e `.pub` adjacente.

```sh
python3 codemark.pyz sign /projeto --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /projeto --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_OPENSSH_COMPLETO'
```

Esse backend usa namespace `codemark-manifest-v1` e `.codemark/manifest.json.sshsig`. É assinatura clássica, distinta da atestação híbrida. O OpenSSH trata seu próprio agente e senha.

## OpenPGP legado

A assinatura opcional OpenPGP precisa de `gpg`, `gpgv`, fingerprint completo de chave existente e keyring público dedicado.

```sh
python3 codemark.pyz sign /projeto --key SEU_FINGERPRINT_GPG_COMPLETO
gpg --export SEU_FINGERPRINT_GPG_COMPLETO > owner-public.gpg
python3 codemark.pyz verify /projeto --require-signature --keyring /confiavel/owner-public.gpg --fingerprint SEU_FINGERPRINT_GPG_COMPLETO
```

Use `--require-signature`, `--keyring` e `--fingerprint` juntos. Não combine backends na mesma operação. O operador gerencia origem, rotação, comprometimento e revogação; não há descoberta online de revogações.

Consulte [Validação](validation.md) para cobertura medida de backends e plataformas.
