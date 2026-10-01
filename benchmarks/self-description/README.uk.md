# Benchmark самопису #2027

Це research-only harness для порівняння чотирьох способів пояснити ту саму доведену selector identity без людських назв:

- flat explicit metadata row;
- компактний proof certificate `root+suffix`;
- typed graph traversal;
- hybrid: graph один раз перевіряє distinct identities, після чого hot explanations використовують certificate.

Усі маршрути мусять відновити однакову name-erased форму:

```text
(root, suffix, depth)
```

Benchmark тримає окремо:
- storage/fact counts;
- relation edges touched;
- cold preparation / verification;
- hot CPU instruction cost.

Перед вимірюванням виконується parity gate.

Повний зафіксований перший прогін для i5-6400 лежить у:

```text
benchmarks/self-description/results/i5-6400-wsl2-2026-10-01/
```

Важлива межа: цей benchmark не ратифікує semantic architecture і не узагальнює selector-result на інші families.
