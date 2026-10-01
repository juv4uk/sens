# #2107 — incidence нижче за relation

Лише дослідження.

## Центральне спостереження

Запис `R ⊆ C×C` вже не є структурно нейтральним. Щоб задати directed relation, ми вже маємо:
```text
distinguishable endpoint occurrences
incidence
ordered roles source/target
optional relation-kind labels
```

## Чотири шари

```text
D  distinguishable points
I  undirected incidence
O  oriented incidence
L  labeled oriented incidence
```

## Witness орієнтації

Однакова undirected star:
```text
a—b
|
c
```
допускає:
```text
out-star: a→b, a→c
in-star:  b→a, c→a
```

Underlying incidence однакова, але directed degree signatures різні. Отже directed graphs не є direction-preserving isomorphic.

Тому orientation — окрема структура поверх incidence.

## Перейменування

Перейменування node tokens зберігає graph isomorphism: host-назви є координатами, не семантичним змістом.

Так само послідовне bijective relabeling relation kinds зберігає typed structure, але злиття двох relation roles в один тип втрачає інформацію.

## Наслідок

Безпечніша декомпозиція:
```text
distinction / endpoint occurrence
 -> incidence
 -> orientation
 -> relation typing
 -> paths / behavior
 -> observations
```

Артефакт: `scripts/research-2107-incidence-foundation.py`.
