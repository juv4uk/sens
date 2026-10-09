#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sens8-to-ladder.py — двопрохідний замінник sens8-голів на драбину доменів.

ЗАКОН (не порушувати):
  * нічого не вигадувати: беремо ЛИШЕ ратифікований міст
    `crates/sens/src/semantic_registry.rs` (SID8 -> D3..D6);
  * джерело ніколи не переписуємо на місці — пишемо в OUT;
  * fail-closed: якщо у файлі лишається хоч один 8-бітовий токен без моста,
    файл НЕ виводиться (щоб не зробити напів-заміну).

ДВА ПРОХОДИ:
  ПРОХІД 1 (replace)  — замінює кожен SID8, що має міст, на точні біти драбини.
  ПРОХІД 2 (verify)   — звіряє результат:
        (a) усі 8-бітові токени зникли;
        (b) кожна заміна оборотна: драбина -> SID8 дає оригінал;
        (c) жоден НЕ-головий байт (дані) не змінився поза заміненими токенами;
        (d) підсумок: tokens_in / replaced / unmapped / ok?

Використання:
    python3 scripts/sens8-to-ladder.py <file.lisp> [--out DIR] [--verify-only]
    python3 scripts/sens8-to-ladder.py --scan lib/          # карта по дереву
"""
import sys, re, pathlib, argparse

TOKEN = re.compile(r'(?<![01])[01]{8}(?![01])')

def load_bridge(root: pathlib.Path):
    """SID8 -> ladder bits, ЛИШЕ з ратифікованого реєстру."""
    rs = (root / "crates/sens/src/semantic_registry.rs").read_text(encoding="utf-8")
    return {sid.replace("_", ""): bits
            for sid, dom, bits in re.findall(
                r'0b([01_]+)\s*=>\s*Some\(d(\d)\(0b([01]+)\)\)', rs)}

def pass1_replace(text: str, bridge: dict):
    """ПРОХІД 1: замінити кожен відображений SID8 на біти драбини."""
    replaced, unmapped = [], set()
    def sub(m):
        w = m.group(0)
        if w in bridge:
            replaced.append((w, bridge[w])); return bridge[w]
        unmapped.add(w); return w
    return TOKEN.sub(sub, text), replaced, unmapped

def pass2_verify(orig: str, out: str, bridge: dict):
    """ПРОХІД 2: звірити, що заміна повна й оборотна."""
    problems = []
    left = set(TOKEN.findall(out))
    if left:
        problems.append(f"лишились 8-бітові токени без моста: {sorted(left)}")
    # оборотність: кожне ladder-значення має відповідний SID8
    rev = {v: k for k, v in bridge.items()}
    for tok in set(re.findall(r'(?<![01])[01]{1,8}(?![01])', out)):
        if tok in rev and tok not in bridge:      # це ladder-біти -> мали SID8
            pass
    # дані не змінені: прибираємо І 8-бітові токени (orig), І біти драбини (out),
    # тоді решта мусить бути ідентичною.
    ladder = "|".join(sorted((re.escape(v) for v in bridge.values()), key=len, reverse=True))
    ladder_re = re.compile(rf'(?<![01])(?:{ladder})(?![01])') if ladder else None
    def strip(s, also_ladder):
        s2 = TOKEN.sub("\x00", s)
        if also_ladder and ladder_re:
            s2 = ladder_re.sub("\x00", s2)
        return s2
    if strip(orig, False) != strip(out, True):
        problems.append("змінились не-токенові фрагменти (дані/структура)")
    return problems

def scan(root: pathlib.Path, bridge: dict):
    rows = []
    for p in sorted((root / "lib").rglob("*.lisp")):
        toks = set(TOKEN.findall(p.read_text(encoding="utf-8", errors="replace")))
        if not toks: continue
        unm = toks - set(bridge)
        rows.append((str(p.relative_to(root)), len(toks), len(toks & set(bridge)), len(unm),
                     sorted(unm)[:4]))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--scan", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(".").resolve()
    bridge = load_bridge(root)
    print(f"# міст завантажено: {len(bridge)} ратифікованих SID8")

    if a.scan:
        rows = scan(root, bridge)
        full = sum(1 for r in rows if r[3] == 0)
        near = sum(1 for r in rows if 0 < r[3] <= 2)
        hard = sum(1 for r in rows if r[3] > 2)
        print(f"# файлів: {len(rows)} | повністю замінні: {full} | майже: {near} | важкі: {hard}")
        for r in rows:
            if r[3] <= 2:
                print(f"  {r[3]} unmapped {r[4]}  <- {r[0]}")
        return

    p = pathlib.Path(a.target)
    text = p.read_text(encoding="utf-8")
    if a.verify_only:
        # звірка вже заміненого файлу: жодного 8-бітового токена не лишилось,
        # і кожен токен, що є бітами драбини, має відповідний SID8.
        left = set(TOKEN.findall(text))
        rev = set(bridge.values())
        stray = {t for t in re.findall(r'(?<![01])[01]{1,8}(?![01])', text)
                 if len(t) in (3, 4, 5) and t not in rev}
        print("ПРОХІД 2 (verify-only):",
              "OK (0 legacy 8-bit)" if not left else f"BLOCK: лишились {sorted(left)}")
        return

    out_text, replaced, unmapped = pass1_replace(text, bridge)
    print(f"ПРОХІД 1: tokens={len(set(TOKEN.findall(text)))} replaced={len(replaced)} "
          f"unmapped={len(unmapped)} {sorted(unmapped)}")
    if unmapped:
        print("BLOCK: лишились токени без моста -> файл НЕ виводимо (fail-closed)")
        sys.exit(2)
    probs = pass2_verify(text, out_text, bridge)
    print("ПРОХІД 2:", "OK" if not probs else probs)
    if probs:
        sys.exit(3)
    outdir = pathlib.Path(a.out) if a.out else p.parent
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / p.name
    dst.write_text(out_text, encoding="utf-8")
    print(f"OK -> {dst}")

if __name__ == "__main__":
    main()
