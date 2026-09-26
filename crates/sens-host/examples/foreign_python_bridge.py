#!/usr/bin/env python
"""Minimal, auditable Python-side adapter for the transport
proof-of-concept in foreign_python_probe.rs (docs/FOREIGN-RUNTIME-PROTOCOL-DESIGN-2026-09-11.md).

Not "the implementation" of anything -- a small, fixed script proving
the transport mechanism only, the same role asm/nucleus.s plays for
wsm-my-lisp: a minimal, auditable adapter, not a general Python bridge.

Protocol (line-based, stdin -> stdout, one request per line):
  call <module> <function> <arg>
    -> ok <result>
    -> err <message>

Deliberately minimal: one module, one function, one numeric argument --
proving only "can a persistent subprocess receive a request and return
a real computed result," not the full call/import/handle protocol the
design document describes. importlib is used generically (not
hardcoded to `math`) so the same script already proves "any module,
any zero-or-one-arg function," a slightly stronger proof than the
single hardcoded case would have been, at no extra design cost.
"""
import sys
import importlib


def main():
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split(" ")
        try:
            if parts[0] != "call" or len(parts) < 3:
                raise ValueError(f"malformed request: {line!r}")
            module_name, function_name = parts[1], parts[2]
            args = [float(a) for a in parts[3:]]
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            result = function(*args)
            print(f"ok {result}", flush=True)
        except Exception as error:  # noqa: BLE001 -- deliberately broad: any
            # foreign exception must be reported back, not crash the bridge.
            print(f"err {error}", flush=True)


if __name__ == "__main__":
    main()
