# СТАН РЕЛІЗНИХ ГЕЙТІВ — вимір, не оцінка

Автор: агент Sampūrti, 2026-10-26. Кожен рядок — результат запуску, не припущення.

## Прогнано на поточному main

| гейт | результат |
|---|---|
| `scripts/check-release-pins.py` | **PASS** `RELEASE_PINS_PASS channel=1.99.0 workflows=14` |
| `scripts/check-release-version-alignment.py` | **PASS** `expected=0.42.1 crates=7 locked=7 guix=0.42.1` |
| `scripts/audit-workflow-pins.py` | **PASS** `AUDIT_PASS` |
| `scripts/check-sens-only-semantic-tests.sh` | **PASS** `МОВНИЙ_ГЕЙТ=OK registry=ARCHIVE runner_workflows=310` |
| `scripts/check-release-admission-ledger.py` | **BLOCKED** — див. нижче |
| `scripts/check-release-triple-corpus.py` | потребує ЗГЕНЕРОВАНОГО інвентаря (крок пайплайна), не статичного файла |

**Чотири гейти зелені. Один блокує. Один — крок пайплайна.**

## ЄДИНИЙ БЛОКЕР — і він правий

```
RELEASE_ADMISSION_BLOCKED: запис 1: typed_word_sha256 не збігається
                           з .sens tests/semantic/meta-eval-graph-d1-law.sens
```

Виміряно:

| | значення |
|---|---|
| заявлено в реєстрі | `d01268c05132611c32f79c30b9faa71594b5008106c7ad327df0aad9bdb0a98d` |
| реально в файлі | `d1a8a8882461a28dcfe4c4876b832195ff1a805e69e930649106a56d03fb698c` |

Файл декодується: **671 слово**, хеш збігається з `content_sha256()` — тобто
перевірка рахує правильно, розбіжність **справжня**.

## Чому це НЕ застарілий реєстр, а справжня розбіжність

Історія:

```
f845f6c3  2026-10-24 05:31  «Виправити докази MetaEval на структурних іменах»   ← засвідчено
5ae71b9f  2026-10-24 05:33  «Оновити походження доказів MetaEval»               ← реєстр оновлено
16d4ed47  2026-10-26 11:07  «ремонт пар: канонічні SENS/Zig T5M на актуальному main»
                                                                                ← ФАЙЛ ПЕРЕМІНТЕНО ПІСЛЯ
```

Файл перемінчено **через два дні після** засвідчення. `typed_word_sha256` засвідчує
**слова**, а не байти. Отже перемінчення дало **ІНШІ СЛОВА** — а не той самий вміст в
іншій упаковці.

**Тому оновлювати хеш у реєстрі НЕ МОЖНА.** Це було б підробкою засвідчення: записати
новий вміст під старим доказом F1–F4, який стосується коміта `f845f6c3`.

## ВІДПОВІДЬ: джерело змінилося — мінтер не винен

Перевірив історію трьох файлів:

```
tests/semantic/meta-eval-graph-d1-law.lisp
   018f556f  2026-10-26T11:00:18  «test(SENS): refresh meta-eval graph T5M pair natively…»
   f845f6c3  2026-10-24T05:31:52  ← засвідчений коміт

tests/semantic/meta-eval-graph-d1-law.sens
   16d4ed47  2026-10-26T11:07:43  «ремонт пар: канонічні SENS/Zig T5M…»   ← через 7 хвилин

scripts/prove-meta-eval-graph-d1.sh
   3f1aa53d  2026-10-26T11:08:53  «test(SENS): run exact-main native laws…»
   ada80732  2026-10-26T10:33:07  «SENS: graph/predicates prove без sha256sum»
   f845f6c3  2026-10-24T05:31:52  ← засвідчений коміт
```

**Джерело (`.lisp`) ЗМІНИЛОСЯ 2026-10-26 о 11:00**, і `.sens` перемінчено **через 7
хвилин** — тобто пара **свіжа й узгоджена**. Отже:

- це **НЕ дефект мінтера**;
- змінився **вміст**, тому `typed_word_sha256` змінився **законно**;
- **застаріле саме ЗАСВІДЧЕННЯ**: докази F1–F4 прибиті до `f845f6c3`, а після нього
  змінилися **і джерело, і скрипт доказу**.

## Що потрібно, щоб зняти блок

Пере-засвідчити запис **проти нового коміта**:
`scripts/connect-release-admission-native.py` проганяє
`scripts/prove-meta-eval-graph-d1.sh` і вимагає `NATIVE_SENS_PASS`, після чого F1–F4
мають вказувати на **актуальний** SHA, а `typed_word_sha256` — на
`d1a8a8882461a28dcfe4c4876b832195ff1a805e69e930649106a56d03fb698c`.

**Оновлювати лише хеш, лишивши F1–F4 на `f845f6c3`, НЕ МОЖНА** — це записало б новий
вміст під старим доказом.

**Чому я цього не зробив:** конектор вимагає `target/debug/sens` (native `sens` CLI).
У моєму середовищі немає `cargo`/`rustc`, тому він друкує
`NATIVE-CONNECTOR-BLOCKED` і нічого не вигадує — це його власна fail-closed поведінка.
Python-кодек **не може** відтворити `.sens` із `.lisp`: його `parse_words` /
`parse_t5m_words` приймають двійкові слова, а не Lisp-джерело (`SensT5Error: got ';'`).

## Deutsch

Vier Release-Gates grün, eines blockiert — und der Block ist berechtigt.

## English

Four release gates green, one blocks — and the block is justified.
