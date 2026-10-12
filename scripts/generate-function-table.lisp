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
(0011 registry-form (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))
(0011 registry-rows registry-form)
; Historical rows are retained only for migration/provenance consumers.
; Their eight-bit coordinates do not create canonical language identity.
(0011 entries registry-rows)

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(0011 machine-profile-form
  (100 (110101001 (110110111 "lib/machine/intel-core-i5-6400.lisp"))))

(0011 find-section
  (0010 (name sections)
    (110
      ((010 sections) (001 ()))
      
      ((101 (100 (100 sections)) name) (100 sections))
      ((010 (001 ())) (find-section name (011 sections))))))

(0011 machine-rows
  (011 (find-section (001 rows) (011 machine-profile-form))))

(0011 find-machine-row
  (0010 (sid rows)
    (110
      ((010 rows) (001 ()))
      
      ((11110111 (100 (100 rows)) sid) (100 rows))
      ((010 (001 ())) (find-machine-row sid (011 rows))))))

(0011 machine-path
  (0010 (sid)
    (001000 ((row (find-machine-row sid machine-rows)))
      (110 ((010 row) "()") ((010 (001 ())) (10011 row))))))

; Historical (McCarthy 1960 / Lisp 1.5) realization projection. Its rows
; never create an identity: they may only annotate IDs that already exist
; in `entries` above. Reverse-authority is forbidden by the contract file
; itself -- a historical name never mints a new my-lisp SID.
(0011 historical-profile-form
  (100 (110101001 (110110111 "contracts/core1-historical-sid-map.lisp"))))

(0011 historical-rows
  (011 (find-section (001 rows) (011 historical-profile-form))))

(0011 find-historical-row
  (0010 (sid rows)
    (110
      ((010 rows) (001 ()))
      
      ((11110111 (1001 (100 rows)) sid) (100 rows))
      ((010 (001 ())) (find-historical-row sid (011 rows))))))

(0011 mccarthy-label
  (0010 (sid)
    (001000 ((row (find-historical-row sid historical-rows)))
      (110 ((010 row) "()") ((010 (001 ())) (str+ (11110100 (100111 row)) " (" (11110100 (110110101 row)) ")"))))))

; A surface word is usually a symbol (write-to-string strips the
; Lisp-level Symbol wrapping down to bare text); the reconstructed
; apostrophe case above is already a plain string. For prose contexts
; (the human .md table) the bare apostrophe is fine either way.
(0011 surface-word-text
  (0010 (word)
    (110
      ((11110111 word (001 ())) "()")
      ((101 (string-membership-helper word) (class-membership string member))
       word)
      ((101 (string-membership-helper word) (class-membership string nonmember))
       (11110100 word)))))

; For the machine-readable .lisp output specifically, a bare apostrophe
; word must NOT be re-embedded unquoted: a future reader of this
; generated file would hit the exact same "'" quote-shorthand collision
; this script itself just worked around on the way in. write-to-string
; already does exactly the right thing per Value type -- a String gets
; quoted/escaped (read-back-safe), a Symbol stays bare -- so this is
; just write-to-string directly, named for what it's used for here.
(0011 surface-word-wsm-text write-to-string)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(0011 str+
  (0010 args (101110 (0010 (acc s) (110011110 acc s)) "" args)))

; SID already arrives from the registry as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(0011 find-surface
  (0010 (lang surfaces)
    (110
      ((010 surfaces) (001 ()))
      
      ((101 (100 (100 surfaces)) lang) (100 surfaces))
      ((010 (001 ())) (find-surface lang (011 surfaces))))))

(0011 surface-word
  (0010 (surface-entry)
    (110 ((010 surface-entry) (001 ())) ((010 (001 ())) (100 (011 surface-entry))))))

(0011 get-surface
  (0010 (lang surfaces)
    (surface-word (find-surface lang surfaces))))

(0011 surface-usable?
  (0010 (word)
    (0100 (11110111 word (001 ())))))

; --- formal identity stub: first present name among en/ук/sa, else bare id ---
; SID is already a first-class exact eight-bit identity. Its canonical printer
; preserves the exact spelling including leading zeroes; do not reinterpret it
; as arithmetic data merely to reconstruct the same source identity.
(0011 sid-bits
  (0010 (sid)
    (11110100 sid)))

(0011 formal-stub
  (0010 (sid surfaces)
    (001001 ((en (get-surface (001 en) surfaces))
           (ук (get-surface (001 ук) surfaces))
           (sa (get-surface (001 sa) surfaces)))
      (110
        ((surface-usable? en)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text en)))
        ((surface-usable? ук)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text ук)))
        ((surface-usable? sa)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text sa)))
        ((010 (001 ())) (110011110 "identity:" (sid-bits sid)))))))

; Historical projection intentionally has no 256-row completeness law.
; Exact domains grow under their own widths, occupancy maps, and admitted laws.

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(0011 join-newline-onto
  (0010 (strings acc)
    (110
      ((010 strings) acc)
      
      ((101 acc "") (join-newline-onto (011 strings) (100 strings)))
      ((010 (001 ())) (join-newline-onto (011 strings) (str+ acc "
" (100 strings)))))))

(0011 join-newline (0010 (strings) (join-newline-onto strings "")))

(0011 render-wsm-row
  (0010 (entry)
    (001001 ((sid (100 entry))
           (surfaces (011 entry))
           (ук (get-surface (001 ук) surfaces))
           (укр (get-surface (001 укр) surfaces))
           (en (get-surface (001 en) surfaces))
           (sa (get-surface (001 sa) surfaces))
           (sym (get-surface (001 sym) surfaces))
           (formal (formal-stub sid surfaces)))
      (str+
        "  (" (sid-bits sid) " " formal
        " (ук " (surface-word-wsm-text ук) ")"
        " (укр " (surface-word-wsm-text укр) ")"
        " (en " (surface-word-wsm-text en) ")"
        " (sa " (surface-word-wsm-text sa) ")"
        " (sym " (surface-word-wsm-text sym) ")"
        " my-lisp)"))))

(0011 render-md-row
  (0010 (entry)
    (001001 ((sid (100 entry))
           (surfaces (011 entry))
           (ук (get-surface (001 ук) surfaces))
           (укр (get-surface (001 укр) surfaces))
           (en (get-surface (001 en) surfaces))
           (sa (get-surface (001 sa) surfaces))
           (sym (get-surface (001 sym) surfaces)))
      (str+
        "| `" (sid-bits sid) "` | " (surface-word-text ук)
        " | " (surface-word-text укр)
        " | " (surface-word-text en)
        " | " (surface-word-text sa)
        " | " (surface-word-text sym)
        " | " (machine-path sid)
        " | " (mccarthy-label sid) " |"))))

(0011 wsm-header
  (1110
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

(0011 wsm-body (join-newline (1111 wsm-header (101000 render-wsm-row entries))))
(0011 wsm-output (110011110 wsm-body "
)
"))

(0011 md-header
  (1110
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

(0011 md-body (join-newline (1111 md-header (101000 render-md-row entries))))
(0011 md-output (110011110 md-body "
"))

(0011 wsm-output-path "lib/generated/function-table.lisp")
(0011 md-output-path "docs/generated/function-table.md")

(0011 write-projections
  (0010 ()
    (1001
      (1110
        (110111100 wsm-output-path wsm-output)
        (110111100 md-output-path md-output)
        (11011011
          (str+
            "function-table: "
            (110111001 (000000 entries))
            " historical projection rows written"))))))

(0011 check-projections
  (0010 ()
    (001000 ((current-wsm (110110111 wsm-output-path))
          (current-md (110110111 md-output-path)))
      (110
        ((11110111 current-wsm wsm-output)
         (1)
         (110
           ((11110111 current-md md-output)
            (1)
            (11011011
              (str+
                "function-table: "
                (110111001 (000000 entries))
                " historical projection rows current")))
           ((010 (001 ()))
            (1001
              (1110
                (11011011 "function-table markdown projection is stale")
                (100 (001 ())))))))
        ((010 (001 ()))
         (1001
           (1110
             (11011011 "function-table Lisp projection is stale")
             (100 (001 ())))))))))

(110
  ((010 *argv*)
   ()
   (write-projections))
  ((11110111 (100 *argv*) "--check")
   (1)
   (check-projections))
  ((010 (001 ()))
   (write-projections)))
