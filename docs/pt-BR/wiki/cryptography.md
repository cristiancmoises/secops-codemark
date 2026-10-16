# Criptografia e confiança

SecOps Codemark usa implementações estabelecidas para as operações criptográficas. Sua política exige assinaturas ML-DSA-87 e Ed25519 juntas nas atestações híbridas; bundles privados opcionais delegam ao Zupt a criptografia de destinatário ML-KEM-768 + X25519.

## Funções e chaves diferentes

| Operação | Mecanismo | Referência de confiança |
| --- | --- | --- |
| Inventário | SHA-256 e SHA-512 dos bytes | Referência salva; autenticação é separada |
| Atestação híbrida | ML-DSA-87 e Ed25519, ambas obrigatórias | Dois fingerprints públicos confiáveis independentes |
| Detecção de rollback | Checkpoint SHA-512 exato do último registro | Valor esperado guardado fora da árvore não confiável |
| Exportação privada | Destinatário Zupt ML-KEM-768 + X25519 | Fingerprint confiável independente da chave pública do destinatário |
| Assinatura legada de fontes | OpenSSH Ed25519 ou OpenPGP | Chave fixada confiável do backend |

Não some forças em bits de hashes ou assinaturas para alegar um nível combinado de segurança. Troca de chaves, assinaturas, criptografia e timestamps confiáveis têm funções diferentes.

## Padrões e implementação

[ML-DSA é definido no NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final). [ML-KEM é definido no NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final). São padrões de algoritmos, não certificação deste aplicativo, host ou configuração publicada.

As atestações híbridas usam o [provider padrão do OpenSSL 3.5](https://docs.openssl.org/3.5/man7/OSSL_PROVIDER-default/). SecOps Codemark não afirma validação FIPS 140. Usar um algoritmo cujo padrão contém FIPS no nome não estabelece essa validação.

As evidências precisam identificar as versões reais do OpenSSL e Zupt e os caminhos exercitados. Não deduza correção, resistência a canais laterais, desempenho ou qualificação de plataforma apenas pelo nome do algoritmo.

## O que as assinaturas vinculam

As duas assinaturas cobrem payload canônico com hashes SHA-256 e SHA-512 dos bytes exatos do snapshot, identidade, fingerprints, sequência, horário local e vínculo anterior. Não assinam a apresentação visual do JSON.

O contexto ML-DSA separa este protocolo de outros usos da chave. As chaves embutidas são conferidas contra fingerprints completos independentes. O relatório distingue continuidade histórica de chaves e autenticação do registro mais recente.

## Confiança e recuperação

Mantenha chaves privadas e arquivos de senha fora do projeto escolhido. Faça backup conforme sua política. Preserve separadamente dois fingerprints públicos, revisão aprovada, snapshot, histórico e checkpoint esperado.

Não há serviço online de identidade, revogação, timestamp ou transparência. O operador gerencia comprometimento, rotação, atualização por canal confiável e aceitação de assinaturas antigas. Perder a chave privada do destinatário pode tornar uma exportação irrecuperável.

Leia [Assinaturas](../signing.md), [Rastreabilidade](../traceability.md), [Criptografia](../encryption.md) e [Segurança](../security.md).
