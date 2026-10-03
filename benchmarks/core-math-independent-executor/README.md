# Core-Math independent executor (#2428)

Standalone Rust mechanism consuming the #2427 neutral IR.

Independence boundaries:
- does not call the SENS evaluator;
- does not parse core.lisp;
- does not import Lisp operation tables;
- does not copy generated closure rows;
- uses its own gcd-normalized i128 rational representation;
- derives generated operations by dependency closure from the neutral rules.

The executor verifies the #2433 semantic-signature certificates and emits the
first concrete counterexample when an in-memory SUB law is intentionally
corrupted.
