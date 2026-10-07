# D10 island bridge factorization v1

**Status:** research / unratified  
**Issues:** #4036 #4054 #4094  
**Foundation:** #4008 / Contract 11.8

The execution/backend repository set is reviewed only for substrate-independent seam laws. Native CUDA, FPGA, ABI, ISA, driver, MMIO and compiler-IR operations remain mechanism-owned.

## Selected Core seam meanings

```text
ISLAND-CALL
EXECUTION-WITNESS
NATIVE-OBSERVATION
RESULT-COUNT
BRIDGE
MISSING-CAPABILITY
```

## Factored away

```text
ZERO-RESULTS = RESULT-COUNT == 0
ONE-RESULT   = RESULT-COUNT == 1
MANY-RESULTS = RESULT-COUNT > 1

MISSING-BRIDGE = MISSING-CAPABILITY(kind=bridge)
MISSING-KERNEL = MISSING-CAPABILITY(kind=kernel)

EXPLICIT-PROJECTION = ordinary APPLY of a projection function
ISLAND-PROVENANCE   = lower PROVENANCE projection
ISLAND-SELECT       = ordinary data selection
RAW-ISLAND-INVOKE   = mechanism-only escape hatch
```

## D10 accounting

```text
before      428/1024
new           6
after       434/1024
placed      256
unplaced    178
remaining   590
ratified      0
```

All six selected meanings remain UNPLACED.
