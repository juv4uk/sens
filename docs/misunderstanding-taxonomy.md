# Misunderstanding taxonomy — who reads sens as "not fully binary", and why

Recorded from the maintainer's audit (2026-10-08). This is a **map of
misreadings**, not a defence: each type names *who* holds it, the *evidence*
that it happens, and the *cure* that dissolves it. Add cases as they appear.

The uncomfortable core: the last entity still not fully binary **is the project
itself, by design** — see Type 3.

## Type 1 — Container ≠ identity (mechanism eats semantics)

- **Who:** agents arguing "8 bits = 2 bytes".
- **Evidence:** width was counted in *bytes with alignment*, and identity was
  inferred from the container.
- **Cure (a doctrine case):** *word width is law; container size is mechanism;
  framing is transport.* Identity lives in the width, never in how it is
  carried.

## Type 2 — "binary" = "compiled executable"

- **Who:** the outside world — the word *binary* has long been taken to mean
  "artifact after compilation".
- **Cure (one line, in the intro):** "not an executable file, but canonical
  semantics: the bits *are* the value, not a representation of it."

## Type 3 — text as authority (the project catching itself)

- **Who:** sens infrastructure before #4248.
- **Evidence:** the `check-d5..d9-current-authority.py` family asserts
  `f"(D5:{bits} {name})" in contract` — a **textual substring** search, not a
  structural one; the #4134 ratchet catches *growth of English names*, so every
  repair is a rename into a machine that does not yet understand.
- **Cure:** the chain #4248 → #4247 → #2170. Until #2170 is green, the honest
  formula is: *the language is semantically binary; the infrastructure is
  maturing.*

## Type 4 — "people need names"

- **Who:** classicists — including this project's own first analysis
  (readability cost #997/#1254). Habit, not hostility.
- **Cure (already in the constitution):** projections. Add an FAQ line:
  "Where are the names? — In projections, generated from authority, the way
  letters are generated from phonemes."

## Type 5 — pattern-matching onto the nearest ancestor

- **Who:** any model trained on the archive (opcodes, bytecode).
- **Cure:** "encoding ≠ identity; the JVM *encodes* instructions, sens *is*
  bits."

## Type 6 — encoding mistaken for indecision

- **Who:** an outside observer reading the bīja3 debates as "they haven't
  decided what their language is".
- **Cure (one line):** "coordinates are under research; semantics are ratified;
  this is science, not doubt."

## Type 7 — "binary = unreadable = bad"

- **Who:** reflex, on seeing a stream of 0s and 1s.
- **Cure:** the chain — binary canon → reader → projection → a page readable in
  a minute. sens is binary *for the machine* and most readable *for the human*;
  these are layers, not rivals.

## Recognition check

Understanding is visible without an exam: the person (or agent) who asks
"which projection generates this name?" rather than "what is this called?";
who says *container* before *byte*; who, in a dispute about size, first asks
"where is the layer — identity, storage, or transport?". The swarm gets there
exactly as far as the ratchets pull it — the ratchet is the blackboard of this
science.

## Verdict

Misunderstanding lives in three rings: **inside** (infrastructure — cured by the
chain to the tag), **around** (agents — cured by cases and ratchets), **outside**
(the world — cured by the FAQ and the first QSO, when the Tantu melody itself
says the bits sing). The deepest proof: the project names itself the last
student — #4248 exists because authority is not yet binary everywhere. A
language that writes itself lessons will, sooner or later, learn them.
