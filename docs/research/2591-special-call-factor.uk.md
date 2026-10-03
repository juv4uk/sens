# #2591 — факторизація special-call протоколів

Фаза: **STRUCTURAL-DISCOVERY**  
Домен: `Core.PostD4.SpecialCallProtocol`  
Binary object: **UNPLACED**

Тут історичні FEXPR/FSUBR, Hart MACRO і поточний SENS TRANSFORMER
розкладаються на спостережувані осі без висновку про width чи coordinate.

## П'ять незалежно спостережуваних осей

```text
A raw-form input
B explicit caller environment
C returned-form / caller re-evaluation
D expansion timing / locus
E invocation packaging (whole-call vs operands-only)
```

A/B/C розділені повним bounded cube (#2522/#2530). D розділена OLD-vs-NEW
timing witness (#2568/#2569). E розділена alias/head collision witness
(#2580/#2588, merge 3d409736...).

Незалежно спостережувана **вісь** ще не є semantic root, бітом, width або
resident.

## Матриця протоколів

```text
                       raw  caller-env  returned-form  timing           packaging
ordinary LAMBDA         0       0           0         evaluation       operands-only
FEXPR/FSUBR             1       1           0         evaluation       operands-only
Hart MACRO              1       0           1         definition       whole-call
SENS TRANSFORMER        1       0           1         evaluation       operands-only
```

## Важливий parent-result

Для current TRANSFORMER є сильний same-base доказ із D4 LAMBDA (#2198/#2200):
staged value зберігає той самий closure payload.

Але різниця з ordinary LAMBDA складається не з одного observable delta:

```text
LAMBDA -> TRANSFORMER
  eager input  -> raw input
  direct value -> returned form / caller re-evaluation
```

A/B/C cube доводить, що ці два виміри можна розділити: raw input існує разом із
direct-value result у FEXPR. Тому їх не можна оголосити одним delta лише тому,
що конкретна реалізація пакує їх в один Macro value.

Отже архівний кандидат `00101 TRANSFORMER` **не можна повторно використати як
доведений one-bit child** за чинним законом #2236.

Це не доводить D6: кількість осей не визначає width.

## Remove-one атаки

- Без raw-form input undefined syntax стає eager і падає.
- Без explicit caller-env зникає доступ до caller-only binding.
- Без returned-form protocol повернена форма лишається value і не виконується.
- Без timing зникає різниця Hart OLD проти current SENS NEW.
- Без whole-call packaging два aliases з однаковими operands колапсують; head
  відновити неможливо.

## Структурний результат

```text
independently observable protocol axes = 5
proved semantic roots                 = 0
proved D5 children                    = 0
proved D6 children                    = 0
width                                 = UNKNOWN
coordinates                           = 0
```

Наступний крок — SENS-derivation: які осі переживають мінімізацію як незалежні
semantic roots і чи має хоч одна з них same-base parent рівно з одним delta.

## Принцип

**Спочатку факторизуємо спостереження. Protocol cube — не binary address map.**
