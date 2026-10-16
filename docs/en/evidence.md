# Evidence and reproducible evaluation

Already used in the maintainer’s projects.

Current qualification, reproducible examples and tool-comparison results are recorded with their commands, versions and limitations. Pending measurements remain pending; controlled fixtures are separate from project use.

## Frozen similarity comparison

The [measured comparison](../reports/0.4.0/similarity-review.md) uses one original
Python reference, five known derived variants and two separately written
controls. Its corpus and matching settings were frozen before the first scores.
Candidates never inherited watermarks. CodeMark marked a temporary reference
copy; JPlag 6.3.0 and Copydetect 0.5.0 read the original unmarked reference.

| Candidate | CodeMark | JPlag AVG | Copydetect mean directional coverage |
| --- | --- | --- | --- |
| Exact copy | 1.0000 | 1.0000 | 1.0000 |
| Identifier rename | 0.9174 | 1.0000 | 1.0000 |
| Formatting/comments | 0.5633 | 0.9937 | 0.9174 |
| Function reorder | 0.9703 | 1.0000 | 0.9978 |
| Partial known copy | 0.3426 | 0.4361 | 0.4353 |
| Same-domain control | 0.0767 | 0.0000 | 0.0000 |
| Unrelated control | 0.0559 | 0.0000 | 0.0000 |

The tools measure different things. At the illustrative value 0.65, all three
summaries miss the partial known copy; CodeMark also misses the formatting/quote
variant. Both controls stay below that value. This is neither a calibrated rule
nor every tool's default. The complete directional scores and native defaults
are in the [raw results](../reports/0.4.0/similarity-results.json).

CodeMark and Copydetect completed two runs with identical scores. JPlag failed
twice on native allocation under the 2 GiB address limit, then completed one
resource-corrected attempt using SerialGC and a 32 MiB initial heap. The limit,
binary, corpus and matching settings were unchanged. All failures and logs are
retained; JPlag repeat stability remains unmeasured. Its blocked version probe
and JVM startup are included in timing. Different workloads and this small
corpus do not support a speed winner, a general tool ranking, or plagiarism proof.

The source release includes the reproducible runner, corpus manifest, dependency
hashes and instructions in `examples/evaluation/`. It accepts existing tools and
does not download or install packages. This comparison covers Python fixtures
on the recorded GNU/Linux environment, not every supported language or platform.

See [Validation](validation.md) for release records and [Integration](integration.md) for the operating workflow.
