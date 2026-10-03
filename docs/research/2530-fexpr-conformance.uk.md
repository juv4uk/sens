# #2530 — behavioral conformance для FEXPR/FSUBR

Статус: лише research.

Цей slice закриває concrete-behavior gaps після protocol cube #2522.

## C1 — raw list structure

Bounded fixture містить nested syntax та undefined branch:

    (wrapper
      (quote (a b))
      (branch never-defined))

Raw mode може оглянути точну структуру форми, не торкаючись undefined branch. Eager mode доходить до нього і падає.

## C2 — nested raw call

Outer raw callable передає ті самі syntax objects внутрішньому raw callable. Inner повертає лише першу form і не обчислює невикористаний never-defined.

Ті самі operands в eager mode падають до body.

## C3/C4 — live ordinary vs macro control

Witness читає current crates/sens/src/eval/closures.rs: ordinary closure мусить evaluate operands до binding, а current macro зберігає raw Expr через quote.

## C5 — caller environment не є hidden macro-body parameter

Current macro body виконується в closure-derived local frame. Результат пізніше стає code і tail-evaluate у calling_environment. Caller env не додається в transformer parameter slots.

Phase-E distinction:

    historical FEXPR:
      explicit caller a-list = direct call input

    current macro:
      caller environment керує post-expansion execution,
      але не є direct transformer-body parameter

## C6 — no human-name authority

Bounded dispatcher використовує typed CallMode, а не strings FEXPR/FSUBR чи property-list tag.

Historical tags — лише provenance/mechanism evidence.

## Phase-E consequence

Разом із three-axis cube #2522:

    FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES
    TRANSFORMER-RELATION=ORTHOGONAL

ORTHOGONAL тут означає relation між protocol axes, не ranking expressiveness.

## Non-conclusion

Жоден D5/D6 width чи coordinate не випливає з цього witness.

## Принцип

Raw-call semantics мають пережити конкретні syntax-shape та nesting probes, перш ніж їх можна вважати окремою semantic dimension.
