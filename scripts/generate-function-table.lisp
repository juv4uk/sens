; scripts/generate-function-table.lisp — regenerate the ECO-CANON-1 function
; table (my-lisp#75) from its real source of truth, written in my-lisp
; itself (2026-09-12), replacing the retired scripts/generate-function-table.py
; per issue #76 (ECO-LISP-SCRIPTS-1): repo-owned tooling must not add new
; Python scripting surface, and tooling should be written directly in
; my-lisp/wsm rather than migrated later.
;
; This script renders the historical flat registry only as a migration/review
; projection. Canonical language authority is exact domain identity + admitted
; law. Row count and legacy eight-bit position are not language invariants.
; Reads the historical surface registry as ordinary my-lisp data
; (read-file/read-all), not text/regex — the registry is already valid
; my-lisp source, so no foreign parser is needed.
;
; The human projection may also join processor-specific realization metadata.
; That metadata is deliberately NOT semantic authority: the Intel Core i5-6400
; profile is keyed by existing semantic IDs and only says how an already-known
; meaning can reach that processor's x86-64 ISA.
;
; Writes two generated views directly (write-file is language-owned,
; lib/fs.lisp, over the host's read-file-bytes/write-file-bytes):
;   lib/generated/function-table.lisp  (schema ft/2, machine-readable projection)
;   docs/generated/function-table.md  (human table, column order
;     ук -> укр -> English -> Sanskrit -> Intel Core i5-6400 / Skylake)
;
; Usage (from the repo root):
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
;
; `ук` is the current/compact Ukrainian surface.
; `укр` is the full Ukrainian peer surface of the SAME semantic identity.
; Both are read directly from semantic-registry.lisp; this generator never
; invents names and never duplicates `укр` under another full-UK column.

; Registry surfaces are fixed two-element rows: (namespace spelling-or-()).
; Reader-sensitive spellings such as apostrophe are serialized as strings, so the
; registry remains ordinary re-readable Lisp data without a special reconstruction path.
(визначити registry-form (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))
(визначити registry-rows registry-form)
; Historical rows are retained only for migration/provenance consumers.
; Their eight-bit coordinates do not create canonical language identity.
(визначити entries registry-rows)

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(визначити machine-profile-form
  (перше (читати-всі (читати-файл "lib/machine/intel-core-i5-6400.lisp"))))

(визначити find-section
  (функція (name sections)
    (за-умовою
      ((атом? sections) (як-є ()))
      
      ((тотожне? (перше (перше sections)) name) (перше sections))
      ((атом? (як-є ())) (find-section name (решта sections))))))

(визначити machine-rows
  (решта (find-section (як-є rows) (решта machine-profile-form))))

(визначити find-machine-row
  (функція (sid rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      
      ((однакові? (перше (перше rows)) sid) (перше rows))
      ((атом? (як-є ())) (find-machine-row sid (решта rows))))))

(визначити machine-path
  (функція (sid)
    (нехай ((row (find-machine-row sid machine-rows)))
      (за-умовою ((атом? row) "()") ((атом? (як-є ())) (третє row))))))

; Historical (McCarthy 1960 / Lisp 1.5) realization projection. Its rows
; never create an identity: they may only annotate IDs that already exist
; in `entries` above. Reverse-authority is forbidden by the contract file
; itself -- a historical name never mints a new my-lisp SID.
(визначити historical-profile-form
  (перше (читати-всі (читати-файл "contracts/core1-historical-sid-map.lisp"))))

(визначити historical-rows
  (решта (find-section (як-є rows) (решта historical-profile-form))))

(визначити find-historical-row
  (функція (sid rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      
      ((однакові? (друге (перше rows)) sid) (перше rows))
      ((атом? (як-є ())) (find-historical-row sid (решта rows))))))

(визначити mccarthy-label
  (функція (sid)
    (нехай ((row (find-historical-row sid historical-rows)))
      (110 ((010 row) "()") ((010 (001 ())) (str+ (11110100 (100111 row)) " (" (11110100 (110110101 row)) ")"))))))

; A surface word is usually a symbol (write-to-string strips the
; Lisp-level Symbol wrapping down to bare text); the reconstructed
; apostrophe case above is already a plain string. For prose contexts
; (the human .md table) the bare apostrophe is fine either way.
(визначити surface-word-text
  (функція (word)
    (за-умовою
      ((однакові? word (як-є ())) "()")
      ((тотожне? (класифікувати-рядкове-значення word) (class-membership string member))
       word)
      ((тотожне? (класифікувати-рядкове-значення word) (class-membership string nonmember))
       (значення-у-текст word)))))

; For the machine-readable .lisp output specifically, a bare apostrophe
; word must NOT be re-embedded unquoted: a future reader of this
; generated file would hit the exact same "'" quote-shorthand collision
; this script itself just worked around on the way in. write-to-string
; already does exactly the right thing per Value type -- a String gets
; quoted/escaped (read-back-safe), a Symbol stays bare -- so this is
; just write-to-string directly, named for what it's used for here.
(визначити surface-word-wsm-text write-to-string)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(визначити str+
  (функція args (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

; SID already arrives from the registry as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(визначити find-surface
  (функція (lang surfaces)
    (за-умовою
      ((атом? surfaces) (як-є ()))
      
      ((тотожне? (перше (перше surfaces)) lang) (перше surfaces))
      ((атом? (як-є ())) (find-surface lang (решта surfaces))))))

(визначити surface-word
  (функція (surface-entry)
    (за-умовою ((атом? surface-entry) (як-є ())) ((атом? (як-є ())) (перше (решта surface-entry))))))

(визначити get-surface
  (функція (lang surfaces)
    (surface-word (find-surface lang surfaces))))

(визначити surface-usable?
  (функція (word)
    (хибне? (однакові? word (як-є ())))))

; --- formal identity stub: first present name among en/ук/sa, else bare id ---
; SID is already a first-class exact eight-bit identity. Its canonical printer
; preserves the exact spelling including leading zeroes; do not reinterpret it
; as arithmetic data merely to reconstruct the same source identity.
(визначити sid-bits
  (функція (sid)
    (значення-у-текст sid)))

(визначити formal-stub
  (функція (sid surfaces)
    (нехай-послідовно ((en (get-surface (як-є en) surfaces))
           (ук (get-surface (як-є ук) surfaces))
           (sa (get-surface (як-є sa) surfaces)))
      (за-умовою
        ((surface-usable? en)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text en)))
        ((surface-usable? ук)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text ук)))
        ((surface-usable? sa)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text sa)))
        ((атом? (як-є ())) (рядок-додати "identity:" (sid-bits sid)))))))

; Historical projection intentionally has no 256-row completeness law.
; Exact domains grow under their own widths, occupancy maps, and admitted laws.

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(визначити join-newline-onto
  (функція (strings acc)
    (за-умовою
      ((атом? strings) acc)
      
      ((тотожне? acc "") (join-newline-onto (решта strings) (перше strings)))
      ((атом? (як-є ())) (join-newline-onto (решта strings) (str+ acc "
" (перше strings)))))))

(визначити join-newline (функція (strings) (join-newline-onto strings "")))

(визначити render-wsm-row
  (функція (entry)
    (нехай-послідовно ((sid (перше entry))
           (surfaces (решта entry))
           (ук (get-surface (як-є ук) surfaces))
           (укр (get-surface (як-є укр) surfaces))
           (en (get-surface (як-є en) surfaces))
           (sa (get-surface (як-є sa) surfaces))
           (sym (get-surface (як-є sym) surfaces))
           (formal (formal-stub sid surfaces)))
      (str+
        "  (" (sid-bits sid) " " formal
        " (ук " (surface-word-wsm-text ук) ")"
        " (укр " (surface-word-wsm-text укр) ")"
        " (en " (surface-word-wsm-text en) ")"
        " (sa " (surface-word-wsm-text sa) ")"
        " (sym " (surface-word-wsm-text sym) ")"
        " my-lisp)"))))

(визначити render-md-row
  (функція (entry)
    (нехай-послідовно ((sid (перше entry))
           (surfaces (решта entry))
           (ук (get-surface (як-є ук) surfaces))
           (укр (get-surface (як-є укр) surfaces))
           (en (get-surface (як-є en) surfaces))
           (sa (get-surface (як-є sa) surfaces))
           (sym (get-surface (як-є sym) surfaces)))
      (str+
        "| `" (sid-bits sid) "` | " (surface-word-text ук)
        " | " (surface-word-text укр)
        " | " (surface-word-text en)
        " | " (surface-word-text sa)
        " | " (surface-word-text sym)
        " | " (machine-path sid)
        " | " (mccarthy-label sid) " |"))))

(визначити wsm-header
  (список
    "; GENERATED — DO NOT EDIT BY HAND"
    "; HISTORICAL MIGRATION PROJECTION — NOT SEMANTIC AUTHORITY"
    "; Donor: lib/surface/semantic-registry.lisp"
    "; Generator: scripts/generate-function-table.lisp"
    "; Schema ft/2: (legacy-bitstring formal ук укр en sa sym projection)"
    "; ук = current Ukrainian; укр = full Ukrainian peer surface"
    "; Display order for humans: ук → укр → English → Sanskrit"
    "; projection = historical/migration review only"
    ""
    "(ft/2"))

(визначити wsm-body (join-newline (приєднати wsm-header (відобразити render-wsm-row entries))))
(визначити wsm-output (рядок-додати wsm-body "
)
"))

(визначити md-header
  (список
    "# Function table (generated projection)"
    ""
    "**Status:** historical migration projection. Canonical identity comes from exact domains and admitted laws, not this flat table."
    ""
    "**Machine projection:** `lib/machine/intel-core-i5-6400.lisp` — physical execution paths only; it does not create language meaning."
    ""
    "**Historical projection:** `contracts/core1-historical-sid-map.lisp` — one-way SID → McCarthy 1960 / Lisp 1.5 mechanism comparison, pinned against `juv4uk/mccarthy-eval`; it never mints a new identity and does not create language meaning."
    ""
    "Regenerate: `cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp`"
    ""
    "| ID | ук | укр | English | Sanskrit | Symbol | Intel Core i5-6400 / Skylake | McCarthy 1960 / Lisp 1.5 (Core1) |"
    "|----|----|-----|---------|----------|--------|------------------------------|-----------------------------------|"))

(визначити md-body (join-newline (приєднати md-header (відобразити render-md-row entries))))
(визначити md-output (рядок-додати md-body "
"))

(визначити wsm-output-path "lib/generated/function-table.lisp")
(визначити md-output-path "docs/generated/function-table.md")

(визначити write-projections
  (функція ()
    (друге
      (список
        (записати-файл wsm-output-path wsm-output)
        (записати-файл md-output-path md-output)
        (11011011
          (str+
            "function-table: "
            (число-рядок (довжина entries))
            " historical projection rows written"))))))

; The projection payloads and argv selector below are strings, hence atoms.
; Use exact D3:101 EQ (3 bits), not the wider D8:11110111 structural EQUAL.
; This is a source-identity narrowing only; no physical T5 size claim follows.
(визначити check-projections
  (функція ()
    (нехай ((current-wsm (читати-файл wsm-output-path))
          (current-md (читати-файл md-output-path)))
      (за-умовою
        ((тотожне? current-wsm wsm-output)
         (за-умовою
           ((тотожне? current-md md-output)
            (11011011
              (str+
                "function-table: "
                (число-рядок (довжина entries))
                " historical projection rows current")))
           ((атом? (як-є ()))
            (друге
              (список
                (друкувати "function-table markdown projection is stale")
                (перше (як-є ())))))))
        ((атом? (як-є ()))
         (друге
           (список
             (друкувати "function-table Lisp projection is stale")
             (перше (як-є ())))))))))

(за-умовою
  ((атом? *argv*)
   (write-projections))
  ((тотожне? (перше *argv*) "--check")
   (check-projections))
  ((атом? (як-є ()))
   (write-projections)))
