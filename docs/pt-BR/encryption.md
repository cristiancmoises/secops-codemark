# Exportar um bundle privado criptografado

Snapshot, marca, hash e assinatura não ocultam conteúdo. Confidencialidade é uma exportação explícita: `bundle` delega criptografia ao **Zupt nativo 5.2.10+**, usando seu formato híbrido de destinatário ML-KEM-768 + X25519.

Isso é separado da assinatura ML-DSA-87 + Ed25519. Chaves de assinatura autenticam registros; a chave de destinatário controla quem pode descriptografar o arquivo. Não troque um tipo de chave pelo outro.

## Preparar o destinatário

Crie ou use uma chave fora do projeto selecionado. Os comandos nativos do Zupt são:

```sh
zupt keygen -o /fora/chaves/recipient.key
zupt keygen --pub -k /fora/chaves/recipient.key -o /confiavel/recipient.pub
```

Proteja a chave privada do destinatário e mantenha-a fora do projeto e do pacote público. Obtenha chave pública e fingerprint completo por canal independente confiável.

O fingerprint é `SHA256:` seguido de Base64 sem padding do SHA-256 do arquivo `recipient.pub` inteiro. Não é o fingerprint de uma chave de assinatura nem de um corpo PEM decodificado. Calcule sobre dados públicos:

```sh
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /confiavel/recipient.pub
```

## Conferir e criar

```sh
python3 codemark.pyz bundle /projeto --recipient-key /confiavel/recipient.pub --recipient-fingerprint 'SHA256:SEU_FINGERPRINT_DESTINATARIO' --archive /exportacoes/privado.zupt --json
python3 codemark.pyz bundle /projeto --recipient-key /confiavel/recipient.pub --recipient-fingerprint 'SHA256:SEU_FINGERPRINT_DESTINATARIO' --archive /exportacoes/privado.zupt --apply --json
```

A saída é uma exportação privada explícita. Use destino novo e externo ao projeto. Sem `--apply`, confira a prévia antes de criar o pacote.

## Entender o conteúdo

O bundle privado inclui arquivos regulares da árvore escolhida, inclusive metadados `.codemark` e diretórios de controle de versão como `.git`. Não usa as exclusões do snapshot para omiti-los. Um histórico Git pode conter material confidencial antigo mesmo quando o checkout atual parece limpo.

Escolha a raiz e confira a cobertura planejada. Mantenha credenciais, chaves privadas de assinatura e destinatário e arquivos de senha fora dela. Criptografia não autoriza divulgar dados sem relação com a tarefa; o destinatário pode ler o conteúdo após descriptografar. Arquivos externos à árvore não são adicionados intencionalmente.

## Restaurar e verificar

```sh
zupt extract --pq /fora/chaves/recipient.key -o /restauracao/diretorio-novo /exportacoes/privado.zupt
```

A extração pelo Zupt nativo 5.2.10 usa a umask atual e não restaura os modos de permissão POSIX. A qualificação da restauração cobre bytes exatos dos arquivos, não a preservação de ACLs ou modos. Por isso, `audit` pode relatar `mode_changed` até você restaurar os modos esperados a partir de uma referência confiável. Não atualize o snapshot para ocultar essa diferença.

Mantenha a árvore restaurada estável e confira integridade e atestações com os dois fingerprints confiáveis e, quando necessário, checkpoint independente. Descriptografar com sucesso sozinho não comprova identidade jurídica do remetente nem torna atual uma árvore antiga assinada.

## Lançamentos públicos

Os fontes públicos usam `.zupt` genuíno sem criptografia e checksums SHA-256. O comando de bundle serve para exportação privada explícita; não criptografa lançamentos públicos silenciosamente.

A evidência da versão informa versão do Zupt, ambiente, falhas e restauração exercitados. Nomes de algoritmos não constituem certificação FIPS 140. Consulte a [wiki de criptografia](wiki/cryptography.md).
