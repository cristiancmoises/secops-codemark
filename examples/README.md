# Demonstração controlada

Execute na pasta principal do CodeMark:

```sh
python3 codemark.py mark examples/original --owner "Example Author" --apply
python3 codemark.py verify examples/original
python3 codemark.py compare examples/original examples/suspect --json
python3 codemark.py unmark examples/original --apply
```

A comparação deve localizar `renamed.py` apesar dos nomes diferentes. O comando
de comparação retorna 1 quando há candidatos; nesse exemplo é esperado.
Os exemplos são públicos e artificiais. Não medem desempenho contra REA.
