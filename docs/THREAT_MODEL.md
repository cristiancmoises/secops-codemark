# Modelo de ameaças

## O que se pretende proteger

O vínculo entre um projeto, uma identidade declarada e uma versão específica
dos fontes. CodeMark registra esse vínculo por comentários e manifestos. Uma
assinatura opcional torna adulterações na referência verificáveis contra uma
chave pública fixada. O usuário precisa preservar a chave privada.

## O que cada camada oferece

| Camada | Utilidade | Limite |
|---|---|---|
| Comentário identificador | Reconhecer arquivo e projeto, mesmo renomeados | Pode ser removido ou forjado |
| SHA-256 dos fontes | Detectar alterações contra a referência | Manifesto local também pode ser editado |
| Assinatura OpenSSH Ed25519 ou OpenPGP | Autenticar a referência com a chave fixada | Não comprova data, titularidade ou originalidade |
| Tokens normalizados | Localizar candidatos sem marca e com nomes alterados | Falsos positivos e falsos negativos; comparação por arquivo |

Nenhuma camada torna código público secreto. Não há marca invisível,
anti-debugging, controle de licença em runtime, telemetria, dependência de IA
ou execução dos arquivos suspeitos.

## Relação com REA

O README oficial do REA descreve inspeção de binários, JavaScript/Electron,
.NET, Android, sites, símbolos, strings, source maps e comportamento. Essas
operações não são bloqueadas por um comentário no fonte. CodeMark atua sobre
procedência e rastreamento de cópias de fontes, não como um bloqueador do REA.

Não foi instalado nem executado REA nesta entrega; não há benchmark contra
REA ou modelos de IA. Testes de cópia usam fixtures controladas.

O backend SSH fixa uma chave Ed25519 pelo fingerprint SHA256 completo e usa
o namespace `codemark-manifest-v1`. O manifesto é verificado contra a árvore
antes de assinar; dados assinados e verificados são congelados. A chave privada
fica fora do projeto. A confiança, rotação e revogação são geridas pelo operador.

## Direitos sobre software livre

GPL permite estudar, modificar e redistribuir sob seus termos. Ela define
fonte como a forma preferida para modificação; ofuscar não substitui as
obrigações de disponibilizar o fonte correspondente quando aplicáveis.
Uma marca CodeMark não cria condições adicionais nem proíbe sua remoção.
Avisos de copyright/licenças existentes são preservados.

Copyleft ajuda a exigir o cumprimento da licença de cópias distribuídas;
não impede implementação independente de ideias ou estudo do funcionamento.
Os relatórios não decidem questões jurídicas.

## Como preservar evidências úteis

1. Marque apenas código próprio; mantenha dependências e fontes de terceiros fora.
2. Execute testes do seu projeto e registre o manifesto na versão de lançamento.
3. Assine com chave existente; publique a chave/fingerprint por canal confiável.
4. Mantenha cópia independente do manifesto e assinatura, e histórico de commits.
5. Ao comparar suspeitas, confira manualmente os trechos e suas licenças.

Uma pessoa pode reconstruir o algoritmo sem copiar tokens; pode misturar ou
dividir arquivos; pode usar o mesmo boilerplate sem ter copiado o projeto.
Arquivos pequenos não recebem pontuação aproximada: são necessários ao menos
40 tokens e 8 fingerprints. Strings e números são mantidos nos tokens.
Cada sketch guarda até 256 hashes de grupos de 5 tokens; Jaccard é calculado
sobre esses sketches, não sobre uma porcentagem literal de linhas copiadas.

## Ameaças fora do escopo

Máquina/usuário local hostil, kernel comprometido, races deliberadas no
filesystem, chave privada roubada, acesso ao servidor, cópia de binários,
ataques a IA, ofuscação robusta e prova temporal reconhecida por terceiros.
As gravações são atômicas por arquivo com rollback em erros comuns; queda de
energia ou encerramento forçado durante operação pode deixar estado parcial.
Uma trava que sobrar deve ser removida apenas após confirmar que não há uma
operação ativa. Não altera `.gitignore` nem instala hooks automaticamente.

## Referências primárias consultadas

- REA: https://github.com/morluto/rea
- GPLv3: https://www.gnu.org/licenses/gpl-3.0.en.html
- SPDX GPL-3.0-or-later: https://spdx.org/licenses/GPL-3.0-or-later.html
- GnuPG: https://www.gnupg.org/documentation/manuals/gnupg/gpgv.html

- OpenSSH ssh-keygen/SSHSIG: https://man.openbsd.org/ssh-keygen
