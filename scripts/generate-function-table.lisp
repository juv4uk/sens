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
(00001001 registry-form (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))
(00001001 registry-rows registry-form)
; Historical rows are retained only for migration/provenance consumers.
; Their eight-bit coordinates do not create canonical language identity.
(00001001 entries registry-rows)

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(00001001 machine-profile-form
  (00000101 (01001011 (10100110 "lib/machine/intel-core-i5-6400.lisp"))))

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (1) (00000001 ()))
      ((00000011 (00000101 (00000101 sections)) name) (00000101 sections))
      (t (find-section name (00000110 sections))))))

(00001001 machine-rows
  (00000110 (find-section (00000001 rows) (00000110 machine-profile-form))))

(00001001 find-machine-row
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((00000010 rows) (1) (00000001 ()))
      ((00100010 (00000101 (00000101 rows)) sid) (00000101 rows))
      (t (find-machine-row sid (00000110 rows))))))

(00001001 machine-path
  (00001000 (sid)
    (10011100 ((row (find-machine-row sid machine-rows)))
      (00000111
        ((00000010 row) () "()")
        ((00000010 row) (1) "()")
        (t (00110000 row))))))

; Historical (McCarthy 1960 / Lisp 1.5) realization projection. Its rows
; never create an identity: they may only annotate IDs that already exist
; in `entries` above. Reverse-authority is forbidden by the contract file
; itself -- a historical name never mints a new my-lisp SID.
(00001001 historical-profile-form
  (00000101 (01001011 (10100110 "contracts/core1-historical-sid-map.lisp"))))

(00001001 historical-rows
  (00000110 (find-section (00000001 rows) (00000110 historical-profile-form))))

(00001001 find-historical-row
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((00000010 rows) (1) (00000001 ()))
      ((00100010 (00101111 (00000101 rows)) sid) (00000101 rows))
      (t (find-historical-row sid (00000110 rows))))))

(00001001 mccarthy-label
  (00001000 (sid)
    (10011100 ((row (find-historical-row sid historical-rows)))
      (00000111
        ((00000010 row) () "()")
        ((00000010 row) (1) "()")
        (t (str+ (01001100 (00110001 row)) " (" (01001100 (00110010 row)) ")"))))))

; A surface word is usually a symbol (write-to-string strips the
; Lisp-level Symbol wrapping down to bare text); the reconstructed
; apostrophe case above is already a plain string. For prose contexts
; (the human .md table) the bare apostrophe is fine either way.
(00001001 surface-word-text
  (00001000 (word)
    (00000111
      ((00100010 word (00000001 ())) "()")
      ((string-membership-helper word)
       (class-membership string member)
       word)
      ((string-membership-helper word)
       (class-membership string nonmember)
       (01001100 word)))))

; For the machine-readable .lisp output specifically, a bare apostrophe
; word must NOT be re-embedded unquoted: a future reader of this
; generated file would hit the exact same "'" quote-shorthand collision
; this script itself just worked around on the way in. write-to-string
; already does exactly the right thing per Value type -- a String gets
; quoted/escaped (read-back-safe), a Symbol stays bare -- so this is
; just write-to-string directly, named for what it's used for here.
(00001001 surface-word-wsm-text write-to-string)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(00001001 str+
  (00001000 args (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

; SID already arrives from the registry as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(00001001 find-surface
  (00001000 (lang surfaces)
    (00000111
      ((00000010 surfaces) () (00000001 ()))
      ((00000010 surfaces) (1) (00000001 ()))
      ((00000011 (00000101 (00000101 surfaces)) lang) (00000101 surfaces))
      (t (find-surface lang (00000110 surfaces))))))

(00001001 surface-word
  (00001000 (surface-entry)
    (00000111
      ((00000010 surface-entry) () (00000001 ()))
      ((00000010 surface-entry) (1) (00000001 ()))
      (t (00000101 (00000110 surface-entry))))))

(00001001 get-surface
  (00001000 (lang surfaces)
    (surface-word (find-surface lang surfaces))))

(00001001 surface-usable?
  (00001000 (word)
    (00100001 (00100010 word (00000001 ())))))

; --- formal identity stub: first present name among en/ук/sa, else bare id ---
; SID is already a first-class exact eight-bit identity. Its canonical printer
; preserves the exact spelling including leading zeroes; do not reinterpret it
; as arithmetic data merely to reconstruct the same source identity.
(00001001 sid-bits
  (00001000 (sid)
    (01001100 sid)))

(00001001 formal-stub
  (00001000 (sid surfaces)
    (10011101 ((en (get-surface (00000001 en) surfaces))
           (ук (get-surface (00000001 ук) surfaces))
           (sa (get-surface (00000001 sa) surfaces)))
      (00000111
        ((surface-usable? en)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text en)))
        ((surface-usable? ук)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text ук)))
        ((surface-usable? sa)
         (str+ "identity:" (sid-bits sid) "/surface:" (surface-word-text sa)))
        (t (00111010 "identity:" (sid-bits sid)))))))

; Historical projection intentionally has no 256-row completeness law.
; Exact domains grow under their own widths, occupancy maps, and admitted laws.

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(00001001 join-newline-onto
  (00001000 (strings acc)
    (00000111
      ((00000010 strings) () acc)
      ((00000010 strings) (1) acc)
      ((00000011 acc "") (join-newline-onto (00000110 strings) (00000101 strings)))
      (t (join-newline-onto (00000110 strings) (str+ acc "
" (00000101 strings)))))))

(00001001 join-newline (00001000 (strings) (join-newline-onto strings "")))

(00001001 render-wsm-row
  (00001000 (entry)
    (10011101 ((sid (00000101 entry))
           (surfaces (00000110 entry))
           (ук (get-surface (00000001 ук) surfaces))
           (укр (get-surface (00000001 укр) surfaces))
           (en (get-surface (00000001 en) surfaces))
           (sa (get-surface (00000001 sa) surfaces))
           (sym (get-surface (00000001 sym) surfaces))
           (formal (formal-stub sid surfaces)))
      (str+
        "  (" (sid-bits sid) " " formal
        " (ук " (surface-word-wsm-text ук) ")"
        " (укр " (surface-word-wsm-text укр) ")"
        " (en " (surface-word-wsm-text en) ")"
        " (sa " (surface-word-wsm-text sa) ")"
        " (sym " (surface-word-wsm-text sym) ")"
        " my-lisp)"))))

(00001001 render-md-row
  (00001000 (entry)
    (10011101 ((sid (00000101 entry))
           (surfaces (00000110 entry))
           (ук (get-surface (00000001 ук) surfaces))
           (укр (get-surface (00000001 укр) surfaces))
           (en (get-surface (00000001 en) surfaces))
           (sa (get-surface (00000001 sa) surfaces))
           (sym (get-surface (00000001 sym) surfaces)))
      (str+
        "| `" (sid-bits sid) "` | " (surface-word-text ук)
        " | " (surface-word-text укр)
        " | " (surface-word-text en)
        " | " (surface-word-text sa)
        " | " (surface-word-text sym)
        " | " (machine-path sid)
        " | " (mccarthy-label sid) " |"))))

(00001001 wsm-header
  (00100111
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

(00001001 wsm-body (join-newline (00101001 wsm-header (00110111 render-wsm-row entries))))
(00001001 wsm-output (00111010 wsm-body "
)
"))

(00001001 md-header
  (00100111
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

(00001001 md-body (join-newline (00101001 md-header (00110111 render-md-row entries))))
(00001001 md-output (00111010 md-body "
"))

(00001001 wsm-output-path "lib/generated/function-table.lisp")
(00001001 md-output-path "docs/generated/function-table.md")

(00001001 write-projections
  (00001000 ()
    (00101111
      (00100111
        (10100111 wsm-output-path wsm-output)
        (10100111 md-output-path md-output)
        (01001000
          (str+
            "function-table: "
            (01000110 (00101000 entries))
            " historical projection rows written"))))))

(00001001 check-projections
  (00001000 ()
    (10011100 ((current-wsm (10100110 wsm-output-path))
          (current-md (10100110 md-output-path)))
      (00000111
        ((00100010 current-wsm wsm-output)
         (1)
         (00000111
           ((00100010 current-md md-output)
            (1)
            (01001000
              (str+
                "function-table: "
                (01000110 (00101000 entries))
                " historical projection rows current")))
           (t
            (00101111
              (00100111
                (01001000 "function-table markdown projection is stale")
                (00000101 (00000001 ())))))))
        (t
         (00101111
           (00100111
             (01001000 "function-table Lisp projection is stale")
             (00000101 (00000001 ())))))))))

(00000111
  ((00000010 *argv*)
   ()
   (write-projections))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (check-projections))
  (t
   (write-projections)))
