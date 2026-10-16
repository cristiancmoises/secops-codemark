# Resolver problemas

## A árvore está íntegra, mas não autenticada

Sem dois fingerprints híbridos, a verificação confere apenas a referência local. Use `audit` com fingerprints completos ML-DSA-87 e Ed25519 confiáveis por canal independente. Chave embutida não é referência independente.

## A integridade retorna 1

Leia arquivos alterados, ausentes, novos e modos alterados no JSON. Compare com a revisão pretendida. Revise mudanças legítimas antes de gerar e assinar snapshot; preserve evidências se forem inesperadas.

## Uma cadeia válida falha no checkpoint

O checkpoint esperado identifica o último registro exato, não qualquer ancestral. A divergência pode indicar rollback, substituição ou registro novo legítimo ainda não aprovado na referência confiável. Investigue e atualize o checkpoint apenas após revisão. Não remova a verificação para fazer uma falha inexplicada passar.

## O OpenSSL não assina

Confira `doctor --json` e a versão nativa do OpenSSL. O modo híbrido exige OpenSSL 3.5 com provider padrão e PEM ML-DSA-87 e Ed25519. Uma chave privada OpenSSH usa formato diferente.

A assinatura não é interativa. Chaves criptografadas exigem a mesma senha num `--passphrase-file` protegido. Arquivos ausentes, incorretos ou alterados falham; nenhum backend mais fraco é substituído automaticamente.

## Opções legadas são recusadas

Se `integrity.json` existe, `verify` usa todos os arquivos. Opções legadas GPG/OpenSSH autenticam só `manifest.json` da marcação. Escolha fluxo e referência apropriados; uma assinatura de fontes não autentica binários e outros dados do snapshot.

## Um arquivo é ignorado ou recusado

Na marcação, leia `skipped`, formato, encoding, prologue, dependências e tetos. No snapshot, leia `excluded` e os limites próprios. Links, especiais e races detectadas são recusados em vez de incluídos silenciosamente.

## O bundle falha no destinatário

Calcule o hash do arquivo público Zupt inteiro e confira o fingerprint completo por canal confiável. Ele é diferente do DER SPKI da assinatura. Mantenha privadas fora da árvore e use destino novo externo. Veja [Criptografia](../encryption.md).

## O relatório não pode ser gravado

`--output` precisa de arquivo novo em pasta existente e gravável, externa às árvores. Espere o término antes de consumir. Preserve evidências anteriores e confira permissões e espaço.

## Uma trava permaneceu

Confirme que não há operação ativa antes de remover `.codemark/lock`. Compare árvore com Git ou backup após interrupção forçada. Rollback comum não recupera queda de energia.

## Pedir ajuda

Informe versões, plataforma, comando, código de saída e reproducer sintético. Oculte caminhos privados e nunca anexe chaves secretas ou senha. Use a [política de segurança](../../../SECURITY.md) para falhas sensíveis.
