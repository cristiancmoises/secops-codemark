# Frozen synthetic similarity comparison

This Python-only corpus compares one original reference with seven candidates:
five known derived copies, including partial overlap, and two separately written
controls. The inputs, labels, hashes, settings, and limitations were frozen in
`corpus/manifest.json` before the first tool scores. This small corpus cannot
establish a general tool ranking or prove plagiarism.

Use Python 3.12, Java 25, the existing JPlag 6.3.0 release JAR, and an existing
Copydetect 0.5.0 installation with the dependency versions in `tools.lock.json`.
The runner checks the pinned JAR hash and every corpus file. It does not download
or install anything. Obtain and verify tools separately through their official
release channels. Run in a network-disabled environment if isolation is required;
the runner does not create that boundary itself. JPlag performs a version probe
even in RUN mode; its blocked probe remains in the captured logs and timing.

The default JVM resource profile adds `-XX:+UseSerialGC -Xms32m` to the bounded
heap/class/code-cache settings. The original profile failed twice under the
recorded 2 GiB address limit; one recovery attempt with these two flags succeeded.
Those failures remain in the published results. To reproduce the original
profile, pass `--java-resource-profile initial`. No sandbox limit was raised and
no matching sensitivity changed. The successful JPlag recovery has one measured
score run; repeat stability was not established for that tool.

```sh
python3 examples/evaluation/run.py \
  --jplag-jar /existing/tools/jplag-6.3.0.jar \
  --output /new/benchmark-output
```

If packages are already unpacked in an isolated environment, supply their
directory explicitly with `--copydetect-path /existing/packages`. The runner
does not modify the installation. It writes only to the new output directory.

CodeMark marks a temporary copy of the reference; candidates remain unmarked.
JPlag and Copydetect receive the original unmarked reference. Each tool runs
twice with its native matching defaults. CodeMark's report threshold is `1e-9`
to expose nonzero reported candidates; an absent candidate is not assigned an
invented zero. Copydetect's two directional coverage fractions are retained.
JPlag's native average similarity and exported data are retained.

The shared `0.65` observation is illustrative. These scores have different
meanings and the tools do not share that default threshold. Preserve misses,
false positives, errors, and complete logs. No sensitivity or corpus changes
are permitted after observing the first scores in this experiment.

Full subprocess timing includes startup and output export. CodeMark timing also
includes reference marking. JPlag timing includes JVM startup and its blocked
network probe. The experiment does not support a speed winner.

All fixture source is original for this example and GPL-3.0-or-later. The two
controls were written separately from the reference; they do not represent
external authors, users, or independent adoption.
