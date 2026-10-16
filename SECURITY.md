# Security policy

## Scope

SecOps Codemark's current release line is 0.4.x. Security fixes are developed against the latest source and current release; the project does not promise backports or a response deadline. Historical qualification files remain evidence for their stated version only.

Read the [security model](docs/en/security.md) or [modelo de segurança](docs/pt-BR/security.md) before using the tool. Reversible comments are not an access-control mechanism. Similarity scores do not establish plagiarism or ownership. A signature authenticates a manifest against a pinned key without proving date or originality.

## Reporting

Use the GitHub repository's **Security → Report a vulnerability** facility when available. If private reporting is unavailable, open an issue requesting a private contact without publishing exploit details or sensitive data. The maintainers must agree on a private channel before you send sensitive material.

Include the version, platform, exact command, expected and observed behavior, exit status, and a minimal synthetic reproducer. Explain the affected trust boundary and whether source, metadata, signing, report handling, or packaging is involved.

Never submit private keys, credentials, real private source trees, personal data, or private agent histories. Do not test a report against another person's infrastructure without authorization.

## Disclosure and fixes

Coordinate disclosure with maintainers after receipt is confirmed. A report is not acknowledged until a maintainer responds. Fixes should preserve limits, source byte preservation, key pinning, safe metadata validation, and failure behavior. Add a regression test for the actual defect and retain failures and skips in the evidence.

The website's dated evidence records are development checks and agent reviews where stated; they are not external certification or a guarantee that no vulnerability exists.

## Português brasileiro

Use **Security → Report a vulnerability** no GitHub quando disponível. Se o relato privado não estiver disponível, abra uma issue pedindo um contato privado, sem detalhes de exploração ou dados sensíveis. Aguarde combinar um canal antes de enviar esse material.

Informe versão, plataforma, comando, comportamento esperado e observado, código de saída e reproducer sintético mínimo. Nunca envie chaves privadas, credenciais, fontes privados ou dados pessoais. A linha atual é 0.4.x; não há promessa de backport ou prazo de resposta. Leia o [modelo de segurança](docs/pt-BR/security.md).
