# Exemplo de verificação de release

[Guia de integração](../../docs/pt-BR/integration.md) · [English](README.md)

`verify-release.sh` verifica todos os arquivos inventariados, as duas assinaturas com chaves fixadas e o checkpoint mais recente armazenado de forma independente. Falha diante de arquivos alterados, configurações ausentes, assinaturas inválidas ou checkpoint antigo. O relatório é um arquivo novo, privado e externo à árvore verificada.

Requisitos: Python 3.10+, `codemark.pyz` com SHA-256 verificado, OpenSSL 3.5+ com ML-DSA-87 e Ed25519, uma árvore preparada e seis variáveis de ambiente. O verificador não precisa de chave privada. Obtenha ambos os fingerprints e o checkpoint de um canal confiável separado do release recebido.

O workflow de exemplo é manual. Acrescente sua etapa de obtenção dos artefatos e a verificação do checksum do portátil; ele não instala ferramentas nem baixa arquivos. A disponibilidade do provedor varia entre executores: consulte `doctor --json`; `audit` falha quando falta criptografia obrigatória.

Prepare o release em uma etapa confiável separada: execute `snapshot --apply` e `sign --pq-key ... --classical-key ...`, com chaves fora da árvore. Preserve o novo checkpoint independentemente. Não substitua o snapshot para fazer uma verificação falha passar sem revisar as mudanças.

`measure.py` mede execuções temporárias com chaves descartáveis e inclui testes de adulteração, mudança intencional e checkpoint antigo. A medição registra comandos, configurações e tempo de execução; não representa tempo humano de implantação ou manutenção de longo prazo.
