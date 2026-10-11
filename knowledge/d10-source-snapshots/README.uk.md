# Незмінні історичні донори досліджень D10

Це **байт-ідентичні Git blob знімки** для перевірки історичних визначень. Вони не є поточним `lib/`, не викликаються runtime, не отримують координат D10 і не підтверджують змісту нового виконуваного файлу.

| Історичний шлях | Blob SHA | Призначення |
|---|---|---|
| `lib/quantity.lisp` | `40c38e6019beccddd8577aa7af5a0957f4932b89` | raw-definition evidence |
| `lib/translation.lisp` | `80cd225cba549a837097b1e633b6662c9434a148` | raw-definition evidence |
| `lib/si.lisp` | `2b94f1ea6d2fb05c084c3a0d863c14119a5ba11f` | raw-definition evidence |
| `lib/reason.lisp` | `fcc6d5828b5c3b883c427b0bcb567777404db184` | raw-definition evidence |
| `lib/persistent-vector.lisp` | `9ae30559eb6d5d265c17c234cee8bb32e9cc5acf` | D9 donor-dedup evidence |
| `lib/unify.lisp` | `e5c7399959eab0746930aea6b3e20f047e81c7ae` | D9 donor-dedup evidence |
| `lib/reason.lisp` | `dadc52a2f40f2f30ad77642898afb81980044c08` | separate historical DEFINE evidence |

Фізичний знімок зберігається як `knowledge/d10-source-snapshots/<blob-sha>.lisp`. Перевірки обов'язково обчислюють Git blob SHA фактичних байтів і звіряють розташування визначень. Змінений або відсутній знімок означає FAIL. Поточні `lib/*` перевіряються окремими семантичними тестами; два різні історичні `lib/reason.lisp` є різними доказами, а не взаємозамінними версіями.

Без ратифікації D10 або зміни D1–D9.
