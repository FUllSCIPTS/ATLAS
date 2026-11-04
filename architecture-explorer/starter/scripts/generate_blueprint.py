"""Regenerate the starter's UML inventory from its Python, JavaScript and shell source."""

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "docs/UML_BLUEPRINT.md"
CATALOG = ROOT / "docs/uml-blueprint.json"
EXCLUDED = {".git", ".venv", ".data", "__pycache__", "node_modules"}
SOURCE_DIRS = {"apps", "ml", "packages", "scripts", "services", "tests", "workers"}
JS_FUNCTIONS = {"FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"}
SHELL_FUNCTION = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", re.MULTILINE)


def attr(node):
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return {
            "name": node.target.id, "type": ast.unparse(node.annotation),
            "default": ast.unparse(node.value) if node.value is not None else None,
        }
    return None


def instance_attrs(node):
    fields = {}
    for method in node.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for assignment in ast.walk(method):
            if not isinstance(assignment, (ast.Assign, ast.AnnAssign)):
                continue
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            for target in targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    fields.setdefault(target.attr, {
                        "name": target.attr,
                        "initializer": ast.unparse(assignment.value) if assignment.value is not None else None,
                    })
    return list(fields.values())


def python_inventory(source):
    imports, classes, functions = [], [], []
    tree = ast.parse(source)

    def walk(node, owner="", parent_class=None):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.ClassDef):
            qualified = f"{owner}.{node.name}" if owner else node.name
            entry = {
                "name": qualified, "line": node.lineno,
                "bases": [ast.unparse(base) for base in node.bases],
                "fields": [field for statement in node.body if (field := attr(statement)) is not None],
                "instance_fields": instance_attrs(node), "methods": [],
            }
            classes.append(entry)
            for child in node.body:
                walk(child, qualified, entry)
            return
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = f"{owner}.{node.name}" if owner else node.name
            signature = f"{qualified}({ast.unparse(node.args)})"
            if node.returns is not None:
                signature += " -> " + ast.unparse(node.returns)
            entry = {
                "name": qualified, "signature": signature, "line": node.lineno,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
            }
            (parent_class["methods"] if parent_class is not None else functions).append(entry)
            for child in node.body:
                walk(child, qualified)
            return
        elif isinstance(node, ast.Lambda):
            name = f"<lambda@{node.lineno}:{node.col_offset + 1}>"
            qualified = f"{owner}.{name}" if owner else name
            functions.append({"name": qualified, "signature": f"{qualified}({ast.unparse(node.args)})",
                              "line": node.lineno, "async": False, "decorators": []})
        for child in ast.iter_child_nodes(node):
            walk(child, owner, parent_class)

    walk(tree)
    return {"language": "Python", "imports": list(dict.fromkeys(imports)), "classes": classes, "functions": functions}


def javascript_inventory(path):
    source = path.read_text(encoding="utf-8").encode("utf-16-le")
    command = ["npx", "--yes", "--package", "acorn@8.15.0", "--", "acorn", "--ecma2022", "--locations", "--compact", str(path)]
    tree = json.loads(subprocess.check_output(command, cwd=ROOT, text=True))
    classes, functions = [], []

    def segment(node):
        return source[2 * node["start"]:2 * node["end"]].decode("utf-16-le")

    def callable_name(node, parent):
        if node.get("id"):
            return node["id"]["name"]
        kind = parent.get("type")
        if kind in {"MethodDefinition", "Property", "PropertyDefinition"}:
            return segment(parent["key"])
        if kind == "VariableDeclarator":
            return segment(parent["id"])
        if kind == "AssignmentExpression":
            return segment(parent["left"])
        if kind == "CallExpression":
            label = segment(parent["callee"])
            if parent.get("arguments") and parent["arguments"][0].get("type") == "Literal":
                label += ", " + segment(parent["arguments"][0])
            return f"<callback: {label}>"
        return "<anonymous>"

    def walk(node, owner="", parent=None, parent_class=None):
        if isinstance(node, list):
            for child in node:
                walk(child, owner, parent, parent_class)
        if not isinstance(node, dict) or "type" not in node:
            return
        kind = node["type"]
        if kind in {"ClassDeclaration", "ClassExpression"}:
            name = node["id"]["name"] if node.get("id") else "<anonymous class>"
            qualified = f"{owner}.{name}" if owner else name
            entry = {"name": qualified, "line": node["loc"]["start"]["line"], "bases": [],
                     "fields": [], "instance_fields": [], "methods": []}
            if node.get("superClass"):
                entry["bases"].append(segment(node["superClass"]))
            for member in node["body"]["body"]:
                if member["type"] == "PropertyDefinition":
                    entry["fields"].append({"name": segment(member["key"]), "type": None,
                                            "default": segment(member["value"]) if member.get("value") else None})
            classes.append(entry)
            walk(node["body"], qualified, node, entry)
            return
        if kind in JS_FUNCTIONS:
            name = callable_name(node, parent or {})
            qualified = f"{owner}.{name}" if owner else name
            entry = {
                "name": qualified, "signature": f"{qualified}({', '.join(map(segment, node['params']))})",
                "line": node["loc"]["start"]["line"], "async": node["async"], "decorators": [],
            }
            (parent_class["methods"] if parent_class and parent.get("type") == "MethodDefinition" else functions).append(entry)
            walk(node["body"], qualified, node)
            return
        for child in node.values():
            walk(child, owner, node, parent_class)

    walk(tree)
    return {"language": "JavaScript", "imports": [], "classes": classes, "functions": functions}


def shell_inventory(source):
    entries = [
        {"name": match[1], "signature": f"{match[1]}()", "line": source.count("\n", 0, match.start()) + 1,
         "async": False, "decorators": []}
        for match in SHELL_FUNCTION.finditer(source)
    ]
    return {"language": "Shell", "imports": [], "classes": [], "functions": entries}


def files():
    paths = set()
    for directory, subdirectories, filenames in ROOT.walk():
        subdirectories[:] = [name for name in subdirectories if name not in EXCLUDED]
        for name in filenames:
            path = directory / name
            if path.suffix != ".pyc" and name != ".env":
                paths.add(path.relative_to(ROOT).as_posix())
    paths.add(CATALOG.relative_to(ROOT).as_posix())
    return sorted(paths)


def folder_tree(paths):
    root = {}
    for path in paths:
        directory = root
        parts = path.split("/")
        for parent in parts[:-1]:
            directory = directory.setdefault(parent, {})
        directory[parts[-1]] = None
    lines = ["starter/"]

    def visit(directory, prefix):
        entries = sorted(directory.items(), key=lambda item: (item[1] is None, item[0]))
        for index, (name, child) in enumerate(entries):
            last = index == len(entries) - 1
            lines.append(prefix + ("└── " if last else "├── ") + name + ("/" if child is not None else ""))
            if child is not None:
                visit(child, prefix + ("    " if last else "│   "))

    visit(root, "")
    return "\n".join(lines)


def inventory(paths):
    modules = {}
    hashes = {}
    for name in paths:
        path = ROOT / name
        if path.relative_to(ROOT).parts[0] == "docs" or name in {"README.md", "scripts/generate_blueprint.py"}:
            continue
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.relative_to(ROOT).parts[0] not in SOURCE_DIRS:
            continue
        if path.suffix == ".py":
            modules[name] = python_inventory(path.read_text(encoding="utf-8"))
        elif path.suffix == ".js":
            modules[name] = javascript_inventory(path)
        elif path.suffix == ".sh":
            modules[name] = shell_inventory(path.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "source_root": "architecture-explorer/starter",
        "files": paths,
        "source_sha256": hashes,
        "modules": modules,
    }


def code(value):
    return "`" + value.replace("|", "\\|") + "`"


def symbol_rows(symbols, path, kind):
    for symbol in symbols:
        signature = ("async " if symbol["async"] else "") + symbol["signature"]
        decorators = ", ".join(code(item) for item in symbol["decorators"]) or "—"
        yield f"| {kind} | {code(signature)} | {decorators} | [L{symbol['line']}](../{path}#L{symbol['line']}) |"


def catalog_text(modules):
    lines = []
    for path, module in modules.items():
        lines.extend([f"### {code(path)}", "", f"[Open source](../{path})", ""])
        for cls in module["classes"]:
            bases = ", ".join(map(code, cls["bases"])) or "none"
            lines.extend([f"**Class {code(cls['name'])}** · bases {bases} · [L{cls['line']}](../{path}#L{cls['line']})", ""])
            for field in cls["fields"]:
                annotation = f": {field['type']}" if field["type"] else ""
                default = f" = {field['default']}" if field["default"] is not None else ""
                lines.append(f"- Declared field {code(field['name'] + annotation + default)}")
            for field in cls["instance_fields"]:
                lines.append(f"- Instance attribute {code('self.' + field['name'] + ' = ' + str(field['initializer']))}")
            if cls["fields"] or cls["instance_fields"]:
                lines.append("")
            if not cls["methods"]:
                lines.extend(["This class uses inherited methods.", ""])
        rows = list(symbol_rows(module["functions"], path, "Function"))
        for cls in module["classes"]:
            rows.extend(symbol_rows(cls["methods"], path, "Method"))
        if rows:
            lines.extend(["| Kind | Signature | Decorators | Source |", "| --- | --- | --- | --- |", *rows, ""])
        elif not module["classes"]:
            lines.extend(["Entrypoint script with no declared functions.", ""])
    return "\n".join(lines).rstrip()


def replace_block(document, name, content):
    start, end = f"<!-- BEGIN GENERATED {name} -->", f"<!-- END GENERATED {name} -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise ValueError(f"Expected one {name} marker pair in {MARKDOWN.name}")
    before, rest = document.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n\n{content}\n\n{end}{after}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if a checked-in output is stale")
    args = parser.parse_args()
    data = inventory(files())
    document = MARKDOWN.read_text(encoding="utf-8")
    document = replace_block(document, "TREE", "```text\n" + folder_tree(data["files"]) + "\n```")
    document = replace_block(document, "CATALOG", catalog_text(data["modules"]))
    outputs = {MARKDOWN: document, CATALOG: json.dumps(data, indent=2, ensure_ascii=False) + "\n"}
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"{path.relative_to(ROOT)} is stale. Run python scripts/generate_blueprint.py.\n")
        else:
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
