"""Рамка-3: консервативне виключення доведено неможливих викликів.

Це ДОСЛІДНА модель для точних слів D1/D3 і D2-списків, не новий
канонічний читач і не production codec. Прийняття за D2/виконанням
залишається за Rust/SENS. NOT_PROVEN_IMPOSSIBLE не означає valid/evaluable.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Word:
    bits: str

    def __post_init__(self):
        if self.bits not in {"0", "1"} | {f"{n:03b}" for n in range(8)}:
            raise ValueError("дослід підтримує тільки exact D1 і D3")


@dataclass(frozen=True)
class Form:
    items: tuple["Node", ...]


Node = Word | Form

# Ратифіковані D3 імена — лише коментарі; закони визначають exact bits.
# QUOTE=001; ATOM=010; CDR=011; CAR=100; EQ=101; CONS=111.
# D3 COND=110 і D3 EMPTY=000 НЕ отримують вигаданих arity-правил.
FIXED_ARITY = {"001": 1, "010": 1, "011": 1, "100": 1,
               "101": 2, "111": 2}
QUOTE = "001"


def definitely_impossible(node: Node, *, data: bool = False) -> bool:
    """True лише для доведеного арністю неможливого КОДУ.

    Консервативний алгоритм: unknown/macro/COND/necessary forms не
    перевіряємо за уявною таблицею арностей. Дані QUOTE прозорі.
    Вкладена голова-функція виконується як код; можливі аргументи
    unknown calls не оглядаємо, адже макрос може їх не виконувати.
    """
    if data or isinstance(node, Word):
        return False
    if not isinstance(node, Form):
        raise TypeError("очікується Word або Form")
    if not node.items:
        return False  # D2 () є значенням, не викликом.
    head, *arguments = node.items
    if isinstance(head, Form) and definitely_impossible(head):
        return True
    if not isinstance(head, Word):
        return False  # callability динамічної голови тут не доведено.
    arity = FIXED_ARITY.get(head.bits)
    if arity is None:
        return False  # Зокрема COND/макроси мають власну форму аргументів.
    if len(arguments) != arity:
        return True
    if head.bits == QUOTE:
        return False  # Рівно один аргумент, але він ДАНІ, а не виклик.
    return any(definitely_impossible(argument) for argument in arguments)


def words(node: Node) -> tuple[str, ...]:
    """Точний D2-схематичний друк лише для безкрапкових форм."""
    if isinstance(node, Word):
        return (node.bits,)
    return ("10", *(word for item in node.items for word in words(item)), "01")


def finite_candidates() -> tuple[Form, ...]:
    """Незалежний скінченний корпус форм: різні арності і вкладені голови."""
    heads: tuple[Node, ...] = tuple(Word(f"{i:03b}") for i in range(8)) + (
        Form((Word("010"),)), Form((Word("010"), Word("0"))),
    )
    args: tuple[Node, ...] = (Word("0"), Word("1"), Form((Word("010"),)))
    expressions = [Form((head, *values))
                   for head in heads
                   for n in range(4)
                   for values in product(args, repeat=n)]
    # Окремо структура, неправильна як код, але легальна як QUOTE-дані.
    expressions.append(Form((Word(QUOTE), Form((Form((Word("010"),)),)))))
    return tuple(sorted(set(expressions), key=lambda x: words(x)))


def admitted_research_codes() -> tuple[Form, ...]:
    """Ранг тільки серед НЕ доведено неможливих у СКІНЧЕННОМУ корпусі.

    Це НЕ admission oracle; реальні допустимі програми є підмножиною.
    """
    return tuple(x for x in finite_candidates() if not definitely_impossible(x))


def rank(node: Form) -> int:
    """Щільний номер у скінченному корпусі (без місць для неможливих)."""
    try:
        return admitted_research_codes().index(node)
    except ValueError as exc:
        raise ValueError("недопущена до дослідного рангу форма") from exc


def unrank(index: int) -> Form:
    if not isinstance(index, int) or not 0 <= index < len(admitted_research_codes()):
        raise ValueError("номер поза допустимим дослідним корпусом")
    return admitted_research_codes()[index]


if __name__ == "__main__":
    candidates = finite_candidates()
    admissible = admitted_research_codes()
    print(f"SEMANTIC-REDUNDANCY: universe={len(candidates)} "
          f"not-proven-impossible={len(admissible)} "
          f"proved-impossible={len(candidates) - len(admissible)}")
