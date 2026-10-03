# #2628 — shared-location root minimization

Phase: **SENS-DERIVATION**
Factor: `shared-location-update`
Width: **UNKNOWN**
Coordinate: **UNPLACED**

## Result

```text
GLOBAL-D4-COMPILABLE = yes
DERIVED-D4-LOCAL     = no
ROOT-STATUS          = CARRIER-PREMISE
ROOT-PROMOTED        = no
```

This sharpens the older #2442 result rather than replacing it.

The explicit-state D4 model can encode frames, location IDs and an immutable
store as ordinary data. It can reproduce nearest-existing lookup, update,
aliases, shadowing and fail-on-miss.

But its observer protocol is:

```text
observer(store)
```

while the original source-boundary observation is an already-created:

```text
observer()
```

that sees the new value of the same shared location after another scope
updates it.

With immutable persistent data, computing `new_store` cannot retroactively
change the store captured by an unchanged zero-argument closure. The existing
observer continues to see OLD. It sees NEW only if we do one of four things:

1. pass the new store explicitly;
2. mutate its captured location/store;
3. let it read an implicit current/global store;
4. replace/rewrite the observer.

The first and fourth are whole-program protocol rewrites. The second and third
import the very ambient/shared-location carrier under study.

Under the project-wide #2468 derivation rule, this is therefore not a local D4
derivation. At the same time, the mutation algorithm itself is not promoted to
a new semantic root: once the carrier is explicit, the computation is ordinary
D3/D4 data transformation.

The conservative bounded classification is:

```text
CARRIER-PREMISE = ambient-current-store/shared-location
```

### Falsifier

A context-preserving D1-D4 replacement that leaves existing zero-argument
observers/callers unchanged and still makes them observe the nearest existing
location's new value without importing an ambient or mutable store/location
channel defeats this classification.

No D5/D6 residency follows.
