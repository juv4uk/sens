#!/usr/bin/env python3
"""Локальна перевірка асемблерного T5M: mmap .text, виклик через ctypes,
звірка з scripts/sens_t5_t5m_codec.py на реальних словах .sens."""
import ctypes
import mmap
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sens_t5_t5m_codec as codec

with tempfile.TemporaryDirectory(prefix="sens-t5m-asm-") as temp_name:
    temp = pathlib.Path(temp_name)
    obj = temp / "t5m_pack.o"
    binary = temp / "t5m_pack.bin"
    subprocess.run(["as", "--64", "-o", str(obj), str(HERE / "t5m_pack.S")], check=True)
    subprocess.run(["objcopy", "--dump-section", f".text={binary}", str(obj)], check=True)
    symbol_lines = subprocess.run(["nm", "-n", str(obj)], check=True,
                                  capture_output=True, text=True).stdout.splitlines()
    symbols = {
        fields[-1]: int(fields[0], 16)
        for line in symbol_lines
        if len(fields := line.split()) >= 3
    }
    BIN = binary.read_bytes()
    PACK_OFFSET = symbols["sens_t5m_pack"]
    UNPACK_OFFSET = symbols["sens_t5m_unpack"]

mem = mmap.mmap(-1, len(BIN), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
mem.write(BIN)
addr = ctypes.addressof(ctypes.c_char.from_buffer(mem))

PACK = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p)(addr + PACK_OFFSET)
UNPACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p)(addr + UNPACK_OFFSET)


def words_to_trits(words):
    trits = []
    for i, w in enumerate(words):
        if i:
            trits.append(2)
        trits.extend(int(c) for c in w)
    while len(trits) % 5:
        trits.append(2)
    return trits


def trits_to_words(trits):
    words, cur = [], []
    for t in trits:
        if t == 2:
            if cur:
                words.append("".join(map(str, cur)))
            cur = []
        else:
            cur.append(t)
    if cur:
        words.append("".join(map(str, cur)))
    return words


src = (ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.sens").read_bytes()
words = codec.decode_t5m_bytes(src)
trits = words_to_trits(words)
n = len(trits)
print(f"слів={len(words)} тритів={n} груп={n//5}")

tin = ctypes.create_string_buffer(bytes(trits), n)
out = ctypes.create_string_buffer(n // 5)
nb = PACK(tin, n, out)
got = out.raw[:nb]
want = codec.encode_t5m_projection(" ".join(words))
print(f"pack байтів={nb} | == T5M 5-тритів/байт: {got == want}")

tout = ctypes.create_string_buffer(n)
UNPACK(ctypes.create_string_buffer(got), nb, tout)
back = list(tout.raw[:n])
print(f"unpack == трити: {back == trits}")
print(f"unpack → слова == початкові: {trits_to_words(back) == words}")
