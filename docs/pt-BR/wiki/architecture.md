# Arquitetura

SecOps Codemark separa comentários, inventário completo, atestação criptográfica, orquestração e exportação privada opcional. O Python básico usa biblioteca padrão. OpenSSL e Zupt nativos realizam suas operações criptográficas opcionais.

## Componentes e limites

| Componente | Responsabilidade |
| --- | --- |
| `codemark/core.py` | Fontes, comentários, manifestos legados, alterações limitadas e rollback |
| `codemark/integrity.py` | SHA-256/SHA-512 em blocos de regulares e comparação |
| `codemark/pq_signing.py` | Registros canônicos, ML-DSA-87/Ed25519 no OpenSSL e verificação da cadeia |
| `codemark/fingerprint.py` | Sketches normalizados de tokens e similaridade |
| `codemark/cli.py` | Argumentos, relatórios, seleção de modos e códigos de saída |
| `codemark/ssh_signing.py` | Assinatura legada OpenSSH do manifesto de fontes |
| `codemark/signing.py` | Assinatura legada OpenPGP do manifesto de fontes |
| Comando bundle | Exportação explícita de regulares criptografada por destinatário Zupt |
| `codemark/selftest.py` | Fixtures temporárias e ausências explícitas |
| `codemark/gui.py` | Fluxo opcional Tkinter de comentários |

## Fluxo de integridade

```text
Árvore estável selecionada
  -> hashes em blocos dos regulares e exclusões explícitas
  -> bytes exatos de integrity.json
  -> registro canônico com os dois digests do snapshot
  -> assinaturas obrigatórias ML-DSA-87 e Ed25519
  -> histórico encadeado attestations.json

Árvore atual + snapshot + histórico
  + dois fingerprints independentes confiáveis
  + checkpoint esperado mais recente opcional e independente
  -> relatório de integridade e autenticação
```

`verify` escolhe o snapshot quando presente e pode conferir integridade sem autenticação se não houver chaves fixadas. `audit` exige snapshot, histórico e dois fingerprints. Assinaturas legadas do manifesto de fontes não autenticam o snapshot completo.

## Outros fluxos

A marcação insere comentários removíveis somente em formatos de fontes próprios cobertos. A comparação lê fontes como dados e produz candidatos; não os executa. O autoteste só executa suas fixtures.

Bundles privados exportam a árvore de regulares pelo Zupt, incluindo VCS e `.codemark`. Têm destinatário e destino explícitos e são separados da distribuição pública sem criptografia.

## Confiança local

O operador controla host, árvore estável, verificador, chaves privadas, fingerprints, destinatário e checkpoint esperado. Horários locais não criam autoridade externa de timestamp. Veja [Criptografia](cryptography.md) e [Segurança](../security.md).

O site é HTML/CSS/SVG pré-gerado, sem JavaScript, analytics, fontes remotas ou backend de aplicação hospedado.
