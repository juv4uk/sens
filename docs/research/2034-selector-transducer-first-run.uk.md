# #2034 — контрмодель selector-transducer, перший прогін

Статус: **лише дослідження**. Жодних змін production semantics/runtime.

## Виконуваний результат

Witness порівнює два описи виконання вже доведеної selector-family:

1. root + suffix oracle;
2. deterministic subsequential transducer над усім bounded binary word.

Виконувані семантичні outputs — лише exact binary identities:

```text
101
110
```

У witness немає людських назв операцій.

Bounded exhaustive run до ширини 12:

```text
max width: 12
all bounded binary words checked: 8190
accepted selector identities: 2046
emitted primitive schedule steps: 18434
conceptual accepted-prefix trie nodes: 2050
minimal recognizer control states: 6
transition entries: 12

RESULT: exhaustive parity PASS
RESULT: no human operation names used by the executable witness
RESULT: selector execution control compresses to a constant-size automaton
NON-CONCLUSION: semantic identities are NOT collapsed
NON-CONCLUSION: automaton execution does NOT yet provide typed graph self-description
```

## Що це насправді означає

Selector-family можна виконувати малою control machine, кількість станів якої не росте разом із кількістю представлених selector identities.

Для accepted language:

```text
101[01]*
110[01]*
```

recognizer/transducer потребує лише:

- start;
- prefix states після `1`, `10`, `11`;
- одного спільного continuation state;
- dead state.

Після розпізнання root обидва semantic roots ділять той самий майбутній **control** state. Різний semantic root output емітується під час переходу в цей state.

Отже:

```text
semantic distinction
!=
persistent execution-control-state distinction
```

## Важливий non-conclusion

Це **не** доводить, що root+path — погане semantic representation.

Поточна root+generator model уже компактна і не потребує матеріалізації всіх 2050 trie-prefix nodes.

Тому правильне порівняння не таке:

```text
2050 stored tree nodes vs 6 automaton states
```

бо current semantic model не зберігає explicit trie.

Коректний bounded result вужчий:

> Prefix/semantic tree не є необхідною runtime control machine для доведеної selector-family.

## Сильніша архітектурна гіпотеза

Для різних ролей можуть бути природними різні мінімальні representation:

```text
typed graph / proof certificate
    -> explanation, evidence, self-description

minimal transducer / compiled recipe
    -> execution

canonical bounded word
    -> identity / portable semantic reference
```

Намагання змусити одну representation виконувати всі три ролі може додавати зайве machinery.

## Myhill–Nerode observation

Recognizer partition містить шість distinguishable control classes. Далі зливати recognizer states для current selector language уже не можна.

Це також корисне negative evidence: хоча багато повних слів мають спільну continuation structure, pre-root prefixes `1`, `10`, `11` залишаються behaviorally distinguishable.

## Наступні falsifiers

Automaton-first countermodel тепер мусить пройти:

1. non-selector family;
2. один recursive/SCC semantic cluster;
3. self-description / proof reconstruction;
4. state growth під час розширення corpus;
5. benchmark comparison проти direct bit-walk та compile-time recipes.

Якщо поза selectors machine потребує bespoke states майже one-per-semantic-identity — вона програє.

## Принцип

**Semantic graph може пояснювати слово, тоді як менша машина його виконує.**
