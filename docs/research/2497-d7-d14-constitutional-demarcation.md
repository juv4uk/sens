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

### 2.1 Domain Text7 vs Sound7: Atlas Hygiene (#2490 Clarification)
- **Atlas Hygiene:** Under #2490, `D7` was originally reserved as `Sound7 + local ordinals` (acoustic/music synthesis). To prevent semantic collisions, the atlas strictly distinguishes:
  - **Text7 (UPC-7, textual phonetic geometry):** The 7-bit carrier for textual sounds, orthography, and phonetic sandhi.
  - **Sound7 (acoustic sound, in reserve):** The 7-bit carrier for audio/acoustic music synthesis.
  - Text7 and Sound7 are distinct domains despite sharing the 7-bit carrier width (`bits + domain + law -> semantic meaning`). Grammatical intervals and pratyāhāras belong strictly to Text7 and D14, NEVER to Sound7.
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

### 2.5 Machine Oracle Witness
- **Witness Address:** `shiva-sutras/prototype/verify_hakardvitva_c1p.py` (master: `e46b772`).
- **Command:** `python3 prototype/verify_hakardvitva_c1p.py` (runtime ~1.5 s, zero external dependencies).
- **Certified Invariants:**
  1. No hitting set of size $\le 3$ over 84 minimal 3-obstructions $\implies$ 42-sound linear ceiling is strictly $\le 39$.
  2. Unique size-4 hitting set $\mathcal{H}^* = \{\text{jhal}, \text{ral}, \text{val}, \text{śal}\}$ matches Sūtra 14 ($h_2$) in 1-to-1 bijection.
  3. 43-node path with dual $h_1/h_2$ achieves $43/43 = 100.0\%$ contiguous intervals.
