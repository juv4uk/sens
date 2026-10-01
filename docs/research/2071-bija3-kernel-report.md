# #2071 — bīja3 epistemic kernel, first synthesis

Status: research-only. This does not ratify bīja3 minimality or production authority.

## Foundation order

This kernel sits above #2077 Foundation-0:

    exact bounded word
        -> intrinsic bits/width/boundary facts
        -> semantic evidence kernel
        -> self-description / execution / compiler

Bits and width are therefore not duplicated as semantic facts.

## Eight-row epistemic kernel

Every D3 address remains `address_status = premise`.

| word | abstract capability | current evidence strength |
|---|---|---|
| 000 | ground role | exact `()` representative remains premise; necessity open |
| 001 | evaluation suppression | capability supported; packaging as seed remains open |
| 010 | atom/pair classification | bounded lower-bound support; still open |
| 011 | atomic identity observer | bounded support; active alternative-basis attack |
| 100 | pair constructor | bounded fresh-structure lower-bound support |
| 101 | left projection | strongest current structural support |
| 110 | right projection | strongest current structural support |
| 111 | conditional evaluation control | capability supported; packaging/minimality open |

Forbidden inference: same width -> same semantic kind -> same proof strength.

## Intrinsic vs semantic

The checker derives exact bits, width=3, distinctness and padded form mechanically. Those are not semantic meaning.

Kernel rows store only evidence-bearing capability claims and epistemic state.

## Remove-one discipline

For each seed, remove its semantic-evidence row. Required behavior:

    explain(removed-word) -> UNKNOWN

Forbidden fallbacks: human name, numeric order, Hamming neighborhood, zero-padded legacy function, width-based role, prefix geometry.

All eight remove-one checks pass.

Important limitation: this proves fail-closed discipline, not global mathematical irreducibility.

## Critical 000 exception

Current Contract 10 says `()` is structural data outside the function space and function `00000000` is not `()`.

Therefore `000 -> 00000000` cannot be treated as a meaning-preserving legacy projection for the candidate D3 ground word.

The kernel records:
- exact `()` representative = premise;
- `00000000` = mechanical padded form only;
- semantic compatibility projection = forbidden.

For `001..111`, zero-padded legacy forms may be tested as compatibility mechanism candidates, but remain distinct exact identities.

## Consequence for #2081

The D3 shadow adapter cannot be uniform:

    001..111 -> checked legacy mechanism projection may be usable
    000      -> structural-ground oracle, never current function 00000000 as ()

## Executable checker

`scripts/research-2071-bija3-kernel.py` reports PASS for all eight rows, all eight remove-one checks, zero name/geometry fallbacks, and the 000 projection guard.

## Principle

**Store the irreducible claim only at the strength actually earned by evidence; derive the rest and leave the unknown unknown.**