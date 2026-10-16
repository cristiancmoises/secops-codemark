# Integrar ao lançamento

SecOps Codemark é uma CLI local. Proteja o verificador, dois fingerprints, checkpoint esperado e configuração de CI contra a contribuição não confiável em análise.

## Preparar a referência

1. Escolha a revisão pretendida e execute os testes do projeto.
2. Se desejar comentários, marque apenas módulo próprio e teste novamente.
3. Pare escritores simultâneos, confira a prévia do snapshot e suas exclusões.
4. Aplique o snapshot e confira escopo e digests relatados.
5. Assine com as duas chaves híbridas existentes fora do projeto.
6. Preserve bytes exatos do snapshot, histórico, dois fingerprints independentes e checkpoint mais recente num registro confiável.

Conclua as edições antes de inventariar a referência que será assinada. Assinar manifesto local editável sem conferir seus fontes não é revisão.

## Verificar no CI

```sh
python3 /confiavel/codemark.pyz audit /checkout --pq-fingerprint 'SHA256:SEU_FINGERPRINT_MLDSA87' --classical-fingerprint 'SHA256:SEU_FINGERPRINT_ED25519' --checkpoint SEU_CHECKPOINT_SHA512_COMPLETO_MINUSCULO --json
```

Use o checkpoint completo esperado de registro confiável. Faça checkout da revisão exata e interprete autenticação e integridade atual. Não atualize snapshot nem rode `mark --apply` antes da verificação: isso aceitaria mudanças atuais como referência.

Jobs Windows usam `py -3`, caminhos nativos entre aspas e ferramentas externas compatíveis instaladas. Disponibilidade de plataforma e provider são evidências separadas, não implicadas por sucesso Linux. Veja [Validação](validation.md).

## Exemplo reutilizável de pipeline

O repositório inclui uma [etapa shell de verificação](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.0/examples/pipeline/verify-release.sh), um [workflow manual GitHub Actions](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.0/examples/pipeline/verify-release.yml) e [orientação de configuração](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.0/examples/pipeline/README.md).

A etapa exige seis valores protegidos: `CODEMARK_PYZ`, `RELEASE_DIR`, `PQ_FINGERPRINT`, `CLASSICAL_FINGERPRINT`, `CHECKPOINT` e `AUDIT_REPORT`. Forneça portátil com checksum conferido, árvore preparada e OpenSSL 3.5 compatível. Precisa de referências públicas de confiança, não de chave privada.

O workflow é manual e recusa a execução se faltarem entradas ou capacidade criptográfica. Forneça sua etapa confiável de obtenção de artefatos; o exemplo não busca um lançamento nem instala o backend criptográfico. Revise ações fixadas e configuração protegida no seu repositório. Tempo medido da etapa e tamanho da configuração são distintos do tempo humano de implantação ou manutenção.

## Exemplo de integração medido

A [medição reproduzível do pipeline](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.0/examples/pipeline/measure.py) usou três arquivos originais de teste, somando 2.097.184 bytes: um executável sem extensão, JSON e uma imagem binária. Cinco execuções locais usaram Python 3.12.12 e OpenSSL 3.5.7 em um namespace GNU/Linux sem rede. As [amostras brutas e os hashes das ferramentas](../reports/0.4.0/pipeline-results.json) registram a carga e as falhas.

| Etapa | Mediana do tempo total | Faixa observada |
| --- | --- | --- |
| Snapshot | 0,071 s | 0,062–0,095 s |
| Assinatura híbrida | 0,210 s | 0,124–0,262 s |
| Auditoria autenticada | 0,110 s | 0,090–0,161 s |

O exemplo shell real também passou e salvou um relatório correspondente. O experimento rejeitou JSON alterado com código 1, checkpoint antigo após uma mudança intencional com código 2 e ausência de chaves de confiança com código 2. A atualização revisada verificou após criar novo snapshot, assinar e avançar o checkpoint esperado de forma independente.

A etapa de verificação tem **16 linhas shell, 27 linhas de workflow, seis configurações de ambiente obrigatórias e um comando de verificação**. O verificador não guarda chave privada de assinatura. Obter os artefatos, verificar o checksum do portátil, instalar a criptografia e proteger o executor e suas configurações são trabalhos adicionais.

Os tempos incluem inicialização do Python e operações nativas de assinatura sobre uma carga pequena e controlada. As cinco assinaturas estendem o mesmo histórico, aumentando o trabalho das execuções seguintes. Geração de chaves e instalação de dependências ficam fora da medição. Não foram medidos tempo humano de implantação ou manutenção de longo prazo. Use a [planilha de esforço](../reports/0.4.0/integration-effort-template.csv) para registrar essas observações no seu pipeline.

```sh
python3 examples/pipeline/measure.py --codemark dist/codemark.pyz --output /reports/pipeline-NOVO.json --repeats 5
```

## Relatórios

```sh
python3 codemark.pyz verify /checkout --json --output /relatorios/verificacao-NOVA.json
```

Use relatório novo externo às árvores, aguarde o término e registre o código de saída. O exemplo confere integridade sem autenticação; para uma barreira autenticada use audit com dois fingerprints e checkpoint esperado.

## Pacotes públicos e privados

Os lançamentos públicos usam `.zupt` genuíno sem criptografia e checksums SHA-256. Precisam ser testados e extraídos contra a revisão pretendida antes da publicação.

Para exportação confidencial explícita, veja [Bundle criptografado](encryption.md). Essa árvore inclui regulares de diretórios VCS e `.codemark`; confira o conteúdo e mantenha chaves privadas e arquivos de senha fora dela. Pacote privado e fontes públicos têm finalidades diferentes.

A extração pelo Zupt nativo 5.2.10 usa a umask atual em vez de restaurar modos POSIX. Veja [restauração e verificação](encryption.md#restaurar-e-verificar) antes da auditoria; igualdade de bytes não qualifica preservação de ACLs ou modos.

## Responsabilidades de manutenção

| Gatilho | Ação do operador |
| --- | --- |
| Mudanças pretendidas nos arquivos | Revisar, testar o projeto, atualizar snapshot e assinar a referência |
| Lançamento aprovado | Preservar dois fingerprints e checkpoint mais recente exato independentemente |
| Comprometimento ou rotação de chaves | Revisar transições e atualizar política protegida por canal confiável |
| Atualização de OpenSSL ou Zupt | Repetir testes positivos e negativos no ambiente de destino |
| Exportação privada | Conferir árvore, destinatário e bytes restaurados |

Não há servidor de runtime do SecOps Codemark para administrar. Hash da árvore lê os bytes selecionados; assinatura, custódia de chaves, retenção de checkpoints e atualizações ainda exigem manutenção. Tempos ou custos medidos valem para o ambiente e carga publicados, não como estimativa universal.

## GNU Guix e componentes opcionais

A CLI básica usa Python do perfil. Por exemplo:

```sh
guix shell python -- python3 codemark.pyz doctor --json
```

Assinatura híbrida precisa de OpenSSL compatível, assinatura legada das ferramentas correspondentes e bundles de Zupt. São requisitos de ambiente, não afirmação de pacote Guix ou todas as plataformas qualificadas. A GUI opcional precisa de Tkinter e sessão gráfica e atende comentários legados.
