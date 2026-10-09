# Archipelago v1 — карта механізмів виконання, НЕ окремих D10 namespace

**Статус:** execution-island architecture; попередню семантичну ownership-модель скасовано рішенням [#4162](https://github.com/juv4uk/sens/issues/4162).  
**Семантична влада:** Contract 11.8, D1–D9 owner-ratified; D10 — **єдиний 10-бітний research/unratified потік**.  
**Лічильник D10:** виключно `knowledge/d10-v1-semantic-inventory.json`, не історична карта `knowledge/archipelago-map-v1.json`.

## Один D10, багато донорів

```text
SENS Core
  = одна однозначно декодована D10 semantic identity + закони + явний execution border

execution islands / packages / substrates
  = власні механізми виконання, реалізації алгоритмів, native result model
```

**Усі 87 авторських репозиторіїв — потенційні донори** незалежних, мовно-видимих законів для **того самого** D10 потоку. Доменна/пакетна належність, шахи, санскрит, фізика, знання або операційна система **не є підставою відхиляти** незалежний semantic law. Заборонені лише точний дублікат D1–D9/уже обраного D10, псевдонім поверхні, чистий механізм/бекенд і спростований закон. D2 залишається єдиним власником структури й керування.

Історичні #4047/#4092 прибрали 55+15 meaningful рядків за належністю острову. **[#4162 відновило всі 70](https://github.com/juv4uk/sens/issues/4162)** як selected-but-unplaced research, жодних D10 координат не відновлено. Тому старе `PACKAGE-ISLAND → NO-SLOT` правило **нечинне**.

## Відокремлені механізми виконання

Чотири execution islands мають native runtime model: Common Lisp; Prolog (уніфікація, підстановки й 0..N відповідей); Datalog (relations та fixed-point); CLIPS (facts, agenda, правила). Це лише власність **реалізації**, а не автоматична заборона окремих мовно-видимих законів на вході/виході.

Backend-репозиторії cml, fpga-lisp, sens-futhark, wsm-cuda, wsm-graalvm, wsm-os-lisp та wsm-target-contract володіють opcode/ISA, registers, ABI, CUDA/FPGA transport і runtime machinery. Самі механізми **не** D10 meanings; новий спостережуваний мовний закон із цих репозиторіїв може бути донором після індивідуального доказу.

## Уже обрані шість bridge meanings

Наведені універсальні мости є **частиною** inventory D10, а не обмеженням усіх інших значень:

```text
ISLAND-CALL
EXECUTION-WITNESS
NATIVE-OBSERVATION
RESULT-COUNT
BRIDGE
MISSING-CAPABILITY
```

Island result `0 substitutions`, порожній Datalog relation, відсутній native результат і D1 FALSE не є автоматично одним і тим самим. Producer-native observation та provenance зберігаються.

## Матриця донорів — чинне рішення #4162

`knowledge/d10-owner-repo-donor-matrix-v3.json` розподіляє 87 репозиторіїв:

```text
EVIDENCE-DONOR                    33
DIRECT-SEMANTIC-DONOR             43
SEMANTIC-DONOR-WITH-MECHANISM-GATE 11
------------------------------------
TOTAL                             87
```

Це класифікація джерел, **не** три D10 namespace, не автоматичне право на слот.

## Машинно перевірюваний стан D10

Числа з **поточного** `knowledge/d10-v1-semantic-inventory.json` (у разі наступної зміни inventory оновити цей блок в тому самому PR).

<!-- D10-INVENTORY-COUNTS:BEGIN -->
```text
D10 selected              625/1024
law-forced                256
unplaced                  369
remaining                 399
ratified                    0
```
<!-- D10-INVENTORY-COUNTS:END -->

**0 D10 residents ratified.** Для некоординатованих кандидатів `coordinate=null`, а сам факт selected/research **не надає** механізму авторизацію створити новий `.sens`.

## Суворе правило пропозицій

```text
джерело / реальний BLOCK .lisp → .sens
          ↓
оригінальний Git blob, рядок, явний input/output/observable law + falsifier
          ↓
семантичний dedup з ратифікованими D1–D9 і ВСІМ current D10 selected
          ↓
відкинути duplicate/alias/mechanism/falsified
          ↓
якщо незалежна мовно-видима семантика — HOLD/pending owner review (#4463)
          ↓
owner ratification або відхилення; до рішення: ratified=false, coordinate=null
```

Питання 8-бітної source-era, D2/Text7 Local/Global, T5 bytes/view, host effects та Core4 oracle **не** вирішуються вигадуванням D10 функції. D10 не замінює контракт #4449 source/physical/oracle admission. Proposal intake #4471 на review не означає, що незлита таблиця вже працює в `main`.

**Машинні джерела:** `knowledge/d10-v1-semantic-inventory.json` (current semantic count), `knowledge/d10-owner-repo-donor-matrix-v3.json` (донори), `knowledge/archipelago-map-v1.json` (історична/superseded execution map), #4162 (single stream), #4463 (research intake).
