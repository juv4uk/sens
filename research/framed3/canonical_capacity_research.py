"""Рамка-3: канонічна ємність із законом форми (арність + жива голова + дані QUOTE).

ДОСЛІДНИЦЬКИЙ розрахунок. Не канонічний кодек, не .sens, не runtime.

Що рахує: кількість допустимих програм Рамки-3 (одна зовнішня рамка `10 … 01`)
як функцію трит-довжини n, у трьох режимах:
    structural — поточний структурний лічильник (валідація проти count_inner);
    canonical(консерв.) — ще й закон арності: мертві дерева відпадають;
    canonical(suворе) — + підформа-голова лише LAMBDA (координата UNRESOLVED).

Закон форми (власник, 11.10.2026):
    1. слово-голова: argc = арність (таблиця; COND — з клаузами);
    2. підформа-голова: лише LAMBDA;
    3. аргумент QUOTE — дані: будь-яке дерево, без арностей.

Вартість (Rule B): n = 4 + біти + (слова - 1) = 3 + біти + слова; n = 4 для порожнього.
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])

QUOTE, ATOM, CDR, CAR, EQ, COND, EMPTY, CONS = (
    "001", "010", "011", "100", "101", "110", "000", "111")
# Доведені фіксовані арності (semantic_redundancy_research.py).
FIXED_ARITY = {QUOTE: 1, ATOM: 1, CDR: 1, CAR: 1, EQ: 2, CONS: 2}
# LAMBDA у чинній D3 таблиці не ратифіковано.
MAX_INNER_BITS = 20

# ---------------------------------------------------------------- категорії слів

# Кожна категорія: (назва, кратність). Ширина окремо — вона дає вартість у бітах.
# 'w1u'      — payload ширини 1 без доведеної арності (2 слова: 0, 1)
# 'ar1c'     — payload з арністю 1, аргументи-код (ATOM, CDR, CAR)
# 'ar1d'     — payload з арністю 1, аргумент-дані (QUOTE)
# 'ar2'      — payload з арністю 2 (EQ, CONS)
# 'un'       — payload без доведеної арності (000, 110, D4–D9)
# 'sep' 'close' 'open' 'dot' — D2 структурні слова
def categories(width: int):
    if width == 1:
        return [("un", 2)]
    if width == 2:
        # D2 структурні слова: 00 sep, 01 close, 10 open, 11 dot
        return [("sep", 1), ("close", 1), ("open", 1), ("dot", 1)]
    if width == 3:
        return [("ar1c", 3), ("ar1d", 1), ("ar2", 2), ("un", 2)]
    return [("un", 1 << width)]


# ---------------------------------------------------------------- кадр стека

HEAD, ARGS, DTAIL, DCLOSE = 0, 1, 2, 3
# кадр: (kind, phase, required, heads, seen, argctx)
#   kind: 0 = code (перевіряється), 1 = data (без перевірок)
#   phase: HEAD очікує голову; ARGS — аргументи; DTAIL — хвіст після крапки;
#          DCLOSE — чекає на закриття
#   required: -1 = невідомо (перевірки немає), інакше точне число аргументів
#   heads: скільки виразів уже в списку (правило крапки)
#   seen:  скільки аргументів після голови
#   argctx: 0 = код, 1 = дані (контекст аргументів цього списку)
ROOT = (0, HEAD, -1, 0, 0, 0)


def close_frame(parent: tuple) -> tuple | None:
    """Закриття дочірнього списку: батько рахує цей вираз."""
    if not parent:
        return ()  # корінь закрився — програма завершена
    kind, phase, required, heads, seen, argctx = parent[-1]
    rest = parent[:-1]
    if phase == HEAD:
        # дочірній список був головою: арність голови невідома без LAMBDA
        return rest + ((kind, ARGS, -1, 1, 0, argctx),)
    if phase == ARGS:
        return rest + ((kind, ARGS, required, heads + 1, seen + 1, argctx),)
    if phase == DTAIL:
        return rest + ((kind, DCLOSE, required, heads + 1, seen + 1, argctx),)
    return None


def step(stack: tuple, category: str, *, strict: bool) -> tuple | None:
    """Один крок читання одного слова; None — недопустимо."""
    top = stack[-1]
    kind, phase, required, heads, seen, argctx = top
    parent = stack[:-1]

    if category == "sep":
        return stack

    if category == "close":
        if phase == HEAD and heads == 0:
            # Порожній D2-кадр не є програмою: `()` — це D3-слово `000`.
            # У даних (kind=1) структурна валідність лишається.
            if kind == 1:
                return close_frame(parent)
            return None
        if phase == ARGS:
            if kind == 1 or required == -1 or seen == required:
                return close_frame(parent)
            return None
        if phase == DCLOSE:
            return close_frame(parent)
        return None

    if category == "dot":
        if phase in (HEAD, ARGS) and heads >= 1:
            return parent + ((kind, DTAIL, required, heads, seen, argctx),)
        return None

    if category == "open":
        if phase == DCLOSE:
            return None
        child_kind = kind if kind == 1 else argctx
        child = (child_kind, HEAD, -1, 0, 0, 1)
        if phase == HEAD and kind == 0 and strict:
            return None  # підформа-голова потребує LAMBDA
        return parent + ((kind, phase, required, heads, seen, argctx), child)

    # payload
    if kind == 1:
        # дані: структурно, без арностей
        if phase == HEAD:
            return parent + ((kind, ARGS, -1, 1, 0, argctx),)
        if phase == ARGS:
            return parent + ((kind, ARGS, required, heads + 1, seen + 1, argctx),)
        if phase == DTAIL:
            return parent + ((kind, DCLOSE, -1, heads + 1, seen + 1, argctx),)
        return None

    if phase == HEAD:
        if category == "ar1c":
            return parent + ((kind, ARGS, 1, 1, 0, 0),)
        if category == "ar1d":
            return parent + ((kind, ARGS, 1, 1, 0, 1),)
        if category == "ar2":
            return parent + ((kind, ARGS, 2, 1, 0, 0),)
        return parent + ((kind, ARGS, -1, 1, 0, 0),)  # невідома голова
    if phase == ARGS:
        return parent + ((kind, ARGS, required, heads + 1, seen + 1, argctx),)
    if phase == DTAIL:
        return parent + ((kind, DCLOSE, required, heads + 1, seen + 1, argctx),)
    return None


# ---------------------------------------------------------------- основний DP

def root_closable(frame: tuple, mode: str) -> bool:
    """Чи може кореневий кадр закритися безкоштовним зовнішнім `01`."""
    kind, phase, required, heads, seen, argctx = frame
    if phase == DCLOSE:
        return True
    if phase == ARGS:
        if mode == "structural":
            return True
        return required == -1 or seen == required
    if phase == HEAD and heads == 0:
        # Порожній кадр: структурно допустимо, канонічно ні (`()` = `000`).
        return mode == "structural"
    return False


def counts(max_bits: int, mode: str):
    """mode: 'structural' | 'canonical' | 'strict'.

    Повертає dict (біти, слова) → кількість програм. Зовнішнє `10`/`01`
    безкоштовні (вони поза тілом); вкладені `01` — звичайні внутрішні слова.
    """
    table: dict[tuple[int, int], dict] = defaultdict(dict)
    accepted: dict[tuple[int, int], int] = defaultdict(int)
    table[(0, 0)][(ROOT,)] = 1
    for bits in range(max_bits + 1):
        for words in range(max_bits + 2):
            state = table.get((bits, words))
            if not state:
                continue
            for stack, count in list(state.items()):
                if len(stack) == 1 and root_closable(stack[0], mode):
                    accepted[(bits, words)] += count
                else:
                    accepted.setdefault((bits, words), accepted.get((bits, words), 0))
                if not stack:
                    continue
                for width in (1, 2, *range(3, 10)):
                    if bits + width > max_bits:
                        continue
                    for category, multiplicity in categories(width):
                        if category == "close" and len(stack) == 1:
                            continue  # зовнішнє `01` безкоштовне, кінець програми
                        result = apply(stack, category, mode)
                        if result is None:
                            continue
                        cell = table[(bits + width, words + 1)]
                        cell[result] = cell.get(result, 0) + count * multiplicity
    return dict(accepted)


def apply(stack: tuple, category: str, mode: str):
    if mode == "structural":
        return step_struct(stack, category)
    strict = mode == "strict"
    return step(stack, category, strict=strict)


def step_struct(stack: tuple, category: str) -> tuple | None:
    """Структурний автомат без перевірки арності (еквівалент count_inner)."""
    top = stack[-1]
    kind, phase, required, heads, seen, argctx = top
    parent = stack[:-1]
    if category == "sep":
        return stack
    if category == "close":
        if phase in (ARGS, DCLOSE) or (phase == HEAD and heads == 0):
            return close_frame(parent)
        return None
    if category == "dot":
        if phase in (HEAD, ARGS) and heads >= 1:
            return parent + ((kind, DTAIL, required, heads, seen, argctx),)
        return None
    if category == "open":
        if phase == DCLOSE:
            return None
        child = (kind, HEAD, -1, 0, 0, argctx)
        return parent + ((kind, phase, required, heads, seen, argctx), child)
    # payload
    if phase == HEAD:
        return parent + ((kind, ARGS, -1, 1, 0, argctx),)
    if phase == ARGS:
        return parent + ((kind, ARGS, required, heads + 1, seen + 1, argctx),)
    if phase == DTAIL:
        return parent + ((kind, DCLOSE, required, heads + 1, seen + 1, argctx),)
    return None


# ---------------------------------------------------------------- звіт

def trit_length(bits: int, words: int) -> int:
    """n = 4 порожнє тіло, інакше 3 + біти + слова."""
    if bits == 0 and words == 0:
        return 4
    return 3 + bits + words


def by_trit_length(mode: str, max_bits: int = 16) -> dict[int, int]:
    distribution = counts(max_bits, mode)
    out: dict[int, int] = defaultdict(int)
    for (bits, words), value in distribution.items():
        out[trit_length(bits, words)] += value
    return dict(out)


def main() -> None:
    from canonical_d2_rank_research import count_inner

    max_bits = 14
    print("== Валідація структурної моделі проти count_inner ==")
    print(f"{'біти':>5} {'структ':>10} {'count_inner':>12} {'каноніч':>10} "
          f"{'suворе':>10}  {'зекономлено %':>14}")
    for bits in range(0, max_bits + 1):
        struct = counts(bits, "structural")
        canon = counts(bits, "canonical")
        strict = counts(bits, "strict")
        s = sum(v for (b, w), v in struct.items() if b == bits)
        c = sum(v for (b, w), v in canon.items() if b == bits)
        t = sum(v for (b, w), v in strict.items() if b == bits)
        ref = count_inner(bits) if bits <= MAX_INNER_BITS else 0
        saved = 100.0 * (s - c) / s if s else 0.0
        print(f"{bits:>5} {s:>10} {ref:>12} {c:>10} {t:>10}  {saved:>13.1f}%")
        assert s == ref, f"structural mismatch at bits={bits}: {s} != {ref}"
    print("[OK] структурна модель збігається з count_inner.\n")

    print("== Ємність Рамки-3 за трит-довжиною ==")
    struct = by_trit_length("structural")
    canon = by_trit_length("canonical")
    strict = by_trit_length("strict")
    print(f"{'n':>4} {'блок':>5} {'структ':>12} {'каноніч':>12} {'suворе':>12} "
          f"{'економія %':>12}")
    for n in range(4, 22):
        block = "1 Б" if n <= 8 else ("2 Б" if n <= 14 else "3 Б")
        s, c, t = struct.get(n, 0), canon.get(n, 0), strict.get(n, 0)
        saved = 100.0 * (s - c) / s if s else 0.0
        print(f"{n:>4} {block:>5} {s:>12} {c:>12} {t:>12} {saved:>11.1f}%")

    print("\n== Підсумок по блоках ==")
    for lo, hi, label in ((4, 8, "1 байт (F3 XX)"), (9, 14, "2 байти"),
                          (15, 20, "3 байти")):
        s = sum(v for n, v in struct.items() if lo <= n <= hi)
        c = sum(v for n, v in canon.items() if lo <= n <= hi)
        t = sum(v for n, v in strict.items() if lo <= n <= hi)
        saved = 100.0 * (s - c) / s if s else 0.0
        print(f"{label:>16}: структурно {s}, канонічно {c}, suворе {t}, "
              f"економія {saved:.1f}%")

    print("\n== Бітова економія (log2 відношення) ==")
    for lo, hi, label in ((4, 8, "1 байт"), (9, 14, "2 байти"),
                          (15, 20, "3 байти")):
        s = sum(v for n, v in struct.items() if lo <= n <= hi)
        c = sum(v for n, v in canon.items() if lo <= n <= hi)
        bits = math.log2(s) - math.log2(c) if s and c else 0.0
        print(f"{label:>16}: зекономлено {bits:.3f} біт/програма")


def mutant_test() -> None:
    """Мертве дерево `((ATOM))` мусить бути названо відкинуто."""
    from semantic_redundancy_research import Form, Word, definitely_impossible

    dead = ("10", "10", "010", "01", "01")  # ((ATOM))
    quoted = ("10", "001", "10", "010", "01", "01")  # (QUOTE ((ATOM)))
    print("\n== Мутант-тест ==")
    print(f"  мертве дерево   : {' '.join(dead)}")
    print(f"  як дані (QUOTE) : {' '.join(quoted)}")
    dead_tree = Form((Form((Word("010"),)),))
    quoted_tree = Form((Word("001"), Form((Form((Word("010"),)),))))
    print(f"  definitely_impossible((ATOM))        = "
          f"{definitely_impossible(dead_tree)}  → named fail")
    print(f"  definitely_impossible(QUOTE ((ATOM))) = "
          f"{definitely_impossible(quoted_tree)}  → збережено як дані")


if __name__ == "__main__":
    main()
    mutant_test()


if __name__ == "__main__":
    main()
