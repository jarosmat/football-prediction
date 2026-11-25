"""Generate Markdown API docs from Google-style docstrings using griffe.

Pipeline: griffe parses each docstring (google style) into structured sections
(parameters, returns, raises, attributes, examples), then this script formats
them as Markdown. Docstrings that do not parse into sections are emitted as-is.

Options come from (highest precedence first):
    1. CLI flags            --src, --output, --modules, --format
    2. YAML config file     --config PATH, or api-docs.yaml next to this script if present
    3. built-in defaults    src/ -> docs/API.md, all modules under src, format "list"

Config file format (paths in the config are relative to the config file):
    src: src
    output: docs/API.md
    format: list        # "list" or "table"
    modules: []         # empty = auto-discover all modules under src

Examples:
    python3 generate_api_docs.py
    python3 generate_api_docs.py --config my-config.yaml
    python3 generate_api_docs.py --format table -o /tmp/api.md
    python3 generate_api_docs.py --modules models.window_model -o /tmp/api.md
"""

import argparse
import shlex
import sys
from pathlib import Path

from griffe import load

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "api-docs.yaml"
CONFIG_KEYS = {"src", "output", "modules", "format"}
FORMATS = ("list", "table")


def discover_modules(src: Path) -> list[str]:
    """Dotted paths of all modules under src, including packages (__init__.py)."""
    modules = []
    for py in sorted(src.rglob("*.py")):
        rel = py.relative_to(src).with_suffix("")
        parts = rel.parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            modules.append(".".join(parts))
    return modules


def load_config(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML is required for config files: pip install pyyaml")
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        sys.exit(f"config {path} must be a mapping of option names to values")
    unknown = set(data) - CONFIG_KEYS
    if unknown:
        print(f"warning: ignoring unknown config keys in {path}: {sorted(unknown)}", file=sys.stderr)
    return data


def signature(fn) -> str:
    """Full call string including the function name, e.g. 'predict(X_data) -> ...'."""
    try:
        return str(fn.signature())
    except Exception:
        params = ", ".join(p.name for p in fn.parameters)
        return f"{fn.name}({params})"


def visible(member) -> bool:
    return not member.is_alias and (not member.name.startswith("_") or member.name == "__init__")


SECTION_TITLES = {
    "DocstringSectionParameters": "Parameters",
    "DocstringSectionReturns": "Returns",
    "DocstringSectionRaises": "Raises",
    "DocstringSectionAttributes": "Attributes",
    "DocstringSectionExamples": "Examples",
    "DocstringSectionWarnings": "Warnings",
    "DocstringSectionNotes": "Notes",
}


def _cell(text) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip()


def _strip_type_prefix(desc, ann) -> str:
    """griffe leaves the type in the returns description; drop it if duplicated."""
    d, a = str(desc or ""), str(ann or "")
    if a and d.startswith(a):
        d = d[len(a):].lstrip(":").strip()
    return d


def _item_lines(label: str, desc) -> list[str]:
    lines = str(desc or "").splitlines()
    first = f"- {label}:" + (f" {lines[0]}" if lines else "")
    return [first] + ["  " + l for l in lines[1:]]


def emit_section(section, out: list[str], fmt: str) -> None:
    name = type(section).__name__
    if name == "DocstringSectionText":
        text = str(section.value).strip()
        if text:
            out.append(text)
            out.append("")
        return

    title = SECTION_TITLES.get(name, name.replace("DocstringSection", ""))
    out.append(f"**{title}:**")
    out.append("")
    value = section.value
    if isinstance(value, str):
        out.append(value.strip())
        out.append("")
        return
    if name == "DocstringSectionExamples":
        items = list(value) if isinstance(value, (list, tuple)) else []
        code = "\n".join(str(getattr(i, "description", "") or i) for i in items).strip()
        if code:
            out.append("```python")
            out.append(code)
            out.append("```")
            out.append("")
        return

    items = list(value or [])
    if fmt == "table" and name in (
        "DocstringSectionParameters",
        "DocstringSectionAttributes",
        "DocstringSectionRaises",
        "DocstringSectionReturns",
    ):
        if name == "DocstringSectionReturns":
            out.append("| Type | Description |")
            out.append("| --- | --- |")
            for it in items:
                ann = str(getattr(it, "annotation", "") or getattr(it, "name", "") or "")
                desc = _strip_type_prefix(getattr(it, "description", ""), ann)
                out.append(f"| `{ann}` | {_cell(desc)} |")
        elif name == "DocstringSectionRaises":
            out.append("| Exception | Description |")
            out.append("| --- | --- |")
            for it in items:
                ann = str(getattr(it, "annotation", "") or "")
                out.append(f"| `{ann}` | {_cell(getattr(it, 'description', ''))} |")
        else:
            out.append("| Name | Type | Description |")
            out.append("| --- | --- | --- |")
            for it in items:
                nm = str(getattr(it, "name", "") or "")
                ann = str(getattr(it, "annotation", "") or "")
                out.append(f"| `{nm}` | `{ann}` | {_cell(getattr(it, 'description', ''))} |")
        out.append("")
        return

    for item in items:
        desc = getattr(item, "description", "") or ""
        ann = str(getattr(item, "annotation", "") or "")
        pname = str(getattr(item, "name", "") or "")
        if name in ("DocstringSectionParameters", "DocstringSectionAttributes"):
            label = f"`{pname}`" + (f" (`{ann}`)" if ann else "")
        elif name == "DocstringSectionReturns":
            label = f"`{ann or pname}`" if (ann or pname) else ""
            desc = _strip_type_prefix(desc, ann or pname)
        elif name == "DocstringSectionRaises":
            label = f"`{ann}`" if ann else ""
        else:
            label = pname
        out.extend(_item_lines(label, desc))
    out.append("")


def emit_docstring(member, out: list[str], fmt: str) -> None:
    ds = member.docstring
    if not ds or not ds.value.strip():
        return
    try:
        sections = ds.parse("google")
    except Exception:
        sections = None
    if sections and any(type(s).__name__ != "DocstringSectionText" for s in sections):
        for s in sections:
            emit_section(s, out, fmt)
    else:
        # no structured sections (plain or dash-list style docstring): emit as-is,
        # inserting a blank line before a list that directly follows a "Section:" line
        lines = ds.value.strip().splitlines()
        prev = ""
        for line in lines:
            if prev and prev.rstrip().endswith(":") and line.lstrip().startswith("- "):
                out.append("")
            out.append(line)
            prev = line
        out.append("")


def emit_function(fn, out: list[str], level: int, fmt: str) -> None:
    h = "#" * level
    out.append(f"{h} `def {fn.name}`")
    out.append("")
    out.append("```python")
    out.append(f"def {signature(fn)}")
    out.append("```")
    out.append("")
    emit_docstring(fn, out, fmt)


def emit_attribute(attr, out: list[str]) -> None:
    value = f" = {attr.value}" if getattr(attr, "value", None) else ""
    annotation = f": {attr.annotation}" if getattr(attr, "annotation", None) else ""
    out.append(f"- `{attr.name}{annotation}{value}`")
    if attr.docstring and attr.docstring.value.strip():
        out.append(f"  {attr.docstring.value.strip()}")
    out.append("")


def emit_class(cls, out: list[str], level: int, fmt: str) -> None:
    h = "#" * level
    bases = f"({', '.join(str(b) for b in cls.bases)})" if cls.bases else ""
    out.append(f"{h} `class {cls.name}{bases}`")
    out.append("")
    out.append("```python")
    out.append(f"class {cls.name}{bases}:")
    init = cls.members.get("__init__")
    if init is not None:
        out.append(f"    def {signature(init)}")
    out.append("```")
    out.append("")
    emit_docstring(cls, out, fmt)

    attrs = [m for m in cls.members.values() if visible(m) and m.is_attribute]
    funcs = [m for m in cls.members.values() if visible(m) and m.is_function]
    if attrs:
        out.append(f"{h}# Attributes")
        out.append("")
        for a in attrs:
            emit_attribute(a, out)
    if funcs:
        out.append(f"{h}# Methods")
        out.append("")

        for f in funcs:
            emit_function(f, out, level + 1, fmt)

    out.append(f"---")


def emit_module(mod, out: list[str], fmt: str) -> bool:
    classes = [m for m in mod.members.values() if visible(m) and m.is_class]
    funcs = [m for m in mod.members.values() if visible(m) and m.is_function]
    attrs = [m for m in mod.members.values() if visible(m) and m.is_attribute]
    has_doc = bool(mod.docstring and mod.docstring.value.strip())
    if not (has_doc or classes or funcs or attrs):
        return False

    out.append(f"## `{mod.path}`")
    out.append("")
    emit_docstring(mod, out, fmt)

    for c in classes:
        emit_class(c, out, 3, fmt)
    for f in funcs:
        emit_function(f, out, 3, fmt)
    if attrs:
        out.append("### Module attributes")
        out.append("")
        for a in attrs:
            emit_attribute(a, out)
    return True


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"YAML config file (default: {DEFAULT_CONFIG.name} next to this script, if it exists)",
    )
    p.add_argument("--src", type=Path, default=None, help="source root searched for modules")
    p.add_argument("-o", "--output", type=Path, default=None, help="output markdown file")
    p.add_argument(
        "--modules",
        nargs="+",
        metavar="MODULE",
        default=None,
        help="dotted module paths to document (default: all modules found under src)",
    )
    p.add_argument(
        "--format",
        choices=FORMATS,
        default=None,
        help='how to render docstring sections: "list" (bullets) or "table" (default: list)',
    )
    return p.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)

    config_path = args.config or (DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else None)
    config = load_config(config_path) if config_path else {}
    config_base = config_path.resolve().parent if config_path else ROOT

    if args.src is not None:
        src = args.src
    elif "src" in config:
        src = config_base / str(config["src"])
    else:
        src = ROOT / "src"

    if args.output is not None:
        output = args.output
    elif "output" in config:
        output = config_base / str(config["output"])
    else:
        output = ROOT / "docs" / "API.md"

    fmt = args.format or str(config.get("format") or "list")
    if fmt not in FORMATS:
        sys.exit(f"unknown format {fmt!r}, expected one of {FORMATS}")

    modules = args.modules or config.get("modules") or None
    if modules is None:
        modules = discover_modules(src)
    modules = [str(m) for m in modules]
    if not modules:
        sys.exit(f"no modules found under {src}")

    out = [
        "# API Reference",
        "Generated from docstrings in Google format."
    ]

    written = 0
    for name in modules:
        try:
            mod = load(name, search_paths=[str(src)])
        except Exception as exc:
            print(f"warning: could not load {name}: {exc}", file=sys.stderr)
            continue
        if emit_module(mod, out, fmt):
            written += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out).rstrip() + "\n")
    print(f"wrote {output} ({written}/{len(modules)} modules, format={fmt})")


if __name__ == "__main__":
    main()
