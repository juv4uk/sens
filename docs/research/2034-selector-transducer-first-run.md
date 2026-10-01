# #2034 — selector transducer countermodel, first run

Status: research-only countermodel. No production semantics/runtime changes.

## Executable result

The witness compares two execution descriptions for the already-proven selector family:

1. root + suffix oracle;
2. whole-word deterministic subsequential transducer.

Executable semantic outputs are exact binary identities only:

```text
101
110
```

No human operation names participate in the witness.

Bounded exhaustive run through word width 12:

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

## What this actually means

The selector family can be executed by a small control machine whose state count does not grow with the number of represented selector identities.

For the accepted language:

```text
101[01]*
110[01]*
```

the recognizer/transducer needs only:

- start;
- prefix states after `1`, `10`, `11`;
- one shared continuation state;
- dead state.

After a root is recognized, both semantic roots share the same future **control** state. Different semantic root output is emitted at the transition into that state.

That means:

```text
semantic distinction
!=
persistent execution-control-state distinction
```

## Important non-conclusion

This does **not** prove that root+path is a bad semantic representation.

The current root+generator model is already compact and does not need to materialize all 2050 trie-prefix nodes.

Therefore the correct comparison is not:

```text
2050 stored tree nodes vs 6 automaton states
```

because the current semantic model does not store that explicit trie.

The valid result is narrower:

> A prefix/semantic tree is not required as the runtime control machine for the proven selector family.

## Stronger architectural hypothesis

Different roles may deserve different minimal representations:

```text
typed graph / proof certificate
    -> explanation, evidence, self-description

minimal transducer / compiled recipe
    -> execution

canonical bounded word
    -> identity / portable semantic reference
```

Trying to force one representation to serve all three roles may add machinery.

## Myhill–Nerode observation

The recognizer partition contains six distinguishable control classes. No further recognizer-state merge is possible under the current selector language.

This is useful negative evidence too: even though many full words share continuation structure, the pre-root prefixes `1`, `10`, and `11` remain behaviorally distinguishable.

## Next falsifiers

The automaton-first countermodel must now face:

1. a non-selector family;
2. one recursive/SCC semantic cluster;
3. self-description / proof reconstruction;
4. state growth as the corpus expands;
5. benchmark comparison against direct bit-walk and compile-time recipes.

If the machine needs bespoke states almost one-per-semantic identity outside selectors, it loses.

## Principle

**The semantic graph may explain a word while a smaller machine executes it.**
