# #2402 — нижня межа nearest-existing mutation

Статус: лише research. Ця робота **не** додає SET/SETQ у production і не
виділяє жодної post-D4 identity.

## Уже відома межа D4

D4 DEFINE уже може спостережувано змінювати binding, якщо target живе в
поточному frame:

```text
same-frame DEFINE X=NEW
  -> closure, яке вже бачить цей frame, бачить NEW
```

Але DEFINE з дочірнього frame для успадкованого імені створює shadow:

```text
parent X=OLD
closure P захоплює parent
child DEFINE X=NEW

child lookup -> NEW
P            -> OLD
```

Тому сама по собі зміна значення не є новою capability.

## Research countermodel

Test-only helper проходить той самий `Environment` graph, який захоплюють
closures:

```text
leaf
 -> parent
 -> ...
 -> nearest frame, де вже існує X
 -> замінити значення саме в цій location
```

Він не створює child shadow і не доступний мові.

Спостереження:

```text
parent X=OLD
closure P захоплює parent
child nearest-update X=NEW

child lookup -> NEW
P            -> NEW
child local X binding -> відсутній
```

Це відрізняється від D4 DEFINE за однакової початкової структури.

## Контрольні перевірки

- у chain із кількох frame змінюється найближча existing location;
- дальній shadowed parent не змінюється;
- missing binding fail-closed і нічого не створює;
- observer створюється до candidate update;
- жодного окремого host side-table/cell немає: змінюється той самий
  `Rc<RefCell<Frame>>` graph.

## Інтерпретація

Якщо witness переживе review:

```text
D4 child DEFINE shadowing
  !=
nearest-existing shared-location update
```

Це доводить observable semantic delta, але ще **не** вирішує:

- чи SET і SETQ — одна operation;
- чи computed target входить у ту саму capability;
- parent/width/bit placement;
- чи SENS взагалі має прийняти mutation.

Це наступні питання #2314/#2236.

## Принцип

**Mutation заслуговує semantic status лише тоді, коли observer, створений до
операції, може відрізнити “та сама location змінилась” від “створено новий
shadow binding”.**
