# Synthetic similarity comparison: CodeMark, JPlag and Copydetect

Recorded on 2026-10-16 UTC with SecOps Codemark 0.4.0, JPlag 6.3.0,
Copydetect 0.5.0, Python 3.12.12 and OpenJDK 25.0.2 on GNU/Linux x86_64.
The [complete results](similarity-results.json) retain tool output, exits, native
exports, errors, settings, dependency hashes, runtime source hashes and timings.
All measured CodeMark runtime bytes match candidate commit
`71ee186b5e1c0c92f5a99b3062f57c6709943f17`; the fixture manifest separately identifies
the experiment inputs. Later platform corrections and a final release revision
need their own qualification and are not silently attributed these scores.

## Frozen inputs and method

One original Python order ledger was compared with seven candidates: exact copy,
identifier renaming, formatting/comments, whole-function reordering, partial
overlap, and two separately written controls. One control addresses the same
broad order domain; the other implements maze search. The partial copy retains
the original shipping-allocation function and adds an unrelated new function.
These construction labels describe known fixture provenance, not legal findings.

The corpus, labels and matching settings were frozen before the first scores at
2026-10-16T03:36:29Z. The manifest SHA-256 is
`56d027dc2a3d6972511ac9e63eab6b15ecaabd45b8b21e29e4fc4d038c835750`.
All eight Python files exceed CodeMark's 40-token/eight-sketch comparison floor.
Python was selected because all three tools support it; this experiment does not
qualify other languages. No corpus or matching sensitivity was changed after
observing results.

CodeMark marked only a temporary reference copy. Candidate sources never received
watermarks. JPlag and Copydetect read the original unmarked reference. CodeMark's
report threshold was `1e-9`; an absent candidate would remain absent, without an
invented zero. Its lexical defaults retain literal spelling, normalize names,
and use five-token shingles with at most 256 hashes. JPlag used its native Python
minimum match of 12 tokens, report threshold 0.0, and default matching options.
Copydetect used Pygments filtering with native noise/guarantee thresholds of 25
filtered characters and display threshold 0.33. Its raw directional matrix was
read without applying the HTML display filter.

## Observed scores

| Candidate | Known fixture label | CodeMark | JPlag AVG | Copydetect mean coverage |
| --- | --- | --- | --- | --- |
| Exact copy | Derived copy | 1.0000 | 1.0000 | 1.0000 |
| Identifier rename | Derived copy | 0.9174 | 1.0000 | 1.0000 |
| Formatting/comments | Derived copy | 0.5633 | 0.9937 | 0.9174 |
| Function reorder | Derived copy | 0.9703 | 1.0000 | 0.9978 |
| Partial overlap | Derived partial copy | 0.3426 | 0.4361 | 0.4353 |
| Same-domain control | Independent control | 0.0767 | 0.0000 | 0.0000 |
| Unrelated control | Independent control | 0.0559 | 0.0000 | 0.0000 |

These are different measurements. CodeMark reports bounded sketch Jaccard or an
exact-content match. JPlag reports structural token similarity. Copydetect's two
directional coverage fractions are retained in full; the displayed mean is an
explicit arithmetic summary. For the partial fixture those fractions are 0.55
of the candidate and approximately 0.3206 of the reference, not copied-line
percentages.

At the predeclared illustrative value 0.65, CodeMark includes three of five known
derived cases; JPlag AVG and the Copydetect mean each include four. All three
exclude both controls at that value. The partial known copy falls below it for
all three summaries. CodeMark also falls below it for the formatting/quote-layout
variant. These misses remain in the record. This shared observation is not a
calibrated decision rule or the default for every tool. In particular,
Copydetect's native display rule uses candidate coverage and its own threshold,
not the mean or 0.65.

## Runs, failures and resource correction

Two initial attempts were made per tool in a network-disabled namespace with a
clean temporary home, read-only source/tools, a 2 GiB address-space cap and a
60-second subprocess timeout. CodeMark and Copydetect completed twice with
identical scores. Both initial JPlag attempts exited 1 during parsing with native
allocation failures. Their complete stdout/stderr and native error logs remain
in the JSON; failed attempts have no invented scores.

A third JPlag attempt added only `-XX:+UseSerialGC -Xms32m` to the original bounded
heap/code-cache/class-space options. The same 2 GiB cap, frozen corpus and matching
settings were retained. It exited 0 and produced the scores above. JPlag therefore
has one successful scored run; repeat stability was not established for it.
The binary was not changed. Its version-update probe was blocked by the network
namespace and is retained in its logs and startup time.

| Tool | Full subprocess wall time in seconds | Scope |
| --- | --- | --- |
| CodeMark | 0.0918, 0.0985 | Reference marking plus seven comparisons |
| Copydetect | 1.2560, 1.2401 | Python/import startup, filtering and seven comparisons |
| JPlag initial failures | 0.5011, 0.5001 | Failed startup/parsing attempts |
| JPlag corrected profile | 1.3060 | JVM/probe, parsing, 28 pairs, clustering and report export |

JPlag also compared candidate/candidate pairs; all 28 exports are retained, while
the table consistently selects the seven predeclared reference pairs. The timing
workloads and startup costs differ, so these measurements do not establish a
speed winner. This tiny synthetic corpus also cannot establish general accuracy,
robustness, plagiarism, legal ownership, or a best tool.

## Reproduce

The source release contains `examples/evaluation/run.py`, its README, the frozen
corpus and `tools.lock.json`. Supply the verified existing
[JPlag 6.3.0 JAR](https://github.com/jplag/JPlag/releases/tag/v6.3.0) and an existing
[Copydetect 0.5.0 installation](https://pypi.org/project/copydetect/0.5.0/).
The runner downloads and installs nothing. Provide network isolation externally.
The default resource profile uses the corrected JVM flags; `--java-resource-profile
initial` reproduces the original profile. Existing outputs are never overwritten.

```sh
python3 examples/evaluation/run.py --jplag-jar /existing/jplag-6.3.0.jar --output /new/results
```

## Português brasileiro

O corpus Python foi congelado antes das pontuações: uma referência original,
cinco variantes derivadas e dois controles escritos separadamente. Candidatos
nunca herdaram marcas; apenas uma cópia temporária da referência foi marcada
pelo CodeMark. Os outros detectores receberam a referência original sem marcas.

No valor ilustrativo 0,65, CodeMark inclui três das cinco variantes derivadas;
JPlag AVG e a média direcional de Copydetect incluem quatro. Os dois controles
ficam abaixo desse valor. A cópia parcial conhecida fica abaixo dele nos três
resumos, e CodeMark também perde a variante de formatação/aspas. As escalas e
regras nativas são diferentes; 0,65 não é um padrão comum ou uma calibração.

CodeMark e Copydetect completaram duas execuções com pontuações idênticas. JPlag
falhou duas vezes por alocação nativa no limite de 2 GiB e concluiu uma terceira
tentativa com SerialGC e heap inicial de 32 MiB, sem ampliar o limite, alterar o
binário, o corpus ou a sensibilidade. Falhas, saídas, logs e exportações foram
preservados. A execução bem-sucedida de JPlag não estabelece repetibilidade.
Tempos incluem custos diferentes e não sustentam vencedor de velocidade.
