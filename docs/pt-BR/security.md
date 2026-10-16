# Modelo de segurança

SecOps Codemark oferece referências de integridade, autenticação híbrida, atestações locais encadeadas, exportações criptografadas opcionais e comentários removíveis. Cada operação tem cobertura e limite de confiança próprios.

## O que cada camada oferece

| Camada | Oferece | Limite |
| --- | --- | --- |
| Snapshot SHA-256 + SHA-512 | Divergências de bytes e modos contra referência | Referência local sem assinatura também pode ser substituída |
| Atestações ML-DSA-87 + Ed25519 | Duas assinaturas e identidades recentes fixadas independentemente | Sem horário confiável, titularidade jurídica ou revogação automática |
| Histórico canônico encadeado | Consistência de assinaturas, sequência, identidade e vínculos | Histórico antigo válido exige checkpoint esperado independente para rejeitar rollback |
| Bundle Zupt criptografado | Exportação privada explícita ML-KEM-768 + X25519 | Destinatário lê o conteúdo; perder a chave pode impedir recuperação |
| Comentário e sketch de fonte | Identificadores removíveis e candidatos de cópia | Marcas forjáveis, falsos positivos e negativos |

Hash e assinatura não ocultam conteúdo. Confidencialidade precisa da operação explícita de bundle criptografado. Fontes públicos continuam sem criptografia. Código público pode ser estudado e copiado sob sua licença.

## Confiança independente

A autenticação híbrida exige os dois fingerprints públicos completos confiáveis. Chaves embutidas não estabelecem confiança. Guarde o checkpoint mais recente esperado fora da árvore controlada pela parte analisada para detectar substituição por histórico antigo válido. Horário local não é timestamp confiável.

O operador gerencia origem, comprometimento, rotação, política de revogação, arquivos de confiança e executável de verificação. Não há serviço online de identidade, revogação, timestamp ou transparência. A aplicação não recupera as premissas de uma chave privada ou host comprometido.

## Limite do filesystem

Use árvore local estável. O snapshot recusa links, arquivos especiais, metadados malformados, races detectadas e violações de tetos. Exclui componentes `.codemark`, `.git`, `.hg` e `.svn`, com motivos. Outros arquivos regulares entram independentemente do formato.

Detectar mudanças simultâneas não garante proteção contra kernel malicioso, races deliberadamente hostis ou conta local comprometida. O snapshot cobre arquivos, não diretórios vazios, imagem completa de filesystem ou backup automático.

Comentários legados têm exclusões, formatos e tetos menores próprios, com rollback por arquivo. Encerramento forçado e queda de energia podem deixar estado parcial. Preserve commit ou backup recuperável e só remova trava remanescente após confirmar que não há operação ativa.

## Privacidade de exportações e metadados

A CLI funciona localmente e não envia o projeto. Não é scanner de segredos. Snapshot e atestação podem revelar caminhos, hashes, identidade, fingerprints e horários locais.

O bundle privado inclui regulares da árvore escolhida, inclusive histórico de versionamento e `.codemark`. Revise o escopo, mantenha segredos e chaves privadas fora da raiz e compartilhe apenas com destinatários pretendidos. Criptografia não torna privado um repositório público nem oculta cópias existentes.

## Escopo criptográfico

A assinatura híbrida usa provider padrão do OpenSSL 3.5; bundles delegam ao Zupt seu formato de destinatário. SecOps Codemark não afirma certificação FIPS 140, prova formal de seu Python, isolamento de host, proteção pós-quântica universal ou benchmark ausente da evidência.

Consulte a [wiki de criptografia](wiki/cryptography.md) e [Validação](validation.md) para versões reais, casos negativos exercitados e limites de plataformas.

## Relatar vulnerabilidade

Siga a [política de segurança](../../SECURITY.md). Use reproducer sintético e não publique credenciais, chaves privadas, fontes privados ou dados pessoais.
