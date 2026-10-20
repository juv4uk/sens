; #419 — Карта споживачів і залежностей Канону. Лише навігація для аудиту.

(canon-sculpt-consumer-map
  (schema-version 1)
  (rule (read-only-consumer-audit))

  (candidate
    (identity PRIM_ATOM)
    (known-semantic-surface structural-kind)
    (migration-hazard "Не виводити стару поведінку предикатів t/(); чинне спостереження структури має багатшу семантику"))
  (candidate
    (identity PRIM_EQ)
    (known-semantic-surface identity-relation)
    (migration-hazard "Не припускати загальної істинності або тотожності вказівників зовнішнього виконавця"))
  (candidate
    (identity PRIM_COND)
    (consumer-hazard "Семантика керування визначає вибір і порядок обчислення; текстова заміна не доводить вивідності"))
  (candidate
    (identity PRIM_QUOTE)
    (consumer-hazard "Звичайні виклики функцій не здатні припинити обчислення аргументів без додаткового механізму керування"))
  (candidate
    (identity PRIM_CONS)
    (consumer-hazard "Споживачів конструктора слід відрізняти від представлення пари й виділення пам’яті виконавцем"))
  (candidate
    (identity PRIM_CAR)
    (consumer-hazard "Споживачів операції спостереження слід відрізняти від машинного механізму читання пам’яті та адресації"))
  (candidate
    (identity PRIM_CDR)
    (consumer-hazard "Споживачів операції спостереження слід відрізняти від машинного механізму читання пам’яті та адресації"))

  (coordination-exclusion
    (active-work
      421
      418 410 406 396
      392
      328
      402 403
      409 413
      317))
  (next
    "Замінити кожний рядок лише з ризиком на виявлених у чинному коді споживачів після завершення паралельних перенесень; доти невідоме залишається невідомим"))
