#!/usr/bin/env python3
"""Вичерпна перевірка всіх тритових рядків 0..12, без семантичних припущень D2.

НЕ ратифікація і НЕ канонічний фізичний .sens/T5.
Усі перевірки діють під python -O; таблиця є відтворюваним свідченням.
"""
import itertools
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import носій as кодер


def вимагати(ok, explanation):
    if not ok:
        raise RuntimeError(explanation)


def має_відхилити(action, explanation):
    try:
        action()
    except ValueError:
        return
    raise RuntimeError(explanation)


def рамка(т):
    n = len(т)
    if n == 5:
        return т == (1, 0, 2, 0, 1)
    return (
        n >= 7 and т[:3] == (1, 0, 2) and т[-3:] == (2, 0, 1)
        and all(not (a == b == 2) for a, b in zip(т, т[1:]))
    )


def слова_за_незалежним_правилом(т):
    if not рамка(т):
        return None
    words = "".join(map(str, т)).split("2")
    if words[0] != "10" or words[-1] != "01":
        return None
    depth = 0
    for i, word in enumerate(words):
        if not (1 <= len(word) <= 9 and all(bit in "01" for bit in word)):
            return None
        if word == "10":
            depth += 1
        elif word == "01":
            depth -= 1
            if depth < 0 or (depth == 0 and i != len(words) - 1):
                return None
        elif depth <= 0:
            return None
    return words if depth == 0 else None


def відтворити():
    table = []
    seen_physical = {}
    one_byte = {}
    for n in range(13):
        counted, admitted = 0, 0
        for trits in itertools.product((0, 1, 2), repeat=n):
            if not рамка(trits):
                має_відхилити(
                    lambda t=trits: кодер.ранг(t),
                    f"Ранг прийняв нерамковий рядок n={n}: {trits}",
                )
                continue
            expected_rank = counted
            counted += 1
            rank = кодер.ранг(trits)
            вимагати(rank == expected_rank, f"Лексикографічний ранг n={n}: {rank}")
            вимагати(кодер.за_рангом(n, rank) == trits,
                     f"Незворотний ранг n={n}: {rank}")
            words = слова_за_незалежним_правилом(trits)
            if words is None:
                invalid_words = "".join(map(str, trits)).split("2")
                має_відхилити(
                    lambda w=invalid_words: кодер.упакувати(w),
                    f"Прийнято погану структуру n={n}: {trits}",
                )
                continue
            admitted += 1
            physical = кодер.упакувати(words)
            вимагати(кодер.розпакувати(physical) == words,
                     f"Побайтовий roundtrip зламаний n={n}: {trits}")
            вимагати(len(physical) <= кодер.байтів_т5(words),
                     f"Більше байтів за T5 n={n}: {trits}")
            вимагати(physical not in seen_physical,
                     f"Колізія {physical.hex()}: {trits}")
            seen_physical[physical] = trits
            if len(physical) == 1:
                one_byte[physical] = words
        вимагати(counted == кодер.місткість(n),
                 f"Місткість не збіглася для n={n}")
        table.append({
            "тритів": n,
            "усіх_трійкових_рядків": 3 ** n,
            "рамок_без_22": counted,
            "прийнято_обмеженою_перевіркою_слів": admitted,
            "відхилено_серед_рамок": counted - admitted,
        })

    for value in range(256):
        raw = bytes([value])
        if raw in one_byte:
            вимагати(кодер.розпакувати(raw) == one_byte[raw],
                     f"Неоднозначний 1-байтовий код {value}")
        else:
            має_відхилити(lambda b=raw: кодер.розпакувати(b),
                           f"Прийнято чужий 1-байтовий код {value}")

    source = subprocess.run(
        ["git", "hash-object", str(HERE / "носій.py")],
        cwd=HERE, text=True, capture_output=True, check=True,
    ).stdout.strip()
    framed = sum(item["рамок_без_22"] for item in table)
    accepted = sum(item["прийнято_обмеженою_перевіркою_слів"] for item in table)
    total = sum(item["усіх_трійкових_рядків"] for item in table)
    return {
        "схема": "ramka3-exhaustive-trits-0-12/v1",
        "статус": "RESEARCH-ONLY; NOT-T5; NOT-FULL-D2",
        "обсяг": "Усі послідовності алфавіту 0,1,2 довжини від 0 до 12 включно",
        "git_blob_кодера": source,
        "таблиця": table,
        "разом": {
            "перебрано": total,
            "рамок_без_22": framed,
            "прийнято_кодером": accepted,
            "відхилено_структурно": total - framed,
            "відхилено_серед_рамок": framed - accepted,
            "однобайтових_фізичних_кодів_перевірено": 256,
        },
        "межа_доказу": (
            "Доведено лише однозначність rank/unrank і pack/unpack у заявленому "
            "обмеженому дослідному синтаксисі; жодної повної D2-семантики чи "
            "потокової рамки/EOF/CRC тут не доведено."
        ),
    }


if __name__ == "__main__":
    proof = відтворити()
    expected_text = json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    source = HERE / "свідчення_до12.json"
    if len(sys.argv) == 2 and sys.argv[1] == "--write":
        source.write_text(expected_text, encoding="utf-8")
    else:
        вимагати(source.read_text(encoding="utf-8") == expected_text,
                 "Застаріла таблиця свідчень: відтворити --write та перевірити diff")
    print(f"РАМКА-3: PASS {proof['разом']['перебрано']} усіх тритових рядків; "
          f"{proof['разом']['рамок_без_22']} рамок; "
          f"{proof['разом']['прийнято_кодером']} оборотних кодів; "
          "256 однобайтових фізичних кодів")
