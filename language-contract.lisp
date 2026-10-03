; language-contract.lisp — current machine-readable Level 1/2 contract.
;
; Contract 11.0 — domain-qualified binary ontology.
; Authority: #2490 #1706, ratified D1-D4 #2155 #2158 #2162,
; ratified D5/D6 owner maps #2414.
;
; Breaking change from Contract 10:
; exact-eight Function8/Sens8 is no longer the universal semantic identity.
; Canonical semantic identity is exact bits + exact domain + admitted/proved law.
; Historical Contract 10 is preserved at
; docs/archive/historical/language-contract-10.0.lisp.
;
; Compatibility Sens8/Sid8 may remain only behind explicit transition,
; transport or backend-mechanism boundaries. It may not silently reconstruct
; D3/D4/D5/D6 identity by truncation, extension or packed numeric equality.

((major . #d11) (minor . 0)
 (note . "RATIFIED domain ontology from #2490/#1706. Contract 11.0 replaces the universal flat Function8 identity with exact binary objects in explicit domains. D1 PredicateBit, D2 structure, D3 foundation and D4 bootstrap have ratified exact maps; D5/D6 owner maps are ratified but executable admission remains separately gated. Legacy Sens8/Sid8 is compatibility/mechanism only, never canonical identity.")
 (covers . (G1 G2 G3 G4 G5 G6 G7 G8 S1 S2 S3))
 (invariants
   . ((binary-domain-identity
       . "Every canonical semantic object is an exact binary object inside an explicit semantic domain and interpreted by an admitted/proved law. Equal packed bits in different domains do not imply equal identity or meaning.")
      (domain-is-interpretation-boundary
       . "A domain is the explicit carrier/admissibility and law context for its residents. It is not required to be another resident of itself. Reified domain metadata is a separate object in a separately declared meta-domain.")
      (core-d1-map
       . "Core.D1 PredicateBit is exactly one bit: 0 NO and 1 YES. PredicateBit is not Number, host Bool, T/NIL, Symbol or structural ().")
      (core-d2-map
       . "Core.D2 structure is exactly: 00 separator, 01 close, 10 open, 11 dot. Equal packed values in other domains never alias these structural roles.")
      (core-d3-map
       . "Core.D3 foundation is exactly: 000 structural empty (), 001 QUOTE, 010 ATOM, 011 COND, 100 CONS, 101 CAR, 110 CDR, 111 EQ. The old eight-bit Function8 coordinates are not canonical D3 identity.")
      (core-d4-map
       . "Core.D4 bootstrap is exactly: 0000 APPLY, 0001 EVAL, 0010 LAMBDA, 0011 DEFINE, 0100 NOT, 0101 unallocated, 0110 EVCON, 0111 EVLIS, 1000 LIST, 1001 unallocated, 1010 CAAR, 1011 CADR, 1100 CDAR, 1101 CDDR, 1110 LOOKUP, 1111 BIND. Residency does not imply primitiveness.")
      (d4-free-fail-closed
       . "Core.D4 words 0101 and 1001 are unallocated and must fail closed in canonical semantic admission. No legacy Function8 low bits may populate them.")
      (d5-d6-owner-map-boundary
       . "Core.D5 and Core.D6 owner maps are ratified exact-width domain occupancy records. Occupancy is not by itself runtime/evaluator/compiler admission; those layers must preserve the exact domain and pass their own gates.")
      (callable-domain-boundary
       . "Callable Core identity is domain-qualified. Current callable strata are D3/D4 and admitted residents of D5/D6. D1 predicates, D2 structure and D7 Sound/local ordinals do not become callable merely because they are binary.")
      (legacy-sens8-compatibility
       . "Sens8/Sid8/Function8 is a historical compatibility, transport or backend-mechanism representation only. Canonical semantic layers must not infer D3/D4/D5/D6 identity from an eight-bit value by zero-extension, truncation, low bits, packed numeric equality or human-name lookup.")
      (single-unnamed-binary-ontology
       . "There is no second human-named function ontology. Host enums and mechanism tags may represent already-selected domain identities, but names/opcodes/backend identifiers never own language meaning.")
      (surface-non-authority
       . "Human-language and symbolic surfaces are optional source/UI routing metadata only. A spelling never creates a semantic object, owns meaning or becomes canonical identity.")
      (atom-d3-law
       . "Core.D3 010 ATOM has one foundation law: structural empty () and every admitted non-pair value answer PredicateBit 1; pair answers PredicateBit 0. Structural () is an ATOM-yes subject, not a truth value.")
      (eq-d3-law
       . "Core.D3 111 EQ has one foundation law: the same admitted atom answers PredicateBit 1; distinct admitted atoms answer PredicateBit 0; pair/out-of-domain input raises the named domain/type failure. EQ is not deep structural equality.")
      (cond-d3-law
       . "Core.D3 011 COND evaluates two-field clauses (test expression) left-to-right. Tests must return exact PredicateBit. 1 selects/evaluates the expression, 0 skips it, and exhaustion returns structural ().")
      (reader-apostrophe
       . "At expression start, apostrophe is reader sugar whose canonical operation identity is Core.D3 001 QUOTE. Inside an identifier, apostrophe remains an ordinary Unicode character at the human/source projection boundary.")
      (reader-exact-width
       . "Canonical visible-binary source preserves each word's exact width and leading zeroes. Width is never recovered from host numeric value. A source word gains semantic identity only through explicit domain admission; exactly eight bare bits are not a universal function rule.")
      (reader-decimal-separator
       . "Dot and comma are equivalent decimal separators only for otherwise valid finite decimal/base-10 scientific numeric input. Non-numeric tokens retain their data behavior; this rule never creates a semantic domain identity.")
      (kernel-archipelago
       . "Execution kernels consume already-selected domain-qualified identities or explicitly tagged legacy compatibility identities plus arguments/context. Kernel operator names, opcodes and native types never acquire SENS semantic identity by themselves.")
      (domain-separation
       . "Semantic-law identity never follows from the bit transform alone. A transform repeated in two domains remains two semantic laws unless an explicit cross-domain proof establishes a bridge.")
      (migration-debt-flat8
       . "Any canonical AST, runtime value, registry, environment slot or compiler IR that still uses bare Sens8/Sid8 as universal identity is named migration debt under #2817/#2822. Compatibility adapters must be explicit and removable."))))
