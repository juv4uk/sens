# D10 research: independent CLOS method/class witnesses

Status: historical source-donor oracle only. This change adds no D10 candidate, coordinate, ratification, or physical T5 authority.

## Why this slice

The merged historical review (#4842) identifies method lookup, method removal, and class transition as behaviorally distinct questions. This change executes their ANSI Common Lisp donor witnesses under SBCL so later selection reviews can cite actual oracle observations instead of relying only on name absence or a Python model.

## Executable law slices

- FIND-METHOD distinguishes the method object matching exact qualifiers/specializers from the method currently dispatched for an argument. Missing signatures return NIL when errorp is false and signal when the default errorp applies.
- REMOVE-METHOD returns the same generic function; removing one method does not remove unrelated methods; the standard law requires no error when the requested method is absent.
- CHANGE-CLASS mutates the existing instance, returns that same object, preserves common slot values and common unbound state, initializes a newly added local slot, and invokes UPDATE-INSTANCE-FOR-DIFFERENT-CLASS.

Primary sources:
- FIND-METHOD: https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/stagenfun_find-method.html
- REMOVE-METHOD: https://www.lispworks.com/documentation/HyperSpec/Body/f_rm_met.htm
- CHANGE-CLASS: https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_change-class.html

## Verification boundary

The test runner executes the Lisp source in external SBCL, then checks the exact ordered observation IDs. The checker compares live inventory accounting monotonically, preserves the selected-count-at-creation only as a historic snapshot, and checks the D1-D9 name boundary. This is not a test of the SENS runtime; it must not be counted as a new D10 selection or proof of SENS parity. If a serialized peer selects one of these names meanwhile, this donor oracle remains valid and reports the current selection without mutating the inventory.
