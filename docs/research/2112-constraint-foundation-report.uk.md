# #2112 — статус обмежень до розширення relation

Лише дослідження. Жодної production-міграції.

## Питання

Екстенсійну relation зазвичай записують як множину позитивних фактів:

```text
R = { допустимі кандидати }
```

але у відкритій дослідницькій мові таке подання втрачає різницю між:

```text
REFUTED
UNKNOWN
```

бо обидва стани просто відсутні в `R`.

## Кандидат на нижчий шар

Для обмеженого простору можливостей Ω кожному кандидату надаємо один статус:

```text
ADMITTED
REFUTED
UNKNOWN
```

Це не PredicateBit програми. Це метасемантичний статус кандидата-факту або твердження.

## Результат для повного світу

Якщо кожен кандидат вирішений, тоді:

```text
ADMITTED = Ω \ REFUTED
REFUTED  = Ω \ ADMITTED
```

Отже у справді повній замкненій скінченній моделі позитивне й негативне розширення взаємно визначають одне одного.

## Контрприклад для відкритого світу

Будуємо дві моделі з однаковим позитивним розширенням:

```text
A: p admitted, q refuted,  r unknown
B: p admitted, q unknown,  r refuted
```

В обох:

```text
positive relation = {p}
```

але знання різне.

Так само дві моделі можуть мати однаковий набір спростованих кандидатів, але відрізнятися тим, які з решти допустимі, а які ще невідомі.

Тому:

```text
лише positive extension  втрачає REFUTED проти UNKNOWN
лише negative extension  втрачає ADMITTED проти UNKNOWN
```

## Припущення closed world

Executable witness окремо застосовує політику:

```text
UNKNOWN -> REFUTED
```

і показує, що вона змінює модель.

Отже closed-world reasoning є додатковим законом або політикою, а не властивістю вихідного шару статусів.

## Перейменування

Бієктивне перейменування токенів кандидатів зберігає структуру статусів, хоча host-токени змінюються.

Тому назви proposition/fact є координатами механізму; змістом у цій моделі є саме структура `ADMITTED/REFUTED/UNKNOWN`.

## Наслідок для relation/composition

Коли evidence неповне, relation-факти з #2103/#2107 слід читати як **ADMITTED-зріз** багатшого status-шару.

Перевірені falsifier-и з #2017 природно лежать у **REFUTED-зрізі**.

Усе інше повинно залишатися UNKNOWN, доки окрема теорема повноти або closed-world закон не доведе інше.

Це ортогонально до:
- правил виводу #2108;
- форми judgment з #2104;
- incidence/orientation з #2107.

## Фундаментальний наслідок

Безпечніша поточна драбина:

```text
candidate possibility / proposition
  -> admitted | refuted | unknown
  -> incidence/orientation/composition facts
  -> consequence/proof
  -> observations/equivalence
  -> identities/words/binary
```

Абсолютне дно ще відкрите, бо навіть `candidate possibility` може вже приховано припускати identity/occurrence.

Артефакт: `scripts/research-2112-constraint-foundation.py`.
