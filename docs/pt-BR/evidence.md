# Evidências e avaliação reproduzível

Em uso nos projetos do mantenedor.

Qualificação atual, exemplos reproduzíveis e comparações de ferramentas registram comandos, versões e limitações. Medições pendentes continuam pendentes; fixtures controladas são separadas do uso em projetos.

## Comparação de similaridade com corpus congelado

A [comparação medida](../reports/0.4.0/similarity-review.md) usa uma referência
Python original, cinco variantes derivadas conhecidas e dois controles escritos
separadamente. Corpus e sensibilidade foram congelados antes das pontuações.
Candidatos nunca herdaram marcas. CodeMark marcou uma cópia temporária da
referência; JPlag 6.3.0 e Copydetect 0.5.0 leram a referência original sem marcas.

| Candidato | CodeMark | JPlag AVG | Copydetect: média das coberturas direcionais |
| --- | --- | --- | --- |
| Cópia exata | 1.0000 | 1.0000 | 1.0000 |
| Identificadores renomeados | 0.9174 | 1.0000 | 1.0000 |
| Formatação/comentários | 0.5633 | 0.9937 | 0.9174 |
| Funções reordenadas | 0.9703 | 1.0000 | 0.9978 |
| Cópia parcial conhecida | 0.3426 | 0.4361 | 0.4353 |
| Controle do mesmo domínio | 0.0767 | 0.0000 | 0.0000 |
| Controle não relacionado | 0.0559 | 0.0000 | 0.0000 |

As ferramentas medem coisas diferentes. No valor ilustrativo 0,65, os três
resumos perdem a cópia parcial conhecida; CodeMark também perde a variante de
formatação/aspas. Os dois controles ficam abaixo desse valor. Isso não é regra
calibrada nem padrão de todas as ferramentas. Pontuações direcionais completas
e padrões nativos estão nos [resultados brutos](../reports/0.4.0/similarity-results.json).

CodeMark e Copydetect concluíram duas execuções com pontuações idênticas. JPlag
falhou duas vezes por alocação nativa no limite de endereçamento de 2 GiB, depois
concluiu uma tentativa com SerialGC e heap inicial de 32 MiB. Limite, binário,
corpus e sensibilidade permaneceram iguais. Falhas e logs foram preservados;
a repetibilidade de JPlag ainda não foi medida. A consulta de versão bloqueada
e o início da JVM entram no tempo. Cargas diferentes e este corpus pequeno não
sustentam vencedor de velocidade, ranking geral ou prova de plágio.

O pacote de fontes inclui executor reproduzível, manifesto do corpus, hashes das
dependências e instruções em `examples/evaluation/`. Aceita ferramentas existentes
e não baixa nem instala pacotes. A comparação cobre fixtures Python no ambiente
GNU/Linux registrado, não todas as linguagens ou plataformas cobertas.

Veja [Validação](validation.md) para registros da versão e [Integração](integration.md) para o fluxo operacional.
