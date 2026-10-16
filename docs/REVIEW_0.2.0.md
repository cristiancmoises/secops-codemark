# Revisão independente: CodeMark 0.2.0

Veredito após correções: **adequado para produção no escopo CLI em GNU/Linux,
com assinatura OpenSSH Ed25519 opcional**. Revisão por um agente independente;
não representa auditoria externa ou certificação de segurança.

## Escopo

Baseline 0.1.0, commit `5f758f9`, até a implementação da 0.2.0.
A revisão inicial examinou `218d1a6`; as correções foram reavaliadas no
worktree posteriormente registrado como `72801ad`.

Foram examinados limites, efeitos de falhas de relatórios, vínculo entre
manifesto e assinatura, pinagem da chave/namespace, isolamento do autoteste,
empacotamento e integração da CLI. Nenhum achado crítico foi identificado.

## Achados e resolução

1. **Importante, corrigido:** falha tardia ao gravar o relatório podia deixar
   fontes marcados com retorno 2. Agora a serialização, escrita, flush, fsync
   e fechamento do relatório terminam antes da primeira alteração persistente
   de fontes, manifesto ou assinatura. A operação elimina o relatório se a
   transação do projeto falhar.
2. **Importante, corrigido:** close podia falhar novamente após flush e impedir
   a remoção de um relatório truncado. A limpeza agora executa mesmo nesse caso,
   preservando a falha original.

## Revalidação independente

- Suíte completa: 71 testes; zero falhas e erros; classe GPG suspensa porque
  o ambiente não permite sockets do agente.
- 13 testes reais de OpenSSH, com chaves efêmeras e verificações negativas.
- Probes reais com `RLIMIT_FSIZE=2048`, `SIGXFSZ` ignorado, 25 e 60 arquivos
  não suportados: retorno 2, fontes preservados, manifesto ausente e relatório
  removido. Casos cobrem escrita e flush com buffering.
- Falha ao desmarcar preserva os fontes marcados e o manifesto.
- Falha de relatório ao assinar não publica assinatura.
- Falha ao gravar o projeto após concluir o relatório reverte fontes e remove
  o relatório.

Re-revisão: os dois achados foram resolvidos, sem bloqueadores adicionais
identificados no ajuste.

## Limites da aprovação

Não cobre renderização da GUI, Windows, GNU Guix como plataforma completa,
GPG, queda de energia, encerramento forçado, filesystem local hostil,
comprovação jurídica ou detecção universal de cópias. Não houve execução do
REA nem publicação externa. Consulte `VALIDATION.md`, `QUALIFICATION.json`
e `PRODUCTION.md`.
