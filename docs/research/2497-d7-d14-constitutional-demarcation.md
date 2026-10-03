# Constitutional Demarcation between D7 and D14

**Status:** Ratified Architectural Decision  
**Date:** 2026-10-03  
**Authority:** Owner Directive (#2490, #2494, #2497)  
**Evidence:** `shiva-sutras` PR #113 (`docs/hakardvitva-c1p-topological-necessity.md`), `prototype/verify_hakardvitva_c1p.py`  
**Related Issues:** #2497, #2432, #2756, #2415, #1413

---

## 1. Summary of the Incompatibility Theorem

Over the 42 unique sounds of Sanskrit, the 43 canonical pratyāhāras violate the Consecutive Ones Property (C1P). An exhaustive hypergraph transversal over all 84 minimal 3-element Tucker obstructions (asteroidal triples) proves that **no linear ordering can achieve more than 39 contiguous pratyāhāras**. The lower bound of 39 is constructively achieved by prototype L when omitting the unique minimum transversal:
$$\mathcal{H}^* = \{\text{jhal}, \text{ral}, \text{val}, \text{śal}\}$$

Furthermore, splitting the sound `ha` into two distinct topological nodes ($h_1$ at Sūtra 5 and $h_2$ at Sūtra 14)—exactly matching Pāṇini's recitation (*hakāradvitva*, as analyzed by Patañjali in the *Mahābhāṣya*)—resolves the obstruction completely, yielding **43/43 (100.0%)** contiguous intervals.

Consequently, articulatory geometry (2D place $\times$ effort matrix) and grammatical path intervals (1D Hamiltonian walk with duplicate $h$) **cannot coexist in a single 1-to-1 linear layout of 42 cells**.

---

## 2. Constitutional Domain Law

SENS resolves this mathematical incompatibility not by a compromised synthetic encoding, but through strict domain separation under the constitutional principle:
$$\mathbf{A\ domain\ owns\ the\ law\ it\ operates.}$$

### 2.1 Domain D7 (Text7, 7-bit carrier): Phonetic Geometry
- **Law:** Articulatory place (*sthāna*) and effort (*prayatna*).
- **Consumer:** Orthography, phonetic sandhi, script transcription, surface representation.
- **Representation:** Pinned UPC-7 table (`upc7-table.tsv`).
- **Operation:** Bitwise place/effort masks yielding $O(1)$ *savarṇa* verification.
- **Firewall:** The 21 unallocated cells in Text7 remain strictly reserved under #2494. Injecting foreign sūtra ordinals into Text7 is forbidden.

### 2.2 Domain D14 (14-bit carrier): Grammatical Class Graph
- **Law:** The 43-node Śiva-sūtra path with dual $h_1$ and $h_2$.
- **Consumer:** Pāṇinian grammatical derivation engine, morphology, rule condition dispatch.
- **Representation:** The 43-node traversal graph of the 14 Śiva-sūtras.
- **Operation:** $O(1)$ integer interval comparisons $[start \dots end]$ (`(x - start) <= (end - start)`).

### 2.3 Word-Level Bitmasks (`u64`): Compiled Mechanism Cache
- 64-bit integer masks over the 42 sounds are **strictly compiled mechanism caches**.
- They reside in hot execution paths for fast set intersections.
- They possess **no semantic authority**. They are deterministically generated from D14 and can be invalidated or recomputed at will.

### 2.4 Synthetic Hybrids Rejected
Any synthetic hybrid layout attempting to interleave sūtra prefixes with articulatory suffixes is rejected as ungrounded complexity (#2494).
