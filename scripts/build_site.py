#!/usr/bin/env python3
"""Build the bilingual, JavaScript-free CodeMark website with the stdlib."""

import argparse
import json
import re
import shutil
import xml.etree.ElementTree as ET
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "website"
OUT = SITE / "public"
DOCS = ["getting-started", "cli", "signing", "integration", "security", "validation"]
WIKI = ["architecture", "formats", "troubleshooting", "contributing"]
TEXT = {
    "en": {
        "language": "English",
        "other": "Português",
        "other_lang": "pt-br",
        "source_dir": "en",
        "nav": ["Docs", "Wiki", "Evidence", "Downloads"],
        "skip": "Skip to content",
        "tagline": "Source provenance. Locally verifiable.",
        "description": "Reversible source marks, integrity manifests, and copy-candidate analysis. Your source stays on your machine.",
        "start": "Read the documentation",
        "download": "Get CodeMark",
        "offline": "Offline by design",
        "license": "License",
        "runtime": "Runtime",
        "release": "Release",
        "network": "Network required",
        "none": "None",
        "workflow": "A reference you can inspect.",
        "workflow_detail": "Start with your own source. Keep a trusted record. Investigate differences with the context they deserve.",
        "steps": [
            (
                "Mark",
                "Preview reversible comments. Record a project identity and source hashes without changing the source license.",
            ),
            (
                "Verify",
                "Compare a stable tree with its manifest. Add a pinned-key signature when you need an authenticated reference.",
            ),
            (
                "Compare",
                "Find exact content and token-similarity candidates. Review the matching files before drawing conclusions.",
            ),
        ],
        "limits_title": "Understand what the evidence means.",
        "limits": "Marks are removable. Signatures bind a manifest to a key. Similarity produces candidates for review. None of these establishes legal ownership, a trusted timestamp, or universal copy detection.",
        "security_link": "Read the security model",
        "evidence_link": "Inspect release evidence",
        "docs_title": "Documentation",
        "docs_intro": "From a first preview to a signed release reference. Commands, boundaries, and reproducible checks in one place.",
        "wiki_title": "Project wiki",
        "wiki_intro": "How CodeMark works, how its formats behave, and how to diagnose or contribute a change.",
        "doc_titles": [
            "Get started",
            "CLI reference",
            "Signing",
            "CI and integration",
            "Security model",
            "Validation",
        ],
        "doc_details": [
            "Install, inspect the host, preview, apply, and reverse a mark.",
            "Commands, reports, exit status, and resource limits.",
            "OpenSSH Ed25519 and optional OpenPGP with a pinned key.",
            "Protect the reference through a release and verification pipeline.",
            "Trust boundaries, key handling, and the meaning of a match.",
            "Reproduce checks and distinguish historical evidence.",
        ],
        "wiki_titles": [
            "Architecture",
            "Formats and coverage",
            "Troubleshooting",
            "Contributing",
        ],
        "wiki_details": [
            "Modules, data flow, and operational boundaries.",
            "Comment families, metadata, exclusions, and token sketches.",
            "Interpret failures, skips, locks, and signature errors.",
            "Development checks, bilingual docs, and release evidence.",
        ],
        "evidence_title": "Release evidence",
        "evidence_intro": "Measured results have a date, a source revision, and a scope. Pending work remains visible; historical reports retain their original version.",
        "checks": "Current release checks",
        "reports": "Reports and audits",
        "reports_intro": "Reports state their method, scope, and limitations. Read them alongside the measured results.",
        "commit": "Source revision",
        "date": "Record date",
        "unknown": "Pending",
        "scope": "Scope",
        "report_download": "Download report",
        "view_report": "Read report",
        "downloads_title": "Downloads",
        "downloads_intro": "Portable Python executable and genuine .zupt source archives. Verify SHA-256 checksums against an independently trusted reference before running downloaded code.",
        "downloads_pending": "Downloads are being qualified for this release. Published artifacts will appear here after their checks are recorded.",
        "download_help": "The portable requires Python 3.10 or newer. Source releases use the genuine .zupt format and require zupt to extract. A checksum detects a change against a trusted reference; it does not authenticate the publisher by itself.",
        "footer": "Local provenance and integrity tooling. Free software, GPL-3.0-or-later.",
        "static": "Static HTML + CSS · No JavaScript · No analytics",
        "policy": "Security policy",
        "historical": "Historical record",
        "historical_notice": "This report applies to its stated historical version and scope. It is preserved as evidence and does not qualify changed source in a later release.",
        "statuses": {
            "pass": "Pass",
            "fail": "Fail",
            "skip": "Skip",
            "pending": "Pending",
            "historical": "Historical",
            "qualified-with-scope": "Qualified with scope",
            "current": "Current",
        },
    },
    "pt-br": {
        "language": "Português brasileiro",
        "other": "English",
        "other_lang": "en",
        "source_dir": "pt-BR",
        "nav": ["Docs", "Wiki", "Evidências", "Downloads"],
        "skip": "Pular para o conteúdo",
        "tagline": "Procedência de fontes. Verificação local.",
        "description": "Marcas reversíveis, manifestos de integridade e análise de possíveis cópias. Seus fontes ficam na sua máquina.",
        "start": "Ler a documentação",
        "download": "Baixar CodeMark",
        "offline": "Local por princípio",
        "license": "Licença",
        "runtime": "Ambiente",
        "release": "Versão",
        "network": "Precisa de rede",
        "none": "Não",
        "workflow": "Uma referência que você pode conferir.",
        "workflow_detail": "Comece pelos seus fontes. Preserve um registro confiável. Investigue divergências com o contexto necessário.",
        "steps": [
            (
                "Marcar",
                "Confira a prévia dos comentários reversíveis. Registre identidade e hashes sem mudar a licença do fonte.",
            ),
            (
                "Verificar",
                "Compare a árvore estável com o manifesto. Assine com chave fixada quando precisar autenticar a referência.",
            ),
            (
                "Comparar",
                "Localize candidatos por conteúdo exato e similaridade de tokens. Inspecione os arquivos antes de concluir.",
            ),
        ],
        "limits_title": "Entenda o significado das evidências.",
        "limits": "Marcas são removíveis. Assinaturas vinculam um manifesto a uma chave. Similaridade gera candidatos para revisão. Essas camadas não comprovam titularidade jurídica, data confiável ou detecção universal de cópias.",
        "security_link": "Ler o modelo de segurança",
        "evidence_link": "Conferir as evidências",
        "docs_title": "Documentação",
        "docs_intro": "Da primeira prévia à referência assinada. Comandos, limites e verificações reproduzíveis reunidos num só lugar.",
        "wiki_title": "Wiki do projeto",
        "wiki_intro": "Como CodeMark funciona, seus formatos e como diagnosticar problemas ou contribuir com mudanças.",
        "doc_titles": [
            "Primeiros passos",
            "Referência da CLI",
            "Assinaturas",
            "CI e integração",
            "Modelo de segurança",
            "Validação",
        ],
        "doc_details": [
            "Instalar, conferir o host, visualizar, aplicar e remover marcas.",
            "Comandos, relatórios, códigos de saída e limites.",
            "OpenSSH Ed25519 e OpenPGP opcional com chave fixada.",
            "Preservar a referência no lançamento e na verificação.",
            "Confiança, chaves e o significado de uma correspondência.",
            "Reproduzir checks e identificar evidências históricas.",
        ],
        "wiki_titles": [
            "Arquitetura",
            "Formatos e cobertura",
            "Resolver problemas",
            "Contribuir",
        ],
        "wiki_details": [
            "Módulos, fluxo de dados e limites operacionais.",
            "Comentários, metadados, exclusões e sketches de tokens.",
            "Interpretar falhas, ausências, travas e erros de assinatura.",
            "Checks de desenvolvimento, documentação bilíngue e evidências.",
        ],
        "evidence_title": "Evidências da versão",
        "evidence_intro": "Resultados medidos têm data, revisão e escopo. Pendências ficam visíveis; relatórios históricos preservam sua versão original.",
        "checks": "Verificações da versão atual",
        "reports": "Relatórios e auditorias",
        "reports_intro": "Os relatórios declaram método, escopo e limitações. Leia-os junto dos resultados medidos.",
        "commit": "Revisão do fonte",
        "date": "Data do registro",
        "unknown": "Pendente",
        "scope": "Escopo",
        "report_download": "Baixar relatório",
        "view_report": "Ler relatório",
        "downloads_title": "Downloads",
        "downloads_intro": "Executável Python portátil e fontes em .zupt genuíno. Confira SHA-256 contra referência confiável independente antes de executar código baixado.",
        "downloads_pending": "Os downloads desta versão estão em qualificação. Os artefatos aparecerão aqui após registrar suas verificações.",
        "download_help": "O portátil precisa de Python 3.10 ou superior. Os fontes usam .zupt genuíno e precisam de zupt para extração. Um checksum detecta mudanças contra referência confiável; sozinho não autentica quem publicou o arquivo.",
        "footer": "Ferramentas locais de procedência e integridade. Software livre, GPL-3.0-or-later.",
        "static": "HTML + CSS estáticos · Sem JavaScript · Sem analytics",
        "policy": "Política de segurança",
        "historical": "Registro histórico",
        "historical_notice": "Este relatório vale para a versão e o escopo históricos declarados. Foi preservado como evidência e não qualifica fontes alterados de outra versão.",
        "statuses": {
            "pass": "Passou",
            "fail": "Falhou",
            "skip": "Ausente",
            "pending": "Pendente",
            "historical": "Histórico",
            "qualified-with-scope": "Qualificado no escopo",
            "current": "Atual",
        },
    },
}


def localized(value, lang):
    """Accept plain strings or a small pair of translated labels in metadata."""
    if isinstance(value, dict):
        return str(value.get(lang, value.get("en", "")))
    return str(value) if value is not None else ""


def safe_url(value):
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme not in {"https", "mailto"}:
        raise ValueError(f"Unsupported link scheme: {parsed.scheme}")
    if value.startswith("//") or any(ord(char) < 32 for char in value):
        raise ValueError("Invalid URL")
    return escape(value, quote=True)


def source_file(value, parent):
    path = ROOT / value
    if path.is_absolute() and path.is_relative_to(ROOT / parent):
        if any(
            part.is_symlink()
            for part in (path, *path.parents)
            if part.is_relative_to(ROOT)
        ):
            raise ValueError(f"Symlink not allowed in published source: {value}")
        resolved = path.resolve(strict=True)
        if resolved.is_relative_to(ROOT / parent) and resolved.is_file():
            return resolved
    raise ValueError(f"Publication source must be a regular file below {parent}/")


def slug(text):
    return re.sub(r"[^\w-]+", "-", text.lower()).strip("-")


def document_map(lang, data):
    mapping = {}
    base = ROOT / "docs" / TEXT[lang]["source_dir"]
    for name in DOCS:
        mapping[(base / f"{name}.md").resolve()] = f"/{lang}/docs/{name}/"
    for name in WIKI:
        mapping[(base / "wiki" / f"{name}.md").resolve()] = f"/{lang}/wiki/{name}/"
    mapping[ROOT / "SECURITY.md"] = f"/{lang}/docs/security-policy/"
    mapping[ROOT / "CONTRIBUTING.md"] = f"/{lang}/wiki/contributing/"
    for report in data["reports"]:
        path = source_file(report["path"], "docs")
        mapping[path] = f"/{lang}/reports/{path.stem}/"
    return mapping


def inline(text, source, mapping):
    pattern = r"(`[^`]+`|\[[^\]]+\]\([^\s)]+\)|\*\*[^*]+\*\*)"
    parts = []
    for item in re.split(pattern, text):
        if item.startswith("`") and item.endswith("`"):
            parts.append("<code>" + escape(item[1:-1]) + "</code>")
        elif item.startswith("**") and item.endswith("**"):
            parts.append("<strong>" + escape(item[2:-2]) + "</strong>")
        elif item.startswith("[") and "](" in item:
            label, link = item[1:-1].split("](", 1)
            parsed = urlsplit(link)
            if not parsed.scheme and not link.startswith(("/", "#")):
                target = (source.parent / unquote(parsed.path)).resolve()
                if target not in mapping:
                    raise ValueError(f"Unmapped documentation link in {source}: {link}")
                link = mapping[target] + (
                    "#" + parsed.fragment if parsed.fragment else ""
                )
            parts.append(f'<a href="{safe_url(link)}">{escape(label)}</a>')
        else:
            parts.append(escape(item))
    return "".join(parts)


def markdown(content, source, mapping):
    """Render the documented subset: paragraphs, headings, lists, tables, code."""
    lines = content.splitlines()
    result = []
    index = 0
    ids = {}
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            result.append(
                '<pre tabindex="0"><code>' + escape("\n".join(code)) + "</code></pre>"
            )
        elif match := re.match(r"^(#{1,3}) (.+)$", line):
            level = len(match[1])
            title = match[2]
            name = slug(title)
            ids[name] = ids.get(name, 0) + 1
            if ids[name] > 1:
                name += f"-{ids[name]}"
            result.append(
                f'<h{level} id="{name}">{inline(title, source, mapping)}</h{level}>'
            )
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append(
                    [
                        cell.strip()
                        for cell in lines[index].strip().strip("|").split("|")
                    ]
                )
                index += 1
            result.append(
                '<div class="table-scroll" role="region" aria-label="'
                + ("Tabela" if "/pt-BR/" in str(source) else "Table")
                + '" tabindex="0"><table>'
            )
            for row_index, row in enumerate(rows):
                if all(re.fullmatch(r"[-: ]+", cell) for cell in row):
                    continue
                tag = "th" if row_index == 0 else "td"
                result.append(
                    "<tr>"
                    + "".join(
                        f"<{tag}"
                        + (' scope="col"' if tag == "th" else "")
                        + f">{inline(cell, source, mapping)}</{tag}>"
                        for cell in row
                    )
                    + "</tr>"
                )
            result.append("</table></div>")
            continue
        elif re.match(r"^(?:- |\d+\. )", line):
            ordered = bool(re.match(r"^\d+\. ", line))
            tag = "ol" if ordered else "ul"
            result.append(f"<{tag}>")
            while index < len(lines) and re.match(r"^(?:- |\d+\. )", lines[index]):
                item = re.sub(r"^(?:- |\d+\. )", "", lines[index])
                result.append("<li>" + inline(item, source, mapping) + "</li>")
                index += 1
            result.append(f"</{tag}>")
            continue
        else:
            paragraph = [line]
            index += 1
            while (
                index < len(lines)
                and lines[index].strip()
                and not re.match(r"^(?:#|```|\||- |\d+\. )", lines[index])
            ):
                paragraph.append(lines[index])
                index += 1
            result.append("<p>" + inline(" ".join(paragraph), source, mapping) + "</p>")
            continue
        index += 1
    return "\n".join(result)


def symbol(large=False):
    cls = ' class="hero-symbol"' if large else ""
    line = ' class="logo-line"' if large else ""
    return f'<svg{cls} viewBox="0 0 160 160" fill="none" aria-hidden="true"><path{line} d="M57 34 16 80l41 46m46-92 41 46-41 46M96 20 64 140" stroke="currentColor" stroke-width="5" stroke-linejoin="miter"/></svg>'


def badge(status, lang):
    if status not in TEXT[lang]["statuses"]:
        raise ValueError(f"Unsupported result status: {status}")
    return (
        f'<span class="status status-{status}">{TEXT[lang]["statuses"][status]}</span>'
    )


def page(lang, route, title, description, body, data, section=""):
    t = TEXT[lang]
    path = f"/{lang}/{route}" if route else f"/{lang}/"
    other = f"/{t['other_lang']}/{route}"
    nav = []
    for name, label in zip(("docs", "wiki", "evidence", "downloads"), t["nav"]):
        current = ' aria-current="page"' if section == name else ""
        nav.append(f'<a href="/{lang}/{name}/"{current}>{label}</a>')
    repos = "".join(
        f'<a href="{safe_url(repo["url"])}">{escape(repo["label"])}</a>'
        for repo in data["repositories"]
    )
    canonical = data["site_url"].rstrip("/") + path
    return f'''<!doctype html>
<html lang="{"pt-BR" if lang == "pt-br" else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · CODEMARK</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="theme-color" content="#000000">
<link rel="canonical" href="{safe_url(canonical)}">
<link rel="alternate" hreflang="en" href="{safe_url(data["site_url"].rstrip("/") + "/en/" + route)}">
<link rel="alternate" hreflang="pt-BR" href="{safe_url(data["site_url"].rstrip("/") + "/pt-br/" + route)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/styles.css">
</head>
<body>
<a class="skip-link" href="#main">{t["skip"]}</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="/{lang}/">{symbol()}<span>CODEMARK</span></a>
<nav class="site-nav" aria-label="{"Navegação principal" if lang == "pt-br" else "Main navigation"}">{"".join(nav)}<a class="language-link" lang="{"pt-BR" if lang == "en" else "en"}" hreflang="{"pt-BR" if lang == "en" else "en"}" href="{other}">{t["other"]}</a></nav>
</div></header>
<main id="main" class="wrap" tabindex="-1">{body}</main>
<footer class="site-footer wrap"><div class="footer-top"><div><a class="brand" href="/{lang}/">CODEMARK</a><p>{t["footer"]}</p></div><nav class="repo-links" aria-label="{"Repositórios de fontes" if lang == "pt-br" else "Source repositories"}">{repos}</nav></div>
<div class="footer-bottom"><span>© 2026 CodeMark contributors · <a href="/license.txt">GPL-3.0-or-later</a></span><span>{t["static"]}</span><a href="/{lang}/docs/security-policy/">{t["policy"]}</a></div></footer>
</body>
</html>
'''


def intro(title, description, eyebrow=""):
    return f'<header class="page-intro"><p class="eyebrow">{escape(eyebrow)}</p><h1>{escape(title)}</h1><p>{escape(description)}</p></header>'


def home(lang, data):
    t = TEXT[lang]
    steps = "".join(
        f'<article class="step"><span class="step-number">0{index}</span><h3>{title}</h3><p>{description}</p></article>'
        for index, (title, description) in enumerate(t["steps"], 1)
    )
    return f"""<section class="hero"><div><p class="eyebrow">{t["offline"]} / Python 3.10+</p><h1>CODEMARK</h1><p class="lead">{t["tagline"]}</p><p class="description">{t["description"]}</p><div class="actions"><a class="button" href="/{lang}/docs/getting-started/">{t["start"]} <span aria-hidden="true">↗</span></a><a class="button secondary" href="/{lang}/downloads/">{t["download"]}</a></div></div>
<div class="hero-art"><div class="art-caption"><span>Source → Reference</span><span>v{escape(data["version"])}</span></div>{symbol(True)}<pre><code><span class="prompt">$</span> python3 codemark.pyz mark ./project --owner "You"
<span class="prompt">$</span> python3 codemark.pyz verify ./project --json
<span class="prompt">$</span> python3 codemark.pyz compare ./project ./candidate</code></pre></div></section>
<div class="release-strip"><div><span class="label">{t["release"]}</span><strong>{escape(data["version"])}</strong></div><div><span class="label">{t["runtime"]}</span><strong>Python 3.10+</strong></div><div><span class="label">{t["license"]}</span><strong>GPL-3.0-or-later</strong></div><div><span class="label">{t["network"]}</span><strong>{t["none"]}</strong></div></div>
<section class="section"><div class="section-heading"><h2>{t["workflow"]}</h2><p>{t["workflow_detail"]}</p></div><div class="steps">{steps}</div></section>
<section class="section"><p class="eyebrow">{"Confiança e limites" if lang == "pt-br" else "Trust and limits"}</p><h2>{t["limits_title"]}</h2><p class="statement">{t["limits"]}</p><div class="actions"><a href="/{lang}/docs/security/">{t["security_link"]} →</a><a href="/{lang}/evidence/">{t["evidence_link"]} →</a></div></section>"""


def listing(lang, kind):
    t = TEXT[lang]
    names = DOCS if kind == "docs" else WIKI
    titles = t["doc_titles"] if kind == "docs" else t["wiki_titles"]
    details = t["doc_details"] if kind == "docs" else t["wiki_details"]
    rows = "".join(
        f'<li><a href="/{lang}/{kind}/{name}/"><span class="index">{index:02}</span><span><span class="link-title">{title}</span><span class="link-detail">{detail}</span></span><span class="arrow" aria-hidden="true">↗</span></a></li>'
        for index, (name, title, detail) in enumerate(zip(names, titles, details), 1)
    )
    title = t["docs_title"] if kind == "docs" else t["wiki_title"]
    description = t["docs_intro"] if kind == "docs" else t["wiki_intro"]
    return (
        intro(title, description, "CODEMARK / " + t["language"])
        + '<section class="section"><ul class="link-list">'
        + rows
        + "</ul></section>"
    )


def sidebar(lang, active):
    t = TEXT[lang]
    chunks = []
    for kind, names, titles in (
        ("docs", DOCS, t["doc_titles"]),
        ("wiki", WIKI, t["wiki_titles"]),
    ):
        items = []
        for name, title in zip(names, titles):
            path = f"/{lang}/{kind}/{name}/"
            current = ' aria-current="page"' if path == active else ""
            items.append(f'<li><a href="{path}"{current}>{title}</a></li>')
        chunks.append(
            f"<p>{t['docs_title'] if kind == 'docs' else t['wiki_title']}</p><ul>{''.join(items)}</ul>"
        )
    return (
        '<nav class="docs-sidebar" aria-label="'
        + t["docs_title"]
        + '">'
        + "".join(chunks)
        + "</nav>"
    )


def evidence(lang, data):
    t = TEXT[lang]
    metrics = "".join(
        f'<article class="metric"><span class="label">{escape(localized(item["label"], lang))}</span><strong>{escape(localized(item["value"], lang))}</strong><p>{escape(localized(item["detail"], lang))}</p></article>'
        for item in data["metrics"]
    )
    checks = "".join(
        f"<li><div>{badge(item['status'], lang)}</div><div><h3>{escape(localized(item['name'], lang))}</h3><p>{escape(localized(item['detail'], lang))}</p>"
        + (f"<code>{escape(item['command'])}</code>" if item.get("command") else "")
        + "</div></li>"
        for item in data["checks"]
    )
    reports = []
    for item in data["reports"]:
        source = source_file(item["path"], "docs")
        reports.append(
            f'<article class="report"><div class="report-meta">{badge(item["status"], lang)}<time datetime="{escape(item["date"], quote=True)}">{escape(item["date"])}</time></div><h3>{escape(localized(item["title"], lang))}</h3><p>{escape(localized(item["scope"], lang))}</p><a href="/{lang}/reports/{source.stem}/">{t["view_report"]}</a> · <a download href="/reports/{source.name}">{t["report_download"]}</a></article>'
        )
    return (
        intro(t["evidence_title"], t["evidence_intro"], "CODEMARK / " + data["version"])
        + f'<div class="notice"><p>{badge(data["status"], lang)} <strong>{t["date"]}:</strong> {escape(data["date"])} · <strong>{t["commit"]}:</strong> <code>{escape(data["commit"] or t["unknown"])}</code></p><p>{escape(localized(data["scope"], lang))}</p></div><div class="metrics">{metrics}</div><section class="section"><h2>{t["checks"]}</h2><ul class="check-list">{checks}</ul></section><section class="section"><h2>{t["reports"]}</h2><p>{t["reports_intro"]}</p>{"".join(reports)}</section>'
    )


def downloads(lang, data):
    t = TEXT[lang]
    if data["downloads"]:
        content = (
            '<ul class="link-list">'
            + "".join(
                f'<li><a href="{safe_url(item["url"])}"><span class="index">↓</span><span class="link-title">{escape(localized(item["label"], lang))}</span><span class="arrow" aria-hidden="true">↗</span></a></li>'
                for item in data["downloads"]
            )
            + "</ul>"
        )
    else:
        content = '<div class="notice"><p>' + t["downloads_pending"] + "</p></div>"
    return (
        intro(
            t["downloads_title"], t["downloads_intro"], "CODEMARK / " + data["version"]
        )
        + '<section class="section">'
        + content
        + "<h2>Python 3.10+</h2><p>"
        + t["download_help"]
        + '</p><pre tabindex="0"><code>python3 codemark.pyz --version\npython3 codemark.pyz self-test --json</code></pre><a href="/'
        + lang
        + '/docs/getting-started/">'
        + t["start"]
        + " →</a></section>"
    )


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.errors = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" or any(name.lower().startswith("on") for name in attrs):
            self.errors.append("JavaScript is forbidden")
        if tag == "h1":
            self.h1 += 1
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f"Duplicate element id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if (
            tag in {"img", "iframe", "audio", "video", "source", "script"}
            and "src" in attrs
        ):
            self.links.append(attrs["src"])
            if urlsplit(attrs["src"]).netloc:
                self.errors.append("External assets are forbidden")
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            self.links.append(attrs["href"])
            if urlsplit(attrs["href"]).netloc:
                self.errors.append("External assets are forbidden")


def check_site(output):
    pages = {}
    errors = []
    for path in sorted(output.rglob("*.html")):
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = parser
        errors.extend(f"{path.relative_to(output)}: {error}" for error in parser.errors)
        if parser.h1 != 1:
            errors.append(
                f"{path.relative_to(output)}: expected one h1, found {parser.h1}"
            )
    for source, parser in pages.items():
        for link in parser.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (
                output / unquote(parsed.path).lstrip("/")
                if parsed.path.startswith("/")
                else source.parent / unquote(parsed.path)
            )
            if target.is_dir():
                target /= "index.html"
            if not target.is_file() or not target.resolve().is_relative_to(
                output.resolve()
            ):
                errors.append(
                    f"{source.relative_to(output)}: missing local link {link}"
                )
            elif (
                parsed.fragment
                and target.resolve() in pages
                and parsed.fragment not in pages[target.resolve()].ids
            ):
                errors.append(f"{source.relative_to(output)}: missing anchor {link}")
    for path in output.rglob("*.svg"):
        root = ET.parse(path).getroot()
        if any(
            element.tag.rsplit("}", 1)[-1] == "script"
            or any(name.lower().startswith("on") for name in element.attrib)
            for element in root.iter()
        ):
            errors.append(
                f"{path.relative_to(output)}: active SVG content is forbidden"
            )
    if errors:
        raise ValueError("\n".join(errors))
    return len(pages)


def build(output):
    data = json.loads((SITE / "data/release.json").read_text(encoding="utf-8"))
    if urlsplit(data["site_url"]).scheme != "https":
        raise ValueError("The canonical site URL must use HTTPS")
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("styles.css", "favicon.svg"):
        (output / "assets").mkdir(exist_ok=True)
        shutil.copyfile(SITE / "assets" / filename, output / "assets" / filename)
    shutil.copyfile(ROOT / "COPYING", output / "license.txt")
    (output / "data").mkdir(exist_ok=True)
    shutil.copyfile(SITE / "data/release.json", output / "data/release.json")
    report_names = set()
    for report in data["reports"]:
        source = source_file(report["path"], "docs")
        if source.name in report_names:
            raise ValueError("Published report filenames must be unique")
        report_names.add(source.name)
        (output / "reports").mkdir(exist_ok=True)
        shutil.copyfile(source, output / "reports" / source.name)
    for item in data["downloads"]:
        safe_url(item["url"])
        if item.get("path"):
            source = source_file(item["path"], "dist")
            if item["url"] != "/downloads/" + source.name:
                raise ValueError("Local download URL must match the staged filename")
            (output / "downloads").mkdir(exist_ok=True)
            shutil.copyfile(source, output / "downloads" / source.name)
    routes = []
    for lang, t in TEXT.items():
        mapping = document_map(lang, data)
        inline_mapping = {**document_map(t["other_lang"], data), **mapping}
        routes_for_language = {
            "": ("CODEMARK", t["description"], home(lang, data), ""),
            "docs/": (t["docs_title"], t["docs_intro"], listing(lang, "docs"), "docs"),
            "wiki/": (t["wiki_title"], t["wiki_intro"], listing(lang, "wiki"), "wiki"),
            "evidence/": (
                t["evidence_title"],
                t["evidence_intro"],
                evidence(lang, data),
                "evidence",
            ),
            "downloads/": (
                t["downloads_title"],
                t["downloads_intro"],
                downloads(lang, data),
                "downloads",
            ),
        }
        for source, target in mapping.items():
            if source == ROOT / "CONTRIBUTING.md":
                continue
            content = source.read_text(encoding="utf-8")
            is_report = target.startswith(f"/{lang}/reports/")
            if source.suffix != ".md":
                title = next(
                    localized(item["title"], lang)
                    for item in data["reports"]
                    if (ROOT / item["path"]).resolve() == source
                )
                article = f'<h1>{escape(title)}</h1><pre tabindex="0"><code>{escape(content)}</code></pre>'
            else:
                title = content.splitlines()[0].lstrip("# ")
                article = markdown(content, source, inline_mapping)
            if is_report:
                report = next(
                    item
                    for item in data["reports"]
                    if (ROOT / item["path"]).resolve() == source
                )
                notice = (
                    t["historical_notice"]
                    if report["status"] == "historical"
                    else localized(report["scope"], lang)
                )
                article = (
                    '<div class="notice"><p>'
                    + badge(report["status"], lang)
                    + " · "
                    + escape(report["date"])
                    + "</p><p>"
                    + escape(notice)
                    + '</p><a download href="/reports/'
                    + source.name
                    + '">'
                    + t["report_download"]
                    + "</a></div>"
                    + article
                )
            section = (
                "evidence" if is_report else "wiki" if "/wiki/" in target else "docs"
            )
            body = (
                '<div class="docs-layout">'
                + sidebar(lang, target)
                + '<article class="article"><p class="breadcrumb"><a href="/'
                + lang
                + '/">CODEMARK</a> / <a href="/'
                + lang
                + "/"
                + section
                + '/">'
                + t["nav"][("docs", "wiki", "evidence", "downloads").index(section)]
                + "</a></p>"
                + article
                + "</article></div>"
            )
            routes_for_language[target.removeprefix(f"/{lang}/")] = (
                title,
                title + " — CODEMARK",
                body,
                section,
            )
        for route, (title, description, body, section) in routes_for_language.items():
            destination = output / lang / route / "index.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                page(lang, route, title, description, body, data, section),
                encoding="utf-8",
            )
            routes.append(f"/{lang}/{route}")
    # The root is a useful English page without a redirect or a script.
    shutil.copyfile(output / "en/index.html", output / "index.html")
    (output / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: "
        + data["site_url"].rstrip("/")
        + "/sitemap.xml\n",
        encoding="utf-8",
    )
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for route in routes:
        item = ET.SubElement(sitemap, "url")
        ET.SubElement(item, "loc").text = data["site_url"].rstrip("/") + route
    ET.indent(sitemap)
    ET.ElementTree(sitemap).write(
        output / "sitemap.xml", encoding="utf-8", xml_declaration=True
    )
    return len(routes) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate generated local links, markup invariants, and inactive assets",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT,
        help="generated site directory (default: website/public)",
    )
    args = parser.parse_args()
    try:
        count = build(args.output.resolve())
        if args.check:
            checked = check_site(args.output.resolve())
            print(
                f"Site built: {count} pages; checked {checked} HTML documents, local links, unique IDs, one h1 per page, and inactive local assets."
            )
        else:
            print(f"Site built: {count} pages in {args.output.resolve()}")
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        parser.exit(1, f"Website build failed: {error}\n")


if __name__ == "__main__":
    main()
