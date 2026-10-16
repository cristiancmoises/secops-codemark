# Rastreabilidade e checkpoints confiáveis

A assinatura híbrida vincula atestações autenticadas ao snapshot de integridade salvo. O histórico registra identidade do projeto, sequência, SHA-512 do registro canônico anterior, SHA-256 e SHA-512 do snapshot, fingerprints, horário local e versão da ferramenta.

## Criar o próximo registro

Crie e revise o snapshot antes de assinar:

```sh
python3 codemark.pyz snapshot /projeto --apply --json
python3 codemark.pyz sign /projeto --pq-key /fora/chaves/mldsa87.pem --classical-key /fora/chaves/ed25519.pem --json
```

Os registros ficam em `.codemark/attestations.json`. As assinaturas ML-DSA-87 e Ed25519 precisam ser válidas. Elas cobrem um payload canônico que vincula os hashes dos bytes exatos de `.codemark/integrity.json`. A verificação não executa os fontes.

## Fixar as duas identidades

```sh
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --json
```

Substitua os dois exemplos pelos fingerprints completos e confiáveis por referência independente. Chaves embutidas na atestação são evidência a conferir, não origem de confiança por si mesmas. O registro mais recente precisa coincidir com as duas chaves fixadas. A auditoria confere assinaturas, sequência, identidade e vínculos com registros anteriores.

Assinaturas históricas são verificadas, mas uma chave antiga não se torna independentemente confiável apenas por estar na cadeia. Leia `historical_key_continuity` e guarde um registro confiável das transições.

## Detectar substituição por histórico antigo válido

Uma cadeia antiga e consistente ainda pode ter assinaturas válidas. Para detectar sua substituição, salve o `checkpoint` retornado por assinatura ou auditoria confiável fora do projeto, num canal protegido da parte cuja árvore será verificada.

```sh
python3 codemark.pyz audit /projeto --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --checkpoint SEU_CHECKPOINT_SHA512_COMPLETO_MINUSCULO --json
```

O checkpoint é o digest SHA-512 hexadecimal completo, com 128 caracteres minúsculos, do registro canônico mais recente. O valor fornecido precisa coincidir exatamente com o registro mais recente esperado. Não é timestamp nem é inferido de um arquivo da árvore não confiável.

Sem um checkpoint esperado preservado independentemente, a verificação não detecta substituição de árvore e histórico inteiros por uma versão antiga válida. Leia `rollback_protected`; assinaturas válidas sozinhas não tornam verdadeira a proteção contra rollback.

## Tempo e titularidade

Os horários vêm do relógio local. Não são timestamp confiável nem prova de publicação, titularidade jurídica ou originalidade. Um registro válido mostra que as chaves privadas correspondentes assinaram a referência vinculada sob a política implementada.

## Retenção e limites

Preserve revisão, bytes exatos do snapshot, histórico de atestações, dois fingerprints confiáveis e checkpoint esperado independentemente. A cadeia tem teto de 1.000 registros e 32 MiB; um registro canônico tem teto de 32 KiB. Planeje arquivamento e transições antes de atingir o teto.

Veja [Assinaturas](signing.md) e o limite de confiança em [Segurança](security.md). Use [bundles criptografados](encryption.md) quando a árvore exportada precisar de confidencialidade.
