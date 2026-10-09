# D10: exact Bayesian update as a research-selected, unplaced candidate

Date: 2026-10-09. Source dossier: [#4956](https://github.com/juv4uk/sens/pull/4956). Owner coordination: [#4463](https://github.com/juv4uk/sens/issues/4463).

## Law

For a finite ordered hypothesis set, given exact-rational prior weights p_i in [0,1] with sum(p_i)=1, and exact likelihood values l_i in [0,1], define:

Z = sum_i(p_i * l_i).

If Z > 0, return the original-order exact posterior p'_i = p_i * l_i / Z and the exact evidence normalizer Z. If Z = 0, do not invent a uniform posterior; report an explicit undefined/zero-evidence condition. Reject malformed, inexact or out-of-range inputs. Preserve hypothesis order and entries whose posterior becomes zero.

Primary source: [Stanford Encyclopedia of Philosophy, Bayesian Epistemology, finite Bayes theorem](https://plato.stanford.edu/archives/sum2016/entries/epistemology-bayesian/). The finite formula gives the posterior by multiplying prior and likelihood and dividing by the sum of those products; the evidence term must be nonzero.

## Why this is tied to the owner's projects

This is an exact, substrate-independent observation update usable for symbolic AI / Advice Taker reasoning, Prolog hypotheses, astronomy candidate ranking and radio/SDR signal classification. It consumes exact numeric vectors; it makes no assumption about a telescope, ADC, FPGA, clock or specific sensor.

## Evidence and limitations

The source-only donor dossier #4956 and its independent common-denominator integer-weight oracle remain unchanged. The selected D10 row reproduces its witnesses and falsifiers. No runtime or physical .sens admission is claimed.

Important open question: the operation can be expressed as map/multiply + sum + divide over exact rationals. This PR therefore records research selection only. Whether a named finite update returning both posterior and evidence is a necessary D10 Core resident, or belongs in the exact-math/symbolic-inference library, is explicitly pending owner review.

## Authority boundary

The new row has coordinate=null, coordinate_basis=UNPLACED, ratified_resident=false, proposal_status=pending-owner-review, and physical_t5_authorized=false. The immutable historical D10 transition chain preserves 625→627→630→631→632→634→635. No D1–D9 row, coordinate, contract, compiler or runtime was changed.
