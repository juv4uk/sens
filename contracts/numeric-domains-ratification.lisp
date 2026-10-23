; Ратифіковано безпосередньо власником 2026-10-11: D24/D48/D96/D192/... = повні домени SENS.
; Рівні D1-D9; не позадоменні рівні зберігання Number24. Точний домен
; обов'язковий для тлумачення точного бінарного слова. Числові літерали не потрібні.
(
  (schema . numeric-domains-ratification-1)
  (status . owner-ratified)
  (owner-ratification . "owner direct decision 2026-10-11")
  (date . "2026-10-11")
  (family . numeric)
  (rank . peer-of-D1-D9)
  (first-domain . D24)
  (initial-width . #d24)
  (next-width . double)
  (canonical-domain-names . (D24 D48 D96 D192))
  (domain-rule . "D(24 * 2^n), n >= 0")
  (historical-map-status . "Retired on 2026-10-24; this Lisp contract is the current authority.")
  (laws
    . ((identity . "exact binary bits + explicit numeric domain + domain law")
       (equal-rank . "D24/D48/... are semantic domains with equal ontology rank to D1-D9")
       (role-distinction . "numeric domain laws do not collapse into D1 predicates, D2 structure, D7 text or function domains")
       (arithmetic-exclusivity . "Only explicitly domain-qualified D24/D48/D96/... atoms and their canonical same-domain NEG/RATIO compositions may participate in mathematical + - * / or numeric < > =. D1-D10 are exact binary-digit semantic words, never arithmetic operands or inferred numbers. Legacy Number/Rational and unqualified BinaryNumber cannot bypass this rule. D5/D6 function-code identities selecting arithmetic operators are not themselves mathematical values; D3 EQ and D1 predicate logic are separate non-arithmetic laws.")
       (no-inference . "bits, width alone, human literals, and host storage cannot confer numeric-domain membership")
       (non-collapse . "D24 and D48 remain distinct domain identities even if payload magnitude coincides")
       (no-literals-required . "numeric source tokens are optional projection, not semantic identity")
       (admission-scope . "The Dn law now admits all 2^n exact n-bit words specifically as natural numeric atoms; this does NOT allocate unrelated function roles, additional signed/rational scalar atoms or execution mechanisms")
       (same-domain-natural-addition . "For admitted natural a,b both in exact Dn, compute exact a+b with carry; if sum fits in n bits then result is exact Dn; otherwise the n+1-bit sum is carried in exact D(2n), the next owner-ratified numeric domain. For two n-bit natural operands the sum never needs more than n+1 significant bits.")
       (add-carry-preservation . "No n-bit truncation, wraparound or modulo 2^n; exact output is left-zero-filled to its selected domain width. Explicit Dn/D(2n) identity is retained and is not inferred from normalized magnitude alone.")
       (addition-bridge-scope . "Only same-Dn exact natural ADD/MUL may promote Dn to D(2n) based on significant result bits. SUB and exact integer DIV stay Dn. NEG/RATIO mathematical composition never authorizes a new opcode, unqualified value or mixed-Dn coercion.")
       (same-domain-natural-multiplication . "For admitted a,b both natural Dn atoms, the exact product uses at most 2n significant bits. If it fits n bits the result is Dn, otherwise the full product is admitted into D(2n). Never truncate, wrap or infer mixed-domain coercion.")
       (same-domain-natural-subtraction . "For admitted natural a,b of same Dn, a>=b yields exact Dn difference; a<b mathematically requires canonical NEG(b-a) and must fail closed in the Core evaluator until NEG composite execution is admitted.")
       (same-domain-natural-division . "For admitted natural a,b in same Dn and b>0, exact Euclidean quotient and remainder are Dn atoms with a=b*q+r and 0<=r<b. Division as integer is allowed only when r=0; otherwise RATIO composition remains unimplemented and Core must reject rather than round. b=0 must fail.")
       (base-natural-occupancy . "All 2^n n-bit Dn base words remain unsigned natural atoms 0..2^n-1; no bit is stolen for sign, type or rational denominator.")
       (signed-composition . "NEG(x) is the canonical sign law on strictly nonzero admitted Dn natural magnitude x; NEG(0) collapses to existing Dn zero, never a second negative zero. This operation is a D24+ numeric-domain composition, not a new domain and not an added n-bit atom.")
       (rational-composition . "RATIO(p,q), q>0, gcd(abs(p),q)=1. p is a natural or canonically negated natural; zero numerator collapses to numeric-domain zero; denominator one collapses to the signed or natural integer. Reduced non-integral denominator is >1.")
       (composite-identity . "A NEG or RATIO result is an explicitly composed numeric object over exact constituent D24/D48/... natural domain identities and a law, not a single flat n-bit Dn word or a host tuple claiming semantic status. Preserve both constituent domains; do not infer cross-domain equality/coercion from magnitude.")
       (canonicalization . "Use exact binary gcd/division without rounding; reject denominator zero, negative denominator and ambiguous negative zero. Sign and fraction do not reduce natural Dn atom capacity.")
       (numeric-composition-runtime . "Core executes exact canonical NEG and reduced RATIO Values for same-Dn operands under existing arithmetic operator identities + - * / and D1 comparisons, including unary NEG/reciprocal. Negative zero and denominator zero forbidden; operations normalize gcd and select the smallest successor numeric Dn containing both components, never truncate or round. No new domains, no stolen natural bits, no invented physical binary operation codes.")
       (composite-growth . "For an admitted same-domain Dn operation producing canonical NEG/RATIO components, select the smallest rung D(24*2^k) not narrower than the input Dn and holding the fully reduced numerator and denominator. Growth is a result rule, never implicit mixed-domain operand conversion.")
       (deferred . "physical NEG/RATIO opcode/source-expression/reader and FASL/wire composition encoding, external kernel execution, polarity/two's-complement representation, other-operation overflow policies beyond admitted numeric laws, mixed-domain implicit bridges, decimal lowering")
       (runtime-status . "Core BinaryNumber and evaluator admit same-Dn natural ADD/MUL, nonnegative SUB, exact integer DIV and canonical signed/rational NEG/RATIO Values. Physical composite serialization, text/source macro reification and mixed-domain arithmetic are not admitted.")))
)

; Чинне уточнення власника 2026-10-18. Форму 2026-10-11 вище збережено як
; історію; для інтерпретації цілих чисел D24+ цей закон її переважає.
(
  (schema . numeric-d24-signed-extension-1)
  (status . owner-ratified)
  (owner-decision . "2026-10-18: D24+ integers use fixed-width two's complement; fractions retain existing NEG/RATIO composition")
  (scope . "D24, D48, D96, D192, ... exact-width integer words only; D1-D10 unchanged")
  (integer-law . "For exact n-bit Dn word u, value=u when MSB=0, otherwise value=u-2^n; range is -2^(n-1)..2^(n-1)-1. Every word denotes exactly one integer; there is no negative zero.")
  (arithmetic . "Same-Dn + - * / and comparisons are exact. If an integer result does not fit signed Dn, widen to the smallest allowed D24+ successor that fits. Never wrap, truncate, round, infer domain identity, or coerce mixed Dn operands.")
  (fraction-law . "Keep the existing exact reduced ratio composition: explicit sign plus unsigned numerator magnitude and positive unsigned denominator magnitude; gcd reduction, denominator zero rejected, zero and denominator one canonicalize as before. Integer two's-complement words do not replace the fraction composition.")
  (transport . "T5M transports already-formed exact-width words unchanged; it does not assign numeric meaning. Physical NEG/RATIO serialization remains separate.")
)

; Чинне рішення власника 2026-10-24: математична драбина починається з D12.
; Цей закон переважає мінімальну ширину D24 у записах 2026-10-11/18.
; Старі записи лишаються історією і свідченням чинного D24+ механізму.
; Ратифікація семантики не є доказом реалізації D12 у Core/Zig/T5M.
(
  (schema . numeric-d12-start-extension-1)
  (status . owner-ratified)
  (date . "2026-10-24")
  (owner-decision . "Математичні числові домени SENS починаються з D12+; D12 є найменшим повноцінним числовим доменом для малих точних значень і простих тестів.")
  (authority . "This owner decision supersedes the D24-first width/name law in the 2026-10-11 ratification and its 2026-10-18 D24+ scope only as to the FIRST numeric rung; unchanged D24+ identities remain valid.")
  (family . numeric)
  (first-domain . D12)
  (initial-width . #d12)
  (next-width . double)
  (canonical-domain-names . (D12 D24 D48 D96 D192))
  (domain-rule . "D(12 * 2^n), n >= 0")
  (integer-law . "D12 and every successor Dn use exact n-bit two's-complement words; D12 range is -2048..2047. Every word has one integer value, with no negative zero.")
  (arithmetic . "For same-Dn admitted operands, exact mathematical + - * / and comparison preserve value; a signed integer result outside Dn widens to the smallest admitted successor D(2n), without wrapping or truncation. Mixed-Dn coercion is not implied.")
  (fraction-law . "Exact reduced RATIO remains a semantic composition of admitted integer magnitudes with positive denominator, gcd reduction and no rounding; denominator zero is invalid, zero numerator and unit denominator canonicalize. Float is distinct and never an implicit replacement for exact RATIO.")
  (identity-law . "D12 is a numeric domain, not a D12 callable-function codebook, not D7 text, not a width-only inference and not a source literal. D12 and D24 identities remain distinct even at equal mathematical values.")
  (transport-law . "T5M/Zig carry already-admitted exact domain and payload bits; codec padding or byte framing never decides arithmetic identity, sign, ratio or float semantics.")
  (implementation-status . "Owner-ratified semantic law only; legacy D24-first generated constants, guards, Core admission and Zig physical prefix still require explicit migration and execution tests before D12 is reported operational.")
  (current-normative-source . "contracts/numeric-domains-ratification.lisp")
)
