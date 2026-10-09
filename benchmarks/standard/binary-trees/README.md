# BENCH-STD1: binary-trees

Цей каталог фіксує **spec/provenance** першого зовнішньо впізнаваного
стандартного workload для SENS. Execution adapter буде під'єднано лише після
стабілізації shared cross-language schema (#1546/#1550).

## Upstream

Computer Language Benchmarks Game 25.03:

- description:
  https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/binarytrees.html
- measurements:
  https://benchmarksgame-team.pages.debian.net/benchmarksgame/performance/binarytrees.html
- expected N=10 output:
  https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/binarytrees-output.txt

Зафіксовано: 2026-09-27.

Upstream прямо позначає binary-trees як contentious: на сторінці вимірів
змішані різні implementation approaches, single-thread і multi-thread
програми. Тому ми **не копіюємо чужі fastest variants або published times**.

## Наш профіль порівняння

Мета — той самий алгоритм і той самий обсяг роботи на одному self-hosted
runner:

- single-thread для SENS, CPython, Lua, Racket;
- min_depth = 4;
- max_depth = max(min_depth + 2, N);
- stretch_depth = max_depth + 1;
- stretch tree створюється повністю, перевіряється і відпускається;
- long-lived tree створюється до churn і живе до фінальної перевірки;
- для depth = 4,6,...,max_depth:
  iterations = 2 ** (max_depth + min_depth - depth);
- кожна ітерація повністю створює perfect binary tree, обходить його з
  підрахунком вузлів і відпускає;
- leaf node та interior node мають ту саму node allocation shape;
- node check = 1 + left-check + right-check, leaf check = 1;
- custom arena / memory pool / free list заборонені;
- default GC/runtime allocator, якщо реалізація має GC.

## Масштаб

Перший fixture — N=10, бо upstream дає точний expected output і він
підходить для correctness та первинного same-machine виміру.

N=21 — upstream performance scale. Ми запускаємо його лише якщо поточний
SENS runtime практично витягує цей обсяг без зміни алгоритму. Результат N=10
не називається еквівалентом published Benchmarks Game N=21 timing.

## Межа інтерпретації

Це implementation benchmark, не рейтинг абстрактних мов.

Усі SENS/CPython/Lua/Racket числа мають бути отримані локально на одному
runner. Published upstream seconds/memory використовуються лише як контекст,
не як одна зі сторін нашої таблиці.
