# Ukrainian surface naming

The canonical domain tables use two Ukrainian columns for different jobs:

- `ук` — compact coding surface;
- `укр` — expanded Ukrainian explanation.

The compact surface must stay guessable from the expanded one. We shorten structure, not word roots.

## Stable compact grammar

- predicates keep `?`;
- destructive/in-place operations use `!` in all programming surfaces: `ук`, `укр`, and `en`; `укр` may retain the expanded `-на-місці!` wording;
- composite selectors use a path alphabet:
  - `п` = `перше`;
  - `р` = `решта`;
  - examples: `CAAR → п-п`, `CADR → п-р`, `CDAR → р-п`, `CDDR → р-р`;
- D7 omits redundant domain context such as `звук-` and `текст-` when the resident remains unambiguous;
- standard mathematical abbreviations are allowed when conventional and unambiguous: `нсд`, `нск`;
- do not invent clipped stems such as `відобр`, `посл`, `заст`, `елем`.

## Examples

| ук | укр |
|---|---|
| `п-р` | `перше-від-решти` |
| `видалити!` | `видалити-на-місці!` |
| `нсд` | `найбільший-спільний-дільник` |
| `а-короткий` | `звук-голосний-а-ротовий-короткий` |
| `цифра-8` | `текст-цифра-8` |

The compact form is a human surface only. It never changes exact domain identity, resident coordinates, or law.
