"""CPython-бік бенчмарку агентських повідомлень.

  python3 py_agent.py FORM RECORDS MODE [EXPECTED]
    FORM = src     — текст Python: compile + exec;
           marshal — заздалегідь скомпільований байткод (marshal): loads + exec;
           json    — AST у JSON + маленький інтерпретатор на Python.
    MODE = base | decode | full (як у agent_bench.rs).

Кожне повідомлення присвоює відповідь змінній `result` (src/marshal) або є
виразом (json). Простір імен один на весь потік — як довгоживуча сесія агента.
"""
import json
import marshal
import struct
import sys


def records(data):
    out, at = [], 0
    while at < len(data):
        (length,) = struct.unpack_from("<I", data, at)
        out.append(data[at + 4:at + 4 + length])
        at += 4 + length
    return out


def json_eval(node, env, defs):
    if isinstance(node, int):
        return node
    if isinstance(node, str):
        return env[node]
    op = node[0]
    if op == "+":
        return json_eval(node[1], env, defs) + json_eval(node[2], env, defs)
    if op == "-":
        return json_eval(node[1], env, defs) - json_eval(node[2], env, defs)
    if op == "*":
        return json_eval(node[1], env, defs) * json_eval(node[2], env, defs)
    if op == "if-eq":
        if json_eval(node[1], env, defs) == json_eval(node[2], env, defs):
            return json_eval(node[3], env, defs)
        return json_eval(node[4], env, defs)
    if op == "let":
        inner = dict(env)
        for name, value in node[1]:
            inner[name] = json_eval(value, env, defs)
        return json_eval(node[2], inner, defs)
    if op == "nth":
        return node[1][node[2]]
    if op == "def":
        defs[node[1]] = (node[2], node[3])
        return json_eval(node[4], env, defs)
    if op == "call":
        params, body = defs[node[1]]
        inner = dict(env)
        for name, value in zip(params, node[2:]):
            inner[name] = json_eval(value, env, defs)
        return json_eval(body, inner, defs)
    raise ValueError(op)


def main():
    form, path, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(path, "rb") as fh:
        messages = records(fh.read())
    if mode == "base":
        return 0

    def load(message):
        if form == "src":
            return compile(message, "<message>", "exec")
        if form == "marshal":
            return marshal.loads(message)
        return json.loads(message)

    if mode == "decode":
        for message in messages:
            load(message)
        return 0

    expected = None
    if len(sys.argv) > 4:
        with open(sys.argv[4], encoding="utf-8") as fh:
            expected = fh.read().splitlines()
    namespace, defs = {}, {}
    for index, message in enumerate(messages):
        program = load(message)
        if form == "json":
            got = json_eval(program, {}, defs)
        else:
            exec(program, namespace)
            got = namespace["result"]
        if expected is not None and str(got) != expected[index]:
            print(f"message {index}: expected {expected[index]}, got {got}", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    sys.exit(main())
