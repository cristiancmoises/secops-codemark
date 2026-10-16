# Formatos e cobertura

## Comentário de procedência

A marca contém versão do formato, UUID do projeto, identificador do arquivo e titular em string JSON. O delimitador segue a extensão.

```scheme
;; CodeMark v1 project=<uuid> file=<id> owner="Sua organização"
```

CodeMark preserva shebangs reconhecidos, declarações de encoding, XML, charset CSS, cookies de editor cobertos, BOM UTF-8 e finais CRLF. Avisos de copyright e licença existentes permanecem.

## Diretório de metadados

| Caminho | Significado |
| --- | --- |
| `.codemark/project.json` | Identidade do projeto e titular declarado |
| `.codemark/manifest.json` | Hashes de conteúdo e referência de comparação |
| `.codemark/manifest.json.sshsig` | Assinatura OpenSSH opcional |
| `.codemark/manifest.json.asc` | Assinatura OpenPGP opcional |
| `.codemark/lock` | Trava de operação; não versionar |

Trate metadados como evidência, com o mesmo cuidado dos fontes. Guarde uma referência independente confiável. Remover marcas mantém o manifesto anterior, de modo que a verificação acusa as divergências.

## Famílias de linguagens

| Estilo de comentário | Exemplos |
| --- | --- |
| `#` | Python, shell, Ruby, Perl, PowerShell, Nix, YAML, TOML, CMake |
| `;;` | Scheme, Emacs Lisp, Common Lisp, Clojure, Racket |
| `//` | JavaScript, TypeScript, C, C++, Rust, Go, Java, C#, Kotlin, Swift, Dart |
| `/* … */` | CSS, SCSS, Less |
| `<!-- … -->` | HTML, XML, SVG, Vue, Svelte |
| `--` | SQL, Lua |

Isso cobre formatos de comentário; não é prova por compilador de cada linguagem. Execute os testes do seu projeto após a marcação.

## Entradas ignoradas ou recusadas

Apenas fontes UTF-8 cobertos são marcados. JSON, PHP, binários, compactados, outros encodings, pacotes minificados, PowerShell assinado e prologues protegidos isolados sem quebra de linha ficam fora da marcação.

Diretórios excluídos conhecidos incluem `.git`, `.hg`, `.svn`, `.codemark`, ambientes virtuais, `node_modules`, `vendor`, `third_party`, `third-party`, `dist`, `build`, `target` e caches comuns. Outros diretórios de terceiros precisam ficar fora da raiz escolhida.

Leia o campo JSON `skipped`. Links e arquivos especiais são recusados. Consulte os [limites da CLI](../cli.md).

## Sketch de similaridade

A comparação aproximada ignora comentários e normaliza nomes de variáveis e funções, preservando literais, palavras-chave e operações. Usa grupos de cinco tokens, até 256 hashes e similaridade Jaccard. Exige ao menos 40 tokens e oito fingerprints.

A pontuação descreve esses sketches. Não constitui prova semântica, conclusão de plágio ou porcentagem de linhas copiadas.
