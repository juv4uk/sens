#!/usr/bin/env python3
"""Бенчмарк «агентських повідомлень»: SENS проти CPython у ніші агентів.

Агент отримує потік N маленьких різних програм байтами й кожну одразу виконує
в одній довгоживучій сесії. Міряється вартість одного повідомлення:
декодування/компіляція + виконання, а також розмір повідомлення в байтах.

Форми:
  sens-fasl  — SENS, двійковий fasl, функція = 1 байт;
  sens-wire  — SENS, компактний формат обміну (без хешу, малі цілі — 1 байт);
  sens-en    — той самий SENS англійським текстом (розбір тексту);
  py-src     — CPython, текст: compile + exec;
  py-marshal — CPython, заздалегідь скомпільований байткод: marshal.loads + exec;
  py-json    — AST у JSON + маленький інтерпретатор на Python.

Мірило — інструкції процесора (valgrind cachegrind), медіана REPS повторів.
Вартість повідомлення = (режим − база `base`) / N; база містить старт процесу,
читання файлу й створення сесії.

  python3 run.py --agent-bench target/release/examples/agent_bench --out DIR [--n 1000] [--reps 3]
"""
import argparse
import json
import marshal
import os
import random
import statistics
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Коди SENS звірені з lib/surface/semantic-registry.lisp.
SENS = {"quote": "00000001", "eq": "00000011", "car": "00000101", "cdr": "00000110",
        "cond": "00000111", "lambda": "00001000", "def": "00001011",
        "+": "00001100", "-": "00001101", "*": "00001110"}
EN = {"quote": "quote", "eq": "eq?", "car": "car", "cdr": "cdr", "cond": "cond",
      "lambda": "lambda", "def": "def", "+": "+", "-": "-", "*": "*"}
FORMS = ["sens-fasl", "sens-wire", "sens-en", "py-src", "py-marshal", "py-json"]


# --- генерація повідомлень: AST -> Lisp / Python / JSON --------------------

def gen_expr(rng, depth, names):
    if depth == 0 or rng.random() < 0.3:
        if names and rng.random() < 0.5:
            return rng.choice(names)
        return rng.randint(0, 9)
    return (rng.choice("+-*"), gen_expr(rng, depth - 1, names), gen_expr(rng, depth - 1, names))


def gen_message(rng, index):
    kind = index % 5
    if kind == 0:
        return ("expr", gen_expr(rng, 3, []))
    if kind == 1:
        a, b = rng.randint(0, 9), rng.randint(0, 9)
        return ("let", [("x", a), ("y", b)], gen_expr(rng, 3, ["x", "y"]))
    if kind == 2:
        return ("if-eq", rng.randint(0, 3), rng.randint(0, 3),
                gen_expr(rng, 2, []), gen_expr(rng, 2, []))
    if kind == 3:
        items = [rng.randint(0, 99) for _ in range(rng.randint(3, 6))]
        return ("nth", items, rng.randint(0, len(items) - 1))
    return ("sum", f"f{index}", rng.randint(5, 15))


def lisp_expr(node, t):
    if isinstance(node, (int, str)):
        return str(node)
    op, a, b = node
    return f"({t[op]} {lisp_expr(a, t)} {lisp_expr(b, t)})"


def lisp(msg, t):
    kind = msg[0]
    if kind == "expr":
        return lisp_expr(msg[1], t)
    if kind == "let":
        params = " ".join(n for n, _ in msg[1])
        args = " ".join(str(v) for _, v in msg[1])
        return f"(({t['lambda']} ({params}) {lisp_expr(msg[2], t)}) {args})"
    if kind == "if-eq":
        _, a, b, then, other = msg
        return (f"({t['cond']} (({t['eq']} {a} {b}) {lisp_expr(then, t)}) "
                f"(t {lisp_expr(other, t)}))")
    if kind == "nth":
        _, items, i = msg
        body = f"({t['quote']} ({' '.join(map(str, items))}))"
        for _ in range(i):
            body = f"({t['cdr']} {body})"
        return f"({t['car']} {body})"
    _, name, n = msg
    return (f"({t['def']} {name} ({t['lambda']} (n) ({t['cond']} (({t['eq']} n 0) 0) "
            f"(t ({t['+']} n ({name} ({t['-']} n 1)))))))\n({name} {n})")


def py_expr(node):
    if isinstance(node, (int, str)):
        return str(node)
    op, a, b = node
    return f"({py_expr(a)} {op} {py_expr(b)})"


def python(msg):
    kind = msg[0]
    if kind == "expr":
        return f"result = {py_expr(msg[1])}\n"
    if kind == "let":
        params = ", ".join(n for n, _ in msg[1])
        args = ", ".join(str(v) for _, v in msg[1])
        return f"result = (lambda {params}: {py_expr(msg[2])})({args})\n"
    if kind == "if-eq":
        _, a, b, then, other = msg
        return f"result = {py_expr(then)} if {a} == {b} else {py_expr(other)}\n"
    if kind == "nth":
        _, items, i = msg
        return f"result = {items}[{i}]\n"
    _, name, n = msg
    return f"def {name}(n):\n    return 0 if n == 0 else n + {name}(n - 1)\nresult = {name}({n})\n"


def json_ast(msg):
    def expr(node):
        if isinstance(node, (int, str)):
            return node
        op, a, b = node
        return [op, expr(a), expr(b)]
    kind = msg[0]
    if kind == "expr":
        return expr(msg[1])
    if kind == "let":
        return ["let", [[n, v] for n, v in msg[1]], expr(msg[2])]
    if kind == "if-eq":
        _, a, b, then, other = msg
        return ["if-eq", a, b, expr(then), expr(other)]
    if kind == "nth":
        return ["nth", msg[1], msg[2]]
    _, name, n = msg
    body = ["if-eq", "n", 0, 0, ["+", "n", ["call", name, ["-", "n", 1]]]]
    return ["def", name, ["n"], body, ["call", name, n]]


def answer(msg):
    namespace = {}
    exec(python(msg), namespace)
    return str(namespace["result"])


def write_records(path, payloads):
    with open(path, "wb") as fh:
        for payload in payloads:
            fh.write(struct.pack("<I", len(payload)))
            fh.write(payload)


# --- вимірювання -------------------------------------------------------------

def command(form, bench, files, mode):
    if form.startswith("sens"):
        engine = {"sens-fasl": "sens", "sens-wire": "wire", "sens-en": "en"}[form]
        return [str(bench), "run", engine,
                str(files[form]), mode]
    return [sys.executable, str(HERE / "py_agent.py"), form.split("-")[1], str(files[form]), mode]


def instructions(cmd):
    out = subprocess.run(["valgrind", "--tool=cachegrind", "--cache-sim=no",
                          "--cachegrind-out-file=/dev/null", *cmd],
                         capture_output=True, text=True, check=True)
    for line in out.stderr.splitlines():
        if "I" in line and "refs:" in line:
            return int(line.split("refs:")[1].strip().replace(",", ""))
    raise RuntimeError(out.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-bench", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    messages = [gen_message(rng, i) for i in range(args.n)]
    (out / "expected.txt").write_text("\n".join(answer(m) for m in messages) + "\n")
    files = {form: out / f"messages-{form}.bin" for form in FORMS}
    write_records(out / "messages-sens-text.bin", [lisp(m, SENS).encode() for m in messages])
    write_records(files["sens-en"], [lisp(m, EN).encode() for m in messages])
    write_records(files["py-src"], [python(m).encode() for m in messages])
    write_records(files["py-marshal"],
                  [marshal.dumps(compile(python(m), "<message>", "exec")) for m in messages])
    write_records(files["py-json"],
                  [json.dumps(json_ast(m), separators=(",", ":")).encode() for m in messages])
    for form, fmt in (("sens-fasl", "fasl"), ("sens-wire", "wire")):
        subprocess.run([str(args.agent_bench), "encode", fmt, str(out / "messages-sens-text.bin"),
                        str(files[form])], check=True)

    # Спершу правильність: кожна відповідь кожної форми звіряється з CPython.
    for form in FORMS:
        subprocess.run(command(form, args.agent_bench, files, "full") + [str(out / "expected.txt")],
                       check=True)

    rows = []
    for form in FORMS:
        for mode in ("base", "decode", "full"):
            for rep in range(1, args.reps + 1):
                count = instructions(command(form, args.agent_bench, files, mode))
                rows.append((form, mode, rep, count))
    with open(out / "instructions.tsv", "w", encoding="utf-8") as fh:
        fh.write("form\tmode\trep\tinstructions\n")
        for row in rows:
            fh.write("\t".join(map(str, row)) + "\n")

    def med(form, mode):
        return statistics.median(c for f, m, _, c in rows if f == form and m == mode)

    n = args.n
    size = {form: (os.path.getsize(files[form]) - 4 * n) / n for form in FORMS}
    lines = [
        "# Агентські повідомлення: SENS проти CPython",
        "",
        f"{n} маленьких різних програм (вирази, lambda, умова, список, рекурсія); "
        "агент отримує кожну байтами й одразу виконує в одній сесії. "
        f"Інструкції процесора (valgrind), медіана {args.reps} повторів. "
        "Усі відповіді звірено з CPython до вимірювання.",
        "",
        "| форма | байт на повідомлення | декодування, інстр./повід. | виконання, інстр./повід. | разом, інстр./повід. | старт процесу, інстр. |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total = {}
    for form in FORMS:
        base, decode, full = med(form, "base"), med(form, "decode"), med(form, "full")
        total[form] = (full - base) / n
        lines.append(f"| {form} | {size[form]:.1f} | {(decode - base) / n:,.0f} | "
                     f"{(full - decode) / n:,.0f} | {total[form]:,.0f} | {base:,.0f} |")
    best = total["sens-fasl"]
    lines += ["", "**Разом на повідомлення, у скільки разів SENS fasl швидший** "
              "(більше 1 — SENS швидший):", ""]
    for form in FORMS[1:]:
        lines.append(f"- проти {form}: ×{total[form] / best:.2f}")
    lines += ["", "Один процес на повідомлення (старт + одне повідомлення):", ""]
    for form in FORMS:
        lines.append(f"- {form}: {med(form, 'base') + total[form]:,.0f} інструкцій")
    report = "\n".join(lines) + "\n"
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

# Benchmark refresh: 2026-10-04 evidence run; no executable semantics changed.
