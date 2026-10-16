# Revisão histórica da versão 0.1.0

Registro da primeira entrega. Para a versão atual, consulte PRODUCTION.md.

Uma revisão independente do código identificou sete achados importantes.
Todos receberam correção e testes de regressão antes do pacote final.

| Achado | Correção e evidência |
|---|---|
| XML na mesma linha e encoding sem newline | Posição de inserção e remoção compartilhada; XML reversível; cabeçalho isolado sem newline é ignorado e reportado |
| Marca completa dentro de string era removida | Leitura/remoção limitada ao slot do cabeçalho; conteúdo interno permanece intacto |
| Cookie lexical do Emacs deslocado | Prologues preservados, com regressão também para Ruby e CSS |
| Saída podia ultrapassar limites de leitura | Orçamento de marca separado; metadados até 64 MiB; preflight de tamanhos e teste com 5.000 registros |
| Seleção da GUI podia ler metadados através de link | `checked_root` executado antes de ler o titular |
| Fechar a janela podia interromper transação | Worker não daemon; fechamento aguarda conclusão; teste real em subprocesso |
| Trava era adquirida depois do snapshot | Identidade e fontes lidos sob trava nas operações de escrita; interleaving concorrente testado |

As onze regressões falharam contra a versão anterior e passaram após as
correções. A suíte final executou 42 testes sem falhas; uma classe de assinatura
GPG foi suspensa devido ao bloqueio de sockets do agente neste ambiente.
Não houve segunda revisão independente; as correções foram verificadas por
regressões e pela suíte completa. Não há achados menores adiados.

## Limites de escopo preservados

Estas situações foram avaliadas e permanecem fora do escopo já documentado:

| Situação | Decisão | Custo se a premissa não servir ao uso pretendido |
|---|---|---|
| Filesystem local deliberadamente hostil | Recusar links observados; não prometer resistência a races de usuário/kernel hostil | Seria preciso isolamento e acesso por handles mais restritivo |
| Editores/builds concorrentes | Exigir árvore estável; serializar operações do próprio CodeMark | Alterações externas durante gravação podem conflitar |
| Kill forçado, falta de energia | Rollback de erros comuns, sem prometer crash recovery | Pode restar estado parcial; usar Git/backups |
| Remoção/forja deliberada da marca | Documentar removibilidade; usar referência assinada quando apropriado | A marca visível isolada não é uma defesa forte |
| Prova legal de autoria | Relatórios são indícios técnicos, sem veredito jurídico | É necessária avaliação externa e evidência adicional |
| Similaridade semântica universal | Heurística por arquivo com tokens conservadores | Reescritas e boilerplate podem gerar erros |
| Plataformas/toolchains indisponíveis | Não alegar execução em Windows/Guix, nem GUI visual/GPG completos | A validação deve ser feita nesses ambientes antes de depender dessas funções |

GPGv valida assinaturas contra o keyring indicado e o fingerprint fixado.
Segundo seu manual oficial, assume que as chaves desse keyring são confiáveis
e não verifica expiração ou revogação. A referência de confiança deve ser
mantida pelo usuário; não há busca de chaves ou consultas online.

## Veredito

Primeira versão funcional para uso local de marcação, integridade e comparação
de fontes. A CLI e o pacote portátil foram validados no ambiente disponível.
GUI visual e assinatura GPG completa continuam pendentes em host com esses
recursos. A ferramenta não bloqueia REA nem torna código aberto secreto.
