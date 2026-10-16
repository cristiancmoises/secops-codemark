# Resolver problemas

## A verificação retorna 1

Leia `changed`, `missing`, `untracked` e `invalid_marks` no relatório JSON. Compare com a revisão pretendida. Se as mudanças forem legítimas, revise antes de gerar e assinar uma referência. Preserve a evidência anterior se forem inesperadas.

## A comparação retorna 1

O código 1 indica candidatos encontrados. Leia o método e inspecione os arquivos. Boilerplate compartilhado e código independente podem produzir candidatos enganosos. O código de saída não conclui plágio.

## Um arquivo não foi marcado

Leia `skipped` com `--json`. Confira extensão, encoding, tamanho, prologue, caminho de dependência e formato assinado. Escolha um módulo próprio menor se a operação chegar ao teto de recursos.

## O relatório não pode ser gravado

`--output` precisa de arquivo novo em diretório existente e gravável, externo às árvores. Nunca sobrescreve relatório existente. Espere o processo terminar antes de consumir a saída. Confira espaço e permissões sem apagar evidências anteriores.

## A assinatura não confere

Confira fingerprint completo, origem da chave pública, manifesto atual e backend. OpenSSH exige Ed25519 e namespace esperado. GPG exige três opções juntas: `--require-signature`, `--keyring` e `--fingerprint`.

Atualizar legitimamente o manifesto invalida a assinatura anterior. Assine a nova referência revisada. Não substitua a chave confiável apenas para fazer uma verificação passar.

## Uma trava permaneceu

Confirme que nenhuma operação CodeMark está ativa antes de remover `.codemark/lock`. Confira a árvore contra Git ou backup após uma interrupção forçada. Rollback comum não oferece recuperação de queda de energia.

## GUI ou ferramenta opcional indisponível

Execute `doctor --json`. A GUI precisa de Tkinter e sessão gráfica. OpenSSH precisa de `ssh-keygen` com `-Y`; GPG precisa dos executáveis e agente local funcional. A CLI funciona sem GUI. Um `skip` registra cobertura ausente.

## Pedir ajuda

Informe versões de CodeMark e Python, sistema operacional, comando exato, código de saída e um reproducer sintético pequeno. Oculte caminhos privados. Use a [política de segurança](../../../SECURITY.md) para falhas sensíveis.
