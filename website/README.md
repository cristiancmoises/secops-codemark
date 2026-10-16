# SecOps Codemark static website

The production origin is `https://codemark.securityops.co`. The site is prebuilt HTML and CSS with local SVG assets. It has no JavaScript, analytics, external font requests, npm packages, or runtime service dependency.

## Build and preview

Run from the repository root with Python 3.10 or newer:

```sh
python3 scripts/build_site.py --check
python3 -m http.server 8000 --bind 127.0.0.1 --directory website/public
```

Open `http://127.0.0.1:8000/`. `--check` builds the site and verifies local links and anchors, unique element IDs, one h1 per page, and the absence of script tags, event-handler attributes, and external assets in the generated documents. It also checks local SVG files for active content. It does not replace a browser accessibility or visual check.

Use `--output /path/to/staging` for an alternative output directory. Generated output is not source and is ignored by Git. The builder overwrites its generated files; it does not delete existing downloads. Use a new staging directory when preparing a clean deployment.

## Content

| Source | Published content |
| --- | --- |
| `docs/en/*.md` | English documentation |
| `docs/pt-BR/*.md` | Brazilian Portuguese documentation |
| `docs/en/wiki/*.md` | English wiki |
| `docs/pt-BR/wiki/*.md` | Brazilian Portuguese wiki |
| `SECURITY.md` | Security policy in both language routes |
| `website/assets/` | Local stylesheet and favicon |
| `website/data/release.json` | Release summary, measured checks, repositories, reports, and downloads |
| `COPYING` | Full license at `/license.txt` |

The root is the English homepage. `/en/` and `/pt-br/` have matching page routes and language links. Documentation, wiki, evidence, downloads, and original reports are separate pages. The generator supports the small Markdown subset used by these sources: paragraphs, headings, fenced code, flat lists, tables, links, strong text, and inline code. Raw HTML is escaped.

The logo uses a CSS stroke animation and the title uses a finite entrance animation. Both finish within two seconds and are disabled for `prefers-reduced-motion`. The site uses semantic landmarks, visible keyboard focus, a skip link, responsive layouts, and horizontally scrollable code and tables.

## Release metadata

Results stay `pending` until measured. Never substitute historical test counts for the current source revision. Fields that show text accept either a string or an object with `en` and `pt-br` translations.

The metadata contract is:

```json
{
  "version": "0.4.0",
  "date": "YYYY-MM-DD",
  "commit": "source revision or immutable release reference",
  "site_url": "https://codemark.securityops.co",
  "status": "pending",
  "scope": {"en": "Measured scope", "pt-br": "Escopo medido"},
  "repositories": [{"label": "Repository", "url": "https://example.org/project"}],
  "checks": [{"name": "Check", "status": "pending", "detail": "Exact scope", "command": "optional command"}],
  "metrics": [{"label": "Metric", "value": "Measured value", "detail": "Measurement boundary"}],
  "reports": [{"title": "Report", "path": "docs/reports/0.4.0-validation.json", "date": "YYYY-MM-DD", "scope": "Exact scope", "status": "current"}],
  "downloads": [
    {"label": "Portable", "url": "/downloads/codemark.pyz", "path": "dist/codemark.pyz"},
    {"label": "0.4.0 source", "url": "/downloads/secops-codemark-0.4.0.zupt", "path": "dist/secops-codemark-0.4.0.zupt"}
  ]
}
```

Allowed statuses are `pass`, `fail`, `skip`, `pending`, `historical`, `current`, and `qualified-with-scope`. A report must be a regular file below `docs/`, without symlinks. Filenames must be unique. Original files are copied to `/reports/` and readable report pages are generated in both languages. Historical records retain their original contents and get a visible context notice.

A download's optional `path` copies a regular file from `dist/` to `/downloads/`; its URL must match that filename. Without `path`, the release process must stage the file at the declared local URL before `--check`. Genuine `.zupt` archives, archive testing, extraction comparison, and checksums belong to the release build; the website builder does not create packages.

## Deploy

Publish only the generated output directory. Use a static virtual host for `codemark.securityops.co` with HTTPS and `index.html` directory indexes. Serve unknown paths as 404 rather than returning the homepage for every request.

Recommended response policy for this site:

```text
Content-Security-Policy: default-src 'none'; script-src 'none'; style-src 'self'; img-src 'self'; font-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
```

Use the appropriate MIME types for HTML, CSS, SVG, JSON, plain-text reports, and `.zupt` downloads. Enable HSTS only after confirming the intended HTTPS configuration. Publish an atomic directory switch from a clean, checked staging directory and retain the previous directory for rollback.

Verify the deployed root, both languages, documentation links, reports, artifact checksums, HTTPS, and response headers. Deployment and DNS are operational steps outside the static build.

## Português brasileiro

O site é HTML/CSS/SVG estático, sem JavaScript, analytics ou fontes externas. Gere e confira com `python3 scripts/build_site.py --check`; visualize usando o servidor local acima. Os fontes bilíngues ficam em `docs/en` e `docs/pt-BR`.

Registre somente resultados medidos em `website/data/release.json`. Preserve escopo, datas, falhas e ausências. Publique apenas `website/public`, com HTTPS, tipos MIME corretos e política que bloqueie scripts. Confira páginas, relatórios e checksums após o deploy. Mantenha a versão anterior para rollback.
