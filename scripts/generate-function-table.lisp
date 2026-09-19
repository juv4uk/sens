; scripts/generate-function-table.lisp — regenerate the ECO-CANON-1 function
; table (my-lisp#75) from its real source of truth, written in my-lisp
; itself (2026-09-12), replacing the retired scripts/generate-function-table.py
; per issue #76 (ECO-LISP-SCRIPTS-1): repo-owned tooling must not add new
; Python scripting surface, and tooling should be written directly in
; my-lisp/wsm rather than migrated later.
;
; Semantic authority remains lib/surface/semantic-registry.lisp — this script
; only projects it, the same "projection, not a second source of truth"
; discipline scripts/build-constitution.lisp already uses for
; my-lisp-constitution.lisp. Reads the registry as ordinary my-lisp data
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
;     uk -> ukr -> English -> Sanskrit -> Intel Core i5-6400 / Skylake)
;
; Usage (from the repo root):
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
;
; `uk` is the current/compact Ukrainian surface.
; `ukr` is the full Ukrainian peer surface of the SAME semantic identity.
; Both are read directly from semantic-registry.lisp; this generator never
; invents names and never duplicates `ukr` under another full-UK column.

; sr/2 surfaces are fixed two-element rows: (namespace spelling-or-()).
; Reader-sensitive spellings such as apostrophe are serialized as strings, so the
; registry remains ordinary re-readable Lisp data without a special reconstruction path.
(def registry-form (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))
; SID 00000000 is Canon 0 / (), a semantic ground value rather than a function.
; The function table projects only callable/form identities, so skip that first row.
(def entries (cdr (cdr registry-form)))

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(def machine-profile-form
  (car (read-all (read-file "lib/machine/intel-core-i5-6400.lisp"))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom sections) (quote ()))
      ((eq (car (car sections)) name) (car sections))
      (t (find-section name (cdr sections))))))

(def machine-rows
  (cdr (find-section (quote rows) (cdr machine-profile-form))))

(def find-machine-row
  (lambda (sid rows)
    (cond
      ((atom rows) (quote ()))
      ((equal? (car (car rows)) sid) (car rows))
      (t (find-machine-row sid (cdr rows))))))

(def machine-path
  (lambda (sid)
    (let ((row (find-machine-row sid machine-rows)))
      (cond
        ((atom row) "()")
        (t (third row))))))

; A surface word is usually a symbol (write-to-string strips the
; Lisp-level Symbol wrapping down to bare text); the reconstructed
; apostrophe case above is already a plain string. For prose contexts
; (the human .md table) the bare apostrophe is fine either way.
(def surface-word-text
  (lambda (word)
    (cond
      ((equal? word (quote ())) "()")
      ((string-membership-helper word)
       (class-membership string member)
       word)
      ((string-membership-helper word)
       (class-membership string nonmember)
       (write-to-string word)))))

; For the machine-readable .lisp output specifically, a bare apostrophe
; word must NOT be re-embedded unquoted: a future reader of this
; generated file would hit the exact same "'" quote-shorthand collision
; this script itself just worked around on the way in. write-to-string
; already does exactly the right thing per Value type -- a String gets
; quoted/escaped (read-back-safe), a Symbol stays bare -- so this is
; just write-to-string directly, named for what it's used for here.
(def surface-word-wsm-text write-to-string)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(def str+
  (lambda args (reduce (lambda (acc s) (string-append acc s)) "" args)))

; SID already arrives from sr/2 as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(def find-surface
  (lambda (lang surfaces)
    (cond
      ((atom surfaces) (quote ()))
      ((eq (car (car surfaces)) lang) (car surfaces))
      (t (find-surface lang (cdr surfaces))))))

(def surface-word
  (lambda (surface-entry)
    (cond
      ((atom surface-entry) (quote ()))
      (t (car (cdr surface-entry))))))

(def get-surface
  (lambda (lang surfaces)
    (surface-word (find-surface lang surfaces))))

(def surface-usable?
  (lambda (word)
    (not (equal? word (quote ())))))

; --- formal identity stub: first present name among en/uk/sa, else bare id ---
(def formal-stub
  (lambda (sid surfaces)
    (let* ((en (get-surface (quote en) surfaces))
           (uk (get-surface (quote uk) surfaces))
           (sa (get-surface (quote sa) surfaces)))
      (cond
        ((surface-usable? en)
         (str+ "identity:" sid "/surface:" (surface-word-text en)))
        ((surface-usable? uk)
         (str+ "identity:" sid "/surface:" (surface-word-text uk)))
        ((surface-usable? sa)
         (str+ "identity:" sid "/surface:" (surface-word-text sa)))
        (t (string-append "identity:" sid))))))

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(def join-newline-onto
  (lambda (strings acc)
    (cond
      ((atom strings) acc)
      ((eq acc "") (join-newline-onto (cdr strings) (car strings)))
      (t (join-newline-onto (cdr strings) (str+ acc "
" (car strings)))))))

(def join-newline (lambda (strings) (join-newline-onto strings "")))

(def render-wsm-row
  (lambda (entry)
    (let* ((sid (car entry))
           (surfaces (cdr entry))
           (uk (get-surface (quote uk) surfaces))
           (ukr (get-surface (quote ukr) surfaces))
           (en (get-surface (quote en) surfaces))
           (sa (get-surface (quote sa) surfaces))
           (sym (get-surface (quote sym) surfaces))
           (formal (formal-stub sid surfaces)))
      (str+
        "  (" (write-to-string sid) " " formal
        " (uk " (surface-word-wsm-text uk) ")"
        " (ukr " (surface-word-wsm-text ukr) ")"
        " (en " (surface-word-wsm-text en) ")"
        " (sa " (surface-word-wsm-text sa) ")"
        " (sym " (surface-word-wsm-text sym) ")"
        " my-lisp)"))))

(def render-md-row
  (lambda (entry)
    (let* ((sid (car entry))
           (surfaces (cdr entry))
           (uk (get-surface (quote uk) surfaces))
           (ukr (get-surface (quote ukr) surfaces))
           (en (get-surface (quote en) surfaces))
           (sa (get-surface (quote sa) surfaces))
           (sym (get-surface (quote sym) surfaces)))
      (str+
        "| `" sid "` | " (surface-word-text uk)
        " | " (surface-word-text ukr)
        " | " (surface-word-text en)
        " | " (surface-word-text sa)
        " | " (surface-word-text sym)
        " | " (machine-path sid) " |"))))

(def wsm-header
  (list
    "; GENERATED — DO NOT EDIT BY HAND"
    "; Authority: lib/surface/semantic-registry.lisp"
    "; Generator: scripts/generate-function-table.lisp (ECO-CANON-1 / my-lisp#75)"
    "; Schema ft/2: (sid-bitstring formal uk ukr en sa sym authority)"
    "; uk = current Ukrainian; ukr = full Ukrainian peer surface"
    "; Display order for humans: uk → ukr → English → Sanskrit"
    "; authority = my-lisp (semantic)"
    ""
    "(ft/2"))

(def wsm-body (join-newline (append wsm-header (map render-wsm-row entries))))
(def wsm-output (string-append wsm-body "
)
"))

(def md-header
  (list
    "# Function table (generated projection)"
    ""
    "**Authority:** `lib/surface/semantic-registry.lisp` — projection only, not a second source of truth."
    ""
    "**Machine projection:** `lib/machine/intel-core-i5-6400.lisp` — physical execution paths only; it does not create language meaning."
    ""
    "Regenerate: `cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp`"
    ""
    "| ID | uk | ukr | English | Sanskrit | Symbol | Intel Core i5-6400 / Skylake |"
    "|----|----|-----|---------|----------|--------|------------------------------|"))

(def md-body (join-newline (append md-header (map render-md-row entries))))
(def md-output (string-append md-body "
"))

(write-file "lib/generated/function-table.lisp" wsm-output)
(write-file "docs/generated/function-table.md" md-output)

(print (str+ "function-table: " (number->string (length entries)) " identities written"))
