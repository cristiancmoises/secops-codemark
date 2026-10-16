"""Conservative lexical similarity, never a legal authorship verdict.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import hashlib
import keyword
import re

KEYWORDS = set(keyword.kwlist) | {
    "define",
    "lambda",
    "let",
    "let*",
    "letrec",
    "if",
    "cond",
    "begin",
    "set!",
    "quote",
    "quasiquote",
    "unquote",
    "define-module",
    "use-modules",
    "public",
    "private",
    "protected",
    "static",
    "const",
    "function",
    "return",
    "for",
    "while",
    "do",
    "switch",
    "case",
    "break",
    "continue",
    "class",
    "extends",
    "import",
    "export",
    "from",
    "default",
    "new",
    "this",
    "true",
    "false",
    "null",
    "undefined",
    "var",
    "void",
    "int",
    "long",
    "float",
    "double",
    "char",
    "bool",
    "struct",
    "enum",
    "typedef",
    "sizeof",
    "include",
    "defmodule",
    "fn",
    "mut",
    "pub",
    "impl",
    "trait",
    "use",
    "mod",
    "match",
    "loop",
    "self",
    "async",
    "await",
    "try",
    "catch",
    "finally",
    "throw",
    "throws",
    "package",
    "interface",
    "implements",
    "final",
    "end",
    "then",
    "else",
    "elseif",
    "local",
    "in",
    "select",
    "where",
    "insert",
    "update",
    "delete",
    "create",
    "table",
    "and",
    "or",
    "not",
}
NUMBER = re.compile(r"(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?)")
NAME = re.compile(r"[A-Za-z_$][\w$]*")
SCHEME_NAME = re.compile(r"[A-Za-z_$!%&*+./:<=>?@^~\-][\w$!%&*+./:<=>?@^~\-]*")
OPS = re.compile(
    r"===|!==|>>>|<<=|>>=|==|!=|<=|>=|=>|->|\+=|-=|\*=|/=|&&|\|\||\+\+|--|<<|>>|\*\*|::"
)


def tokens(text, family):
    """Ignore names/comments, preserve literals, keywords and operations."""
    output = []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace() or char == "\ufeff":
            i += 1
            continue
        line_comment = text.startswith("//", i) and family in ("slash", "block")
        line_comment |= char == "#" and family == "hash"
        line_comment |= char == ";" and family == "scheme"
        line_comment |= text.startswith("--", i) and family == "dash"
        if text.startswith("#!", i) and i == 0:
            line_comment = True
        if line_comment:
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
            continue
        pairs = [("/*", "*/")] if family in ("slash", "block") else []
        if family == "markup":
            pairs.append(("<!--", "-->"))
        handled = False
        for opening, closing in pairs:
            if text.startswith(opening, i):
                end = text.find(closing, i + len(opening))
                i = len(text) if end < 0 else end + len(closing)
                handled = True
                break
        if handled:
            continue
        if family == "scheme" and text.startswith("#|", i):
            depth = 1
            i += 2
            while i < len(text) and depth:
                if text.startswith("#|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            continue
        if char in ('"', "'", "`") and not (char == "'" and family == "scheme"):
            start = i
            delim = char * 3 if text.startswith(char * 3, i) and char != "`" else char
            i += len(delim)
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                elif text.startswith(delim, i):
                    i += len(delim)
                    break
                else:
                    i += 1
            output.append("str:" + text[start:i])
            continue
        match = NUMBER.match(text, i)
        if match:
            output.append("num:" + match.group())
            i = match.end()
            continue
        match = (SCHEME_NAME if family == "scheme" else NAME).match(text, i)
        if match:
            word = match.group()
            output.append(
                word
                if word in KEYWORDS or word in ("+", "-", "*", "/", "=", "<", ">")
                else "id"
            )
            i = match.end()
            continue
        match = OPS.match(text, i)
        output.append(match.group() if match else char)
        i = match.end() if match else i + 1
    return output


def fingerprint(text, family):
    stream = tokens(text, family)
    normalized = hashlib.sha256("\x00".join(stream).encode("utf-8")).hexdigest()
    hashes = set()
    for i in range(max(0, len(stream) - 4)):
        gram = "\x00".join(stream[i : i + 5]).encode("utf-8")
        hashes.add(hashlib.sha256(gram).hexdigest()[:16])
    return {
        "normalized_sha256": normalized,
        "tokens": len(stream),
        "sketch": sorted(hashes)[:256],
    }


def similarity(first, second):
    a, b = set(first), set(second)
    return len(a & b) / len(a | b) if a and b else 0.0
