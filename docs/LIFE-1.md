# LIFE-1: fresh-checkout witness

LIFE-1 proves one real end-to-end path without collapsing island result domains:

```text
SWI-Prolog
  -> Lisp-owned explicit projection
  -> Datalog
  -> provenance
  -> scheduler activation
  -> quiescence
```

The trace is provenance/control data, not a truth value. Prolog and Datalog keep their native result domains; the bridge is explicit and partial.

## Reproduce from a fresh checkout

Requirements:

- stable Rust toolchain;
- SWI-Prolog available as `swipl`.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y swi-prolog-nox
swipl --version
cargo test -p wsm-native-result-types --test prolog_datalog_bridge -- --nocapture
```

The same command is the canonical focused CI witness in `.github/workflows/life-1.yml`.

A missing Prolog runtime is an execution-availability failure. It must not mutate SID meaning or be normalized into Lisp falsehood.

## What the witness covers

The focused witness exercises a real SWI-Prolog query, preserves its native observation, applies the Lisp-owned Prolog-to-Datalog projection, runs the real Datalog kernel, records provenance references, schedules the matching pending invocation, rejects mismatched or malformed triggers, deduplicates repeated activation by observation/provenance identity, and reaches explicit quiescence when no pending work, new projection, or lifecycle transition remains.


---

# LIFE-1: перевірка зі свіжого checkout

LIFE-1 доводить один реальний наскрізний шлях без зведення результатів різних execution islands до спільного типу:

```text
SWI-Prolog
  -> явна проєкція, якою володіє Lisp
  -> Datalog
  -> provenance
  -> активація scheduler
  -> quiescence
```

Trace є даними provenance/control, а не значенням істини. Prolog і Datalog зберігають власні native result domains, а bridge залишається явним і частковим.

## Відтворення зі свіжого checkout

Потрібні:

- стабільний Rust toolchain;
- SWI-Prolog, доступний як `swipl`.

На Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y swi-prolog-nox
swipl --version
cargo test -p wsm-native-result-types --test prolog_datalog_bridge -- --nocapture
```

Та сама команда є канонічним focused CI witness у `.github/workflows/life-1.yml`.

Відсутній Prolog runtime є помилкою доступності виконання. Це не повинно змінювати значення SID або нормалізуватися в Lisp-falsehood.

## Що саме доводить witness

Focused witness виконує реальний SWI-Prolog query, зберігає його native observation, застосовує Lisp-owned Prolog-to-Datalog projection, запускає реальне Datalog kernel, записує provenance refs, планує відповідний pending invocation, відхиляє невідповідні або malformed triggers, дедуплікує повторну активацію за observation/provenance identity та доходить до явного quiescence, коли не лишається pending work, нової projection або lifecycle transition.
