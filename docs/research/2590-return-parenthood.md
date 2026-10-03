# #2590 — RETURN / PROG parenthood attack

Status: STRUCTURAL-DISCOVERY, research-only.

## Result under test

Existing executable evidence already separates two cases:

```text
GO
  -> local finite-state parameter + tail recursion

RETURN
  -> value + nearest active dynamic exit context
  -> crosses ordinary nested calls
```

The new bounded verifier does not reimplement those semantics. It checks the
placement question that follows from them.

### Tested D4 parent tournament

```text
APPLY   = invoke callable
EVAL    = evaluate form
LAMBDA  = construct closure
COND    = local branch selection
RETURN  = dynamic non-local exit
```

None of the tested D4 candidates owns the same base operation as RETURN.

### CPS is compilation, not parenthood

The existing D4 countermodel can reproduce RETURN behavior by threading an
explicit `exit-k` through the nested helper call chain. That proves whole-program
D4 compilability, but it changes the call protocol:

```text
source helper interface
    !=
helper + explicit exit-k interface
```

Therefore CPS does not establish a local same-base D4 parent.

### PROG

PROG remains a composition of:

```text
local GO state-machine
+ non-local RETURN factor
```

No single PROG resident follows.

## Cross-family control

RETURN changes control without requiring shared-location mutation. The #2589
mutation factor changes a shared location while ordinary control returns
normally. The bounded observations therefore keep these factors distinct.

## Conservative conclusion

```text
GO                    = derived local structure
RETURN same-base D4 parent = none found in tested set
RETURN exact width     = UNKNOWN
RETURN root status     = NOT PROVED
PROG                   = composite
coordinates allocated  = 0
```

No D5/D6 residency or coordinate follows from this report.
