# Assinar uma referência confiável

A assinatura autentica o manifesto contra uma chave fixada. Ela não estabelece data confiável, originalidade ou titularidade jurídica. Mantenha chaves privadas fora do projeto e distribua chaves públicas e fingerprints completos por canal independente e confiável.

## OpenSSH Ed25519

Use uma chave privada Ed25519 existente com arquivo `.pub` adjacente. O `ssh-keygen` do sistema precisa oferecer assinatura com `-Y`.

```sh
python3 codemark.pyz sign /projeto --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /projeto --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_COMPLETO'
```

Substitua o exemplo pelo fingerprint completo e exato da sua chave. O OpenSSH trata a senha pelos seus recursos locais. Prepare chave e agente antes de uso automatizado.

CodeMark verifica a integridade da árvore antes de assinar e confere a assinatura antes de publicar `.codemark/manifest.json.sshsig`. A verificação fixa uma chave Ed25519 e o namespace `codemark-manifest-v1`. Chave ou namespace incorretos e manifesto alterado devem falhar.

## OpenPGP

Este backend opcional precisa de `gpg` para assinar e `gpgv` para verificar. Use o fingerprint completo de uma chave existente e um keyring público exportado dedicado.

```sh
python3 codemark.pyz sign /projeto --key SEU_FINGERPRINT_COMPLETO
gpg --export SEU_FINGERPRINT_COMPLETO > owner-public.gpg
python3 codemark.pyz verify /projeto --require-signature --keyring /confiavel/owner-public.gpg --fingerprint SEU_FINGERPRINT_COMPLETO
```

Use `--require-signature`, `--keyring` e `--fingerprint` juntos. Não combine opções GPG com OpenSSH. CodeMark não cria chaves nem recebe senhas por argumento.

`gpgv` confia no keyring indicado e não descobre revogações online. O operador gerencia chaves confiáveis, rotação, revogação, política de expiração e procedência do executável de verificação.

## Preservar a referência

Guarde uma cópia confiável independente do manifesto, assinatura, chave pública e fingerprint fixado. Uma chave pública fornecida pela mesma contribuição não confiável que você analisa não constitui referência confiável.

Depois de uma mudança intencional: revise os fontes, atualize o manifesto com `mark --apply`, execute os testes do projeto e assine novamente. Não atualize a referência automaticamente antes de verificar no CI.

Consulte [Validação](validation.md) para a cobertura medida de backends e plataformas.
