# D10 proposal: CLASS-OF / безпосередній-клас (ук) · клас-прямого-екземпляра (укр)

**Stage:** pending owner review. This is a proposal-ledger entry only: it is not selected, not assigned a coordinate, not ratified, and not authorized for physical `.sens` execution.

## Source and existing witness

ANSI Common Lisp defines `CLASS-OF` as returning the class of which an object is a **direct instance**: [CLHS — CLASS-OF](https://www.lispworks.com/documentation/HyperSpec/Body/f_clas_1.htm).

The repository already has an independently executed SBCL donor oracle from merged [#4862](https://github.com/juv4uk/sens/pull/4862): `tests/oracles/d10_clos_slot_states.lisp`. It reports three focused observations:
- `CLASS_OF_EXACT_CLASS_OBJECT`: the result is identical to the class metaobject found for the class;
- `CLASS_OF_NOT_CLASS_SYMBOL`: the result is not just the class-name symbol;
- `CLASS_OF_CHILD_NOT_PARENT`: the direct child class is returned, not its superclass.

The oracle reported 17/17 observations passing in GitHub Actions for #4862. This is donor evidence, not proof that SENS already implements the operation.

## Observable law and discriminating tests

`CLASS-OF(x)` returns the class object of which `x` is a direct instance.

For a named standard class `C` and instance `x`:
1. `(class-of x)` is `eq` to `(find-class 'C)`.
2. If `C` inherits from `P`, an instance of `C` returns `C`'s class object rather than `P`'s.
3. For a named standard-class instance, `TYPE-OF` commonly returns the type specifier/name, while `CLASS-OF` returns the class metaobject. Their observable results differ.

Falsifiers: returning the class-name symbol instead of a class object; returning the superclass; or fabricating a distinct object rather than the class metaobject for the direct class.

## Dedup and ownership question

The current main inventory contains 647 selected research candidates and no exact `CLASS-OF` name. The canonical proposal-ledger records the D1–D9 and D10 Git blob SHA values as **PENDING** rather than claiming an unproved universal no-match. The snapshot is pinned to `c67db6cdd820dea8d3a110caed359507c0a2d7a4` (D1–D9 blob `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`; D10 inventory blob `7e13e929338baeef9b16c2139d24b78e23ea1e03`). That fact is only a routing clue. The substantive distinction is direct class-metaobject identity vs a type specifier, and must still be reviewed against `TYPEP`, `CLASS-NAME`, `FIND-CLASS`, and the full selected D10 vocabulary.

The owner decision is whether this observation is an independently required Core law or a derived composition. No domain is changed in this proposal. The canonical row is `D10P-4870` in `knowledge/d10-proposal-ledger.tsv`, with `width=D10`, `pending-review`, and `ratified=0`; the machine artifact requires `coordinate=null`, `selected_d10_candidate=false`, and `physical_t5_authorized=false`.
