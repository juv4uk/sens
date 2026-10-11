#!/usr/bin/env python3
"""Golden corpus generator for the Lisp-owned x86-64 encoder.

The reference bytes are produced by two *independent* external assemblers,
GNU `as` (GAS) and `nasm`, then extracted with `objcopy -O binary`. Both must
agree; disagreement is a hard error, not a vote. The frozen result is written
to `crates/sens/tests/fixtures/machine-asm-corpus.json` together with a
SHA-256 over the canonical byte corpus, so the corpus is pinned and can be
re-checked without the assemblers.

This is the frozen external witness behind
`crates/sens/tests/machine_asm_differential.rs` (which additionally compares
the live Lisp encoder to these bytes).

Usage:
    python3 scripts/gen-machine-asm-fixtures.py [--out PATH] [--check]

    --check   regenerate and fail if the on-disk fixture drifted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "crates" / "sens" / "tests" / "fixtures" / "machine-asm-corpus.json"

# name, Lisp admitted form, GAS (intel syntax) body, NASM body.
# Mirrors the `cases` table in machine_asm_differential.rs; keep in sync.
CASES: tuple[tuple[str, str, str, str], ...] = (
    ("add_rax_rcx", "(add-r64-r64 rax rcx)", "add rax, rcx", "add rax, rcx"),
    ("add_r8_r9", "(add-r64-r64 r8 r9)", "add r8, r9", "add r8, r9"),
    ("store_rdi_disp8_rax", "(mov-mem-disp8-r64 rdi 8 rax)",
     "mov QWORD PTR [rdi + 8], rax", "mov qword [rdi + 8], rax"),
    ("load_rax_rdi_disp8", "(mov-r64-mem-disp8 rax rdi 8)",
     "mov rax, QWORD PTR [rdi + 8]", "mov rax, qword [rdi + 8]"),
    ("store_r12_disp8_r9", "(mov-mem-disp8-r64 r12 8 r9)",
     "mov QWORD PTR [r12 + 8], r9", "mov qword [r12 + 8], r9"),
    ("aesenc_xmm0_xmm1", "(aesenc-xmm-xmm xmm0 xmm1)", "aesenc xmm0, xmm1", "aesenc xmm0, xmm1"),
    ("aesenc_xmm8_xmm9", "(aesenc-xmm-xmm xmm8 xmm9)", "aesenc xmm8, xmm9", "aesenc xmm8, xmm9"),
    ("pclmulqdq_xmm0_xmm1_11", "(pclmulqdq-xmm-xmm-imm8 xmm0 xmm1 17)",
     "pclmulqdq xmm0, xmm1, 0x11", "pclmulqdq xmm0, xmm1, 0x11"),
    ("pclmulqdq_xmm8_xmm9_01", "(pclmulqdq-xmm-xmm-imm8 xmm8 xmm9 1)",
     "pclmulqdq xmm8, xmm9, 0x01", "pclmulqdq xmm8, xmm9, 0x01"),
    ("ret", "(ret)", "ret", "ret"),
)

def _require(tool: str) -> None:
    if shutil.which(tool) is None:
        raise SystemExit(f"required external witness tool {tool!r} is unavailable")


def _version(tool: str) -> str:
    args = ["-v"] if tool == "nasm" else ["--version"]
    out = subprocess.run([tool, *args], capture_output=True, text=True, check=True)
    text = (out.stdout or out.stderr).strip().splitlines()[0]
    return text


def _extract_text(obj: pathlib.Path, binary: pathlib.Path) -> bytes:
    subprocess.run(
        ["objcopy", "-O", "binary", "--only-section=.text", str(obj), str(binary)],
        check=True, capture_output=True,
    )
    return binary.read_bytes()


def gas_bytes(directory: pathlib.Path, name: str, body: str) -> bytes:
    source = directory / f"{name}.gas.s"
    obj = directory / f"{name}.gas.o"
    binary = directory / f"{name}.gas.bin"
    source.write_text(f".intel_syntax noprefix\n.text\n.global witness\nwitness:\n    {body}\n")
    subprocess.run(["as", "--64", "-o", str(obj), str(source)], check=True, capture_output=True)
    return _extract_text(obj, binary)


def nasm_bytes(directory: pathlib.Path, name: str, body: str) -> bytes:
    source = directory / f"{name}.nasm.asm"
    obj = directory / f"{name}.nasm.o"
    binary = directory / f"{name}.nasm.bin"
    source.write_text(f"bits 64\nsection .text\nglobal witness\nwitness:\n    {body}\n")
    subprocess.run(["nasm", "-f", "elf64", "-o", str(obj), str(source)], check=True, capture_output=True)
    return _extract_text(obj, binary)


def _corpus_digest(cases: list[dict]) -> str:
    digest = hashlib.sha256()
    for case in cases:
        digest.update(case["name"].encode())
        digest.update(b"\x00")
        digest.update(bytes.fromhex(case["bytes_hex"]))
        digest.update(b"\n")
    return digest.hexdigest()


def build_corpus() -> dict:
    for tool in ("as", "nasm", "objcopy"):
        _require(tool)
    cases = []
    with tempfile.TemporaryDirectory(prefix="sens-golden-corpus-") as tmp:
        directory = pathlib.Path(tmp)
        for name, form, gas_src, nasm_src in CASES:
            gas = gas_bytes(directory, name, gas_src)
            nasm = nasm_bytes(directory, name, nasm_src)
            if gas != nasm:
                raise SystemExit(
                    f"independent assemblers disagree for {name}: gas={gas.hex()} nasm={nasm.hex()}"
                )
            cases.append({
                "name": name,
                "form": form,
                "gas": gas_src,
                "nasm": nasm_src,
                "bytes_hex": gas.hex(),
                "sha256": hashlib.sha256(gas).hexdigest(),
            })
    return {
        "schema": "sens.machine-asm-corpus/v1",
        "producers": {
            "gas": _version("as"),
            "nasm": _version("nasm"),
            "objcopy": _version("objcopy"),
        },
        "corpus_sha256": _corpus_digest(cases),
        "cases": cases,
    }


def render(corpus: dict) -> str:
    return json.dumps(corpus, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Golden x86-64 encoder corpus generator.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check", action="store_true", help="fail if the on-disk fixture drifted")
    args = ap.parse_args()

    rendered = render(build_corpus())
    out = pathlib.Path(args.out)
    if args.check:
        if not out.is_file():
            raise SystemExit(f"golden corpus fixture missing: {out}")
        if out.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"golden corpus fixture drifted from live assemblers: {out}")
        corpus = json.loads(rendered)
        print(f"machine-asm-corpus: OK ({len(corpus['cases'])} cases, corpus_sha256={corpus['corpus_sha256']})")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    corpus = json.loads(rendered)
    print(f"wrote {out}")
    print(f"corpus_sha256: {corpus['corpus_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
