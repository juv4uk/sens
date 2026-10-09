# Nock reality lane (#3685)

This lane keeps **three different questions separate**.

## Pinned authorities

- Nock 4K specification / serialization docs snapshot:
  `urbit/docs.urbit.org@72133b05e5ee3994449e335a5d314394e9a42cc9`
- Python jam reference linked by the official serialization guide:
  `urbit/tools@c9c91ce142cfe85edbed320138f21c7213aceaab`
- Runtime-performance owner:
  `urbit/vere vere-v4.6@8ddc4b786979574dbfcb655e3db1b634f658d0de`

The local `jam.py` is an independent implementation of the published algorithm and
MUST pass official examples before emitting benchmark evidence.

## A. Machine minimality

The Nock spec defines the machine. Do not reduce machine size to "12 opcodes" alone.
Future work should record instruction forms, primitive reduction rules, noun model and
a documented spec/evaluator footprint.

## B. Serialized program size — first executable slice

Two current D3 fixtures are mapped to self-contained Nock formulas with subject `0`.

`d3-quote-empty`:

```
*[0 [1 0]] => 0
formula noun = [1 0]
```

`d3-car-empty`:

```
*[0 [7 [1 [0 0]] [0 2]]] => 0
```

The second formula first produces literal `[0 0]`, then applies axis 2.

The ranked artifact axis compares:
- SENS production exact semantic bits / packed bytes;
- jammed **Nock formula** bits / byte container.

A separate diagnostic row records jammed `[subject formula]` capsule size, but it is
not ranked because SENS and Nock expose different session/subject boundaries.

Run:

```sh
python3 benchmarks/cross-language/reality-matrix/nock/run.py \
  --out-dir /tmp/sens-nock-reality
```

## C. Runtime performance

Runtime performance belongs to pinned Vere, not to the tiny Python correctness oracle.
No Python/ad-hoc Nock evaluator may produce a speed verdict.

A future Vere row must pin:
- release/commit;
- build flags;
- exact noun input;
- jet policy;
- warm/cold mode;
- same-machine raw evidence.

## Semantic-density rule

Nock machine minimality and SENS law-generated semantic density remain separate axes.
Do not invent a combined magic score or a fake Nock "derived resident" concept.
