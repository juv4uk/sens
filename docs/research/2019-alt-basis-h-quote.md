# Alternative basis probe H-QUOTE (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture / negative-leaning**  
**Parent:** `2019-seed-necessity.md` · #2011 quote-generator falsifiers  
**Lock:** does **not** remove QUOTE from premise bīja3; does **not** reassign `001`

## Question

```text
Is QUOTE a necessary operator root,
or can evaluation-suspension be recovered without a quote root?
```

## Capability at stake

```text
evaluation_control:
  treat an operand as data even when it has the shape of a form
```

Without some barrier of this kind, a universal evaluator cannot hold literal structure that looks callable.

## Candidate reconstructions (smuggling audit)

| candidate | idea | smuggles evaluation_control? | verdict |
|-----------|------|------------------------------|--------|
| **C1** host constants only | only pre-bound atoms are data; no compound literals | Avoids quote by **forbidding** quoted lists | **not equivalent** — weaker language |
| **C2** CONS of “inert” tags | build `(marker . x)` and special-case marker in eval | Marker + eval special case **is** quote under another spelling | **FAIL smuggle** |
| **C3** reader produces already-evaluated values only | no source form ever reaches eval as data | Moves barrier to **reader**; eval still has a quote-shaped cut | **FAIL smuggle** (phase shift) |
| **C4** fexpr / operator receives unevalled args | every operator controls evaluation | Replaces one quote root with **per-operator** control — larger, not smaller | **not smaller basis** |
| **C5** quote as macro over CONS | `(quote x)` → expand to data constructor | Expansion time still needs a **non-evaluating** phase | **FAIL smuggle** |
| **C6** drop universal eval | language is combinators only, no `eval` | Different language; not SENS-with-eval | **out of scope** |

## Bounded conclusion

```text
H-QUOTE-0 (strong form): "QUOTE is derivable from CAR/CDR/CONS/ATOM/EQ/COND alone"
  → unsupported; every classical path smuggles a suspend-evaluation cut

H-QUOTE-1 (weak form): "QUOTE may live outside operator bīja as a phase rule (reader/eval law)"
  → open conjecture; still an evaluation_control authority, only relocated

H-QUOTE-2 (honest form): "evaluation_control is a distinct capability class;
  packaging it as seed 001 is historical, the capability is not eliminable
  in a Lisp-like eval model"
  → best current fit with #2011 and necessity matrix
```

So the attack on QUOTE does **not** look like H-NIL (demote to pure data).  
It looks like: **keep the capability; debate only packaging** (seed opcode vs phase law).

## Contrast with H-NIL

| | H-NIL | H-QUOTE |
|--|-------|--------|
| Target | ground_value as operator | evaluation_control as operator |
| Demote to data? | plausible | **no** — control is not data |
| Eliminable in eval model? | maybe | **no** without language change |
| Priority | packaging + corpus check | **do not delete**; optional re-home as phase law |

## Falsifiers

1. Executable reconstruction of full #1962 corpus **without** any suspend-evaluation authority (seed, phase, or host).  
2. Proof that C2/C5 are not smuggling (would need formal capability accounting).

## Non-actions

- no removal of `001` from premise table  
- no generator children for QUOTE (already weak per #2011)  
- no status upgrade to theorem  

## One-line summary

```text
QUOTE packaging is negotiable; evaluation_control is not.
```
