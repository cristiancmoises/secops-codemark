# Modelo de segurança

CodeMark registra uma relação entre árvore de fontes, identidade declarada e referência de conteúdo. É uma ferramenta de procedência e integridade, com triagem heurística de possíveis cópias.

## O significado de cada camada

| Camada | Oferece | Limite |
| --- | --- | --- |
| Comentário de procedência | Identificadores de projeto e arquivo que sobrevivem a renomeações | Removível e forjável |
| Manifesto SHA-256 | Divergências contra a referência guardada | Um manifesto local sem assinatura também pode ser editado |
| Assinatura com chave fixada | Autenticação do manifesto contra uma chave | Sem prova jurídica, data confiável ou originalidade |
| Sketch de tokens normalizados | Candidatos após mudanças de alguns nomes e comentários | Falsos positivos e negativos; aproximação por arquivo |

Código público continua disponível para estudo e cópia sob sua licença. Um comentário não bloqueia engenharia reversa, descompilação ou implementação independente. Licenças e avisos de copyright existentes continuam aplicáveis.

## Limite operacional

Trabalhe numa árvore local estável, sem editores ou builds escrevendo ao mesmo tempo. Links simbólicos no caminho ou árvore, arquivos especiais, metadados malformados e violações de limites são recusados. Diretórios conhecidos de dependências e builds são excluídos sem travessia.

As operações usam substituição por arquivo e rollback em erros comuns. Encerramento forçado ou queda de energia podem deixar estado parcial. Guarde commit ou backup recuperável. Remova `.codemark/lock` remanescente apenas após confirmar que não existe operação ativa.

Filesystem e conta local são confiáveis. Kernel hostil, races deliberadas, chave roubada, CI comprometido e executável de verificação substituído ficam fora desse limite.

## Privacidade e chaves

A CLI não envia fontes, chama modelo de IA ou exige rede. Não é um scanner de segredos. Um manifesto pode revelar caminhos relativos, titular declarado e fingerprints de conteúdo; revise os metadados antes de compartilhar.

Use chaves existentes e mantenha os arquivos privados fora do projeto. CodeMark delega assinaturas aos recursos locais do OpenSSH ou GnuPG. Gerencie rotação e revogação separadamente; nenhum serviço online de revogação é consultado.

## Interpretar uma correspondência

Uma correspondência é um ponto de partida para inspeção. Boilerplate comum pode coincidir. Código reescrito, dividido, combinado ou implementado independentemente pode não coincidir. A pontuação não constitui conclusão jurídica nem fração literal de fonte copiado.

## Relatar vulnerabilidade

Siga a [política de segurança](../../SECURITY.md). Não inclua chaves privadas, credenciais, fontes privados ou dados pessoais de terceiros em relatos públicos.

A página de [evidências](validation.md) distingue verificações atuais de registros históricos. Nenhum registro de auditoria garante a ausência de defeitos.
