
---

# Додаток (Parijñāna, 2026-10-25): «прогалина» yantra — НЕ дефект. Ось докази

## Що знайдено

`lib/yantra.lisp` використовується як **джерело прив'язок** (`--binding-source`), а
не як програма:

```
scripts/count-executable-lisp.sh:167
    binding_sources=(--binding-source lib/unify.lisp … \
                     --binding-source lib/yantra.lisp …)

scripts/execute_changed_lisp_t5m.sh:1606
                     --binding-source lib/yantra.lisp
```

А `--binding-source` приймає **`.lisp`** — це видно з власного usage бінарника:

```
usage: sens --t5m-mint-pair <source.lisp> <output.sens> [--binding-source <source.lisp> ...]
```

## Отже

- **Як джерело прив'язок** `yantra` читається **з `.lisp`** — фізичної пари не треба.
- **Як окрема програма** він виконується лише в Rust-тесті через
  `include_str!("../../../lib/yantra.lisp")` — теж без пари.
- **У списках `run_case` SENS-законів його НЕМАЄ** (перевірено grep'ом).

**Висновок: `lib/yantra.sens` не потрібен.** Це не прогалина, а **властивість
задуму**: файл — **джерело прив'язок**, а не фізична програма.

## Що з цього лишається корисним

**Ніде це не записано.** Наступний агент (як і я) побачить 79 `визначити` без пари
й **шукатиме пару, якої не буде**. Тому єдина справжня дія — **зафіксувати явно**:
або в коментарі `lib/yantra.lisp`, або в переліку `is_explicit_non_implementation`,
або в чеку.

**І це змінює мою попередню заяву:** я писав «прогалина». Точніше —
**недокументований задум**. Дефект не в тому, що пари немає, а в тому, що
**невідомо, чи мала бути**.

## Deutsch

Die „Lücke" bei yantra ist kein Defekt: die Datei ist eine Bindungsquelle.

## English

The "gap" at yantra is not a defect: the file is a binding source.
