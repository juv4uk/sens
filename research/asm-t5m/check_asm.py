#!/usr/bin/env python3
"""Локальна перевірка асемблерного T5M: mmap .text, виклик через ctypes,
звірка з scripts/sens_t5_codec.py на реальних словах .sens."""
import ctypes, mmap, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sens_t5_codec as codec

BIN = (HERE / "t5m_pack.bin").read_bytes()
mem = mmap.mmap(-1, len(BIN), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
mem.write(BIN)
addr = ctypes.addressof(ctypes.c_char.from_buffer(mem))

PACK = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p)(addr + 0x00)
UNPACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p)(addr + 0x46)


def words_to_trits(words):
    trits = []
    for i, w in enumerate(words):
        if i:
            trits.append(2)
        trits.extend(int(c) for c in w)
    while len(trits) % 15:
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


src = (ROOT / "tests" / "semantic" / "core-fourth-d3-d5-law.sens").read_bytes()
words = codec.decode_t5m_bytes(src)
trits = words_to_trits(words)
n = len(trits)
print(f"слів={len(words)} тритів={n} груп={n//15}")

tin = ctypes.create_string_buffer(bytes(trits), n)
out = ctypes.create_string_buffer(n // 15 * 3)
nb = PACK(tin, n, out)
got = out.raw[:nb]
want = codec.encode_t5m_projection(" ".join(words))
print(f"pack байтів={nb} | == encode_t5m_projection: {got == want}")

tout = ctypes.create_string_buffer(n)
UNPACK(ctypes.create_string_buffer(got), n // 15, tout)
back = list(tout.raw[:n])
print(f"unpack == трити: {back == trits}")
print(f"unpack → слова == початкові: {trits_to_words(back) == words}")
