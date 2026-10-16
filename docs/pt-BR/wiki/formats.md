# Formatos e cobertura

## Duas referências

| Caminho | Função |
| --- | --- |
| `.codemark/integrity.json` | Snapshot de regulares: caminhos, tamanhos, modos, SHA-256 e SHA-512 |
| `.codemark/attestations.json` | Registros canônicos encadeados de atestação híbrida |
| `.codemark/project.json` | Identidade e titular declarados do fluxo legado |
| `.codemark/manifest.json` | Hashes e sketches de tokens dos fontes legados |
| `.codemark/manifest.json.sshsig` | Assinatura OpenSSH legada opcional |
| `.codemark/manifest.json.asc` | Assinatura OpenPGP legada opcional |
| `.codemark/lock` | Trava de operação; não versionar |

Não reformate snapshot autenticado: assinaturas vinculam os digests de seus bytes exatos. O registro encadeado vincula ambos os digests, identidade, sequência, SHA-512 do registro canônico anterior, horário local, versão e dois fingerprints. Veja [Rastreabilidade](../traceability.md).

O snapshot cobre regulares sem depender de extensão ou encoding, com `.codemark` e VCS explicitamente excluídos. Bundles privados incluem esses diretórios de regulares. Ambos são distintos dos formatos menores de comentários abaixo.

## Comentário legado de procedência

O formato continua `CodeMark v1` por compatibilidade, apesar do nome de apresentação SecOps Codemark:

```scheme
;; CodeMark v1 project=<uuid> file=<id> owner="Sua organização"
```

O comentário contém versão, UUID do projeto, identificador e titular em string JSON. Shebangs, declarações de encoding/XML, charset CSS, cookies cobertos, BOM UTF-8 e CRLF reconhecidos são preservados. Avisos de copyright e licença permanecem.

## Famílias de comentários

| Estilo | Exemplos |
| --- | --- |
| `#` | Python, shell, Ruby, Perl, PowerShell, Nix, YAML, TOML, CMake |
| `;;` | Scheme, Emacs Lisp, Common Lisp, Clojure, Racket |
| `//` | JavaScript, TypeScript, C/C++, Rust, Go, Java, C#, Kotlin, Swift, Dart |
| `/* … */` | CSS, SCSS, Less |
| `<!-- … -->` | HTML, XML, SVG, Vue, Svelte |
| `--` | SQL, Lua |

É cobertura de comentário, não qualificação por compilador de cada linguagem. JSON, PHP, binários, outros encodings, minificados, PowerShell assinado e prologues isolados protegidos ficam fora da marcação; snapshots de regulares ainda podem calcular seus hashes.

Dependências/builds conhecidos são excluídos da marcação, não automaticamente de snapshots ou bundles. Mantenha fontes de terceiros fora do módulo que marca como próprio. Leia `skipped` da marcação e `excluded` explícito do snapshot.

## Sketches de similaridade

A aproximação ignora comentários e normaliza nomes de variáveis/funções, preservando literais, palavras-chave e operações. Usa grupos de cinco tokens, até 256 hashes e Jaccard, com mínimo de 40 tokens e oito fingerprints.

A pontuação descreve sketches limitados, não equivalência semântica, porcentagem de linhas copiadas ou conclusão de plágio. Compare ferramentas apenas no escopo medido de entradas e configuração; veja [Evidências](../evidence.md).
