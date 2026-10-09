; #528 — Lisp-owned replacement for scripts/check_semantic_registry.py.
; Tooling/governance validation only. Semantic authority remains
; lib/surface/semantic-registry.lisp.
;
; The outer pass tokenizes source text instead of using read-all because the
; canonical reader would turn lexical ID 0001 into numeric value 1 and erase
; the required "at least four digits" evidence.

(def sr-same?
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) t)
      ((equal? left right) (structural-relation distinct) (quote ())))))

(def sr-nonempty-list?
  (lambda (value)
    (cond
      ((atom value) (structural-kind pair) t)
      ((atom value) (structural-kind empty-list) (quote ()))
      ((atom value) (structural-kind atom) (quote ())))))

(def sr-member?
  (lambda (value values)
    (cond
      ((atom values) (structural-kind empty-list) (quote ()))
      ((atom values) (structural-kind atom) (quote ()))
      ((atom values) (structural-kind pair)
       (cond
         ((sr-same? value (car values)) t)
         (t (sr-member? value (cdr values))))))))

(def sr-uniq-add
  (lambda (value values)
    (cond
      ((sr-member? value values) values)
      (t (cons value values)))))

(def sr-flush-token
  (lambda (current tokens)
    (cond
      ((string-empty? current) tokens)
      (t (cons current tokens)))))

(def sr-whitespace?
  (lambda (ch)
    (or (sr-same? ch " ")
        (sr-same? ch "\n")
        (sr-same? ch "\r")
        (sr-same? ch "\t"))))

(def sr-tokenize-onto
  (lambda (text current tokens in-comment)
    (cond
      ((string-empty? text)
       (reverse (sr-flush-token current tokens)))
      (t
       (let* ((ch (string-first text))
              (rest (string-rest text)))
         (cond
           (in-comment
            (cond
              ((sr-same? ch "\n")
               (sr-tokenize-onto rest "" tokens (quote ())))
              (t
               (sr-tokenize-onto rest "" tokens t))))
           ((sr-same? ch ";")
            (sr-tokenize-onto
              rest
              ""
              (sr-flush-token current tokens)
              t))
           ((sr-whitespace? ch)
            (sr-tokenize-onto
              rest
              ""
              (sr-flush-token current tokens)
              (quote ())))
           ((or (sr-same? ch "(") (sr-same? ch ")"))
            (sr-tokenize-onto
              rest
              ""
              (cons ch (sr-flush-token current tokens))
              (quote ())))
           (t
            (sr-tokenize-onto
              rest
              (string-append current ch)
              tokens
              (quote ())))))))))

(def sr-tokenize
  (lambda (text)
    (sr-tokenize-onto text "" (quote ()) (quote ()))))

; Parse result shapes:
;   ("ok" value remaining-tokens)
;   ("error" message)
(def sr-parse-list
  (lambda (tokens acc)
    (cond
      ((atom tokens) (structural-kind empty-list)
       (list "error" "unclosed-list"))
      ((atom tokens) (structural-kind atom)
       (list "error" "malformed-token-stream"))
      ((atom tokens) (structural-kind pair)
       (cond
         ((sr-same? (car tokens) ")")
          (list "ok" (reverse acc) (cdr tokens)))
         (t
          (let ((parsed (sr-parse-one tokens)))
            (cond
              ((sr-same? (car parsed) "error") parsed)
              (t
               (sr-parse-list
                 (third parsed)
                 (cons (second parsed) acc)))))))))))

(def sr-parse-one
  (lambda (tokens)
    (cond
      ((atom tokens) (structural-kind empty-list)
       (list "error" "unexpected-eof"))
      ((atom tokens) (structural-kind atom)
       (list "error" "malformed-token-stream"))
      ((atom tokens) (structural-kind pair)
       (let ((token (car tokens)))
         (cond
           ((sr-same? token "(")
            (sr-parse-list (cdr tokens) (quote ())))
           ((sr-same? token ")")
            (list "error" "unexpected-closing-paren"))
           (t
            (list "ok" token (cdr tokens)))))))))

(def sr-parse-root
  (lambda (tokens)
    (let ((parsed (sr-parse-one tokens)))
      (cond
        ((sr-same? (car parsed) "error") parsed)
        (t
         (let ((remaining (third parsed)))
           (cond
             ((atom remaining) (structural-kind empty-list)
              (list "ok" (second parsed)))
             ((atom remaining) (structural-kind atom)
              (list "error" "malformed-token-stream"))
             ((atom remaining) (structural-kind pair)
              (list "error" "extra-top-level-forms")))))))))

(def sr-digit?
  (lambda (ch)
    (sr-member? ch (quote ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(def sr-all-digits?
  (lambda (text)
    (cond
      ((string-empty? text) t)
      (t
       (cond
         ((sr-digit? (string-first text))
          (sr-all-digits? (string-rest text)))
         (t (quote ())))))))

(def sr-at-least-four-chars?
  (lambda (text)
    (cond
      ((string-empty? text) (quote ()))
      (t
       (let ((a (string-rest text)))
         (cond
           ((string-empty? a) (quote ()))
           (t
            (let ((b (string-rest a)))
              (cond
                ((string-empty? b) (quote ()))
                (t
                 (let ((c (string-rest b)))
                   (cond
                     ((string-empty? c) (quote ()))
                     (t t)))))))))))))

(def sr-valid-id?
  (lambda (text)
    (and (sr-at-least-four-chars? text)
         (sr-all-digits? text))))

(def sr-between?
  (lambda (value low high)
    (and (>= value low) (<= value high))))

; Alphabetic coverage for every current human surface, including Latin
; Extended Additional used by Sanskrit transliteration (ṃ/ṇ/ṛ/ṣ), plus common
; future scripts. The guarded law is that punctuation-only spellings may not
; live under a human-language surface.
(def sr-letter-codepoint?
  (lambda (cp)
    (or
      (sr-between? cp 65 90)
      (sr-between? cp 97 122)
      (sr-between? cp 192 214)
      (sr-between? cp 216 246)
      (sr-between? cp 248 687)
      (sr-between? cp 880 1023)
      (sr-between? cp 1024 1327)
      (sr-between? cp 1329 1366)
      (sr-between? cp 1377 1415)
      (sr-between? cp 1488 1514)
      (sr-between? cp 1520 1524)
      (sr-between? cp 2308 2361)
      (sr-between? cp 4352 4607)
      (sr-between? cp 7680 7935)
      (sr-between? cp 19968 40959))))

(def sr-has-letter?
  (lambda (text)
    (cond
      ((string-empty? text) (quote ()))
      (t
       (cond
         ((sr-letter-codepoint? (string->codepoint (string-first text))) t)
         (t (sr-has-letter? (string-rest text))))))))

(def sr-status?
  (lambda (status)
    (sr-member?
      status
      (quote ("stable" "candidate" "missing" "compatibility-only")))))

(def sr-first-wave-present?
  (lambda (languages)
    (and (sr-member? "uk" languages)
         (sr-member? "en" languages)
         (sr-member? "sa" languages))))

(def sr-fail
  (lambda (detail)
    (let ((a (princ "semantic registry error: "))
          (b (princ (write-to-string detail)))
          (c (princ "\n")))
      ; Deliberately cross a real UnknownSymbol boundary after printing the
      ; diagnostic. The dynamically constructed missing symbol carries the
      ; rejection payload in the error itself, so redirected stdout buffering
      ; cannot erase the useful detail before the non-zero process exit.
      (eval
        (list
          (string->symbol
            (string-append
              "semantic-registry-check-failed:"
              (write-to-string detail))))))))

; Result: ("ok" updated-all-surfaces has-sym), or sr-fail.
(def sr-validate-surfaces
  (lambda (identity surfaces entry-languages all-surfaces has-sym)
    (cond
      ((atom surfaces) (structural-kind empty-list)
       (cond
         ((sr-first-wave-present? entry-languages)
          (list "ok" all-surfaces has-sym))
         (t
          (sr-fail
            (list identity "missing-explicit-first-wave-surface"
                  entry-languages)))))
      ((atom surfaces) (structural-kind atom)
       (sr-fail (list identity "surface-tail-not-list" surfaces)))
      ((atom surfaces) (structural-kind pair)
       (let ((surface (car surfaces)))
         (cond
           ((sr-nonempty-list? surface)
            (cond
              ((= (length surface) 3)
               (let* ((language (car surface))
                      (name (second surface))
                      (status (third surface)))
                 (cond
                   ((or (not (string? language))
                        (not (string? name))
                        (not (string? status)))
                    (sr-fail (list identity "surface-fields-must-be-atoms" surface)))
                   ((sr-member? language entry-languages)
                    (sr-fail (list identity "duplicate-surface" language)))
                   ((not (sr-status? status))
                    (sr-fail (list identity language "unknown-status" status)))
                   ((and (sr-same? status "missing")
                         (not (sr-same? name "—")))
                    (sr-fail (list identity language "missing-requires-dash" name)))
                   ((and (not (or (sr-same? status "missing")
                                  (sr-same? status "compatibility-only")))
                         (sr-same? name "—"))
                    (sr-fail (list identity language status "requires-name")))
                   ((sr-same? name identity)
                    (sr-fail (list identity language "surface-name-equals-id")))
                   ((and (not (sr-same? language "sym"))
                         (not (sr-same? name "—"))
                         (not (sr-has-letter? name)))
                    (sr-fail
                      (list identity language
                            "punctuation-belongs-under-sym" name)))
                   (t
                    (sr-validate-surfaces
                      identity
                      (cdr surfaces)
                      (cons language entry-languages)
                      (sr-uniq-add language all-surfaces)
                      (or has-sym (sr-same? language "sym")))))))
              (t
               (sr-fail (list identity "surface-must-have-three-fields" surface)))))
           (t
            (sr-fail (list identity "surface-must-be-list" surface)))))))))

(def sr-validate-entries
  (lambda (entries seen-ids all-surfaces symbolic-count count)
    (cond
      ((atom entries) (structural-kind empty-list)
       (cond
         ((= count 0)
          (sr-fail (list "registry-has-no-semantic-identities")))
         (t
          (list "ok" count all-surfaces symbolic-count))))
      ((atom entries) (structural-kind atom)
       (sr-fail (list "registry-tail-not-list" entries)))
      ((atom entries) (structural-kind pair)
       (let ((entry (car entries)))
         (cond
           ((sr-nonempty-list? entry)
            (cond
              ((>= (length entry) 2)
               (let ((identity (car entry)))
                 (cond
                   ((not (string? identity))
                    (sr-fail (list "semantic-id-must-be-token" identity)))
                   ((not (sr-valid-id? identity))
                    (sr-fail (list "semantic-id-must-be-four-plus-digits" identity)))
                   ((sr-member? identity seen-ids)
                    (sr-fail (list "duplicate-semantic-id" identity)))
                   (t
                    (let ((surface-result
                            (sr-validate-surfaces
                              identity
                              (cdr entry)
                              (quote ())
                              all-surfaces
                              (quote ()))))
                      (sr-validate-entries
                        (cdr entries)
                        (cons identity seen-ids)
                        (second surface-result)
                        (cond
                          ((third surface-result) (+ symbolic-count 1))
                          (t symbolic-count))
                        (+ count 1)))))))
              (t
               (sr-fail (list "malformed-semantic-entry" entry)))))
           (t
            (sr-fail (list "malformed-semantic-entry" entry)))))))))

(def sr-insert-string
  (lambda (value sorted)
    (cond
      ((atom sorted) (structural-kind empty-list) (list value))
      ((atom sorted) (structural-kind atom) (list value sorted))
      ((atom sorted) (structural-kind pair)
       (cond
         ((string<? value (car sorted)) (cons value sorted))
         (t
          (cons (car sorted)
                (sr-insert-string value (cdr sorted)))))))))

(def sr-sort-strings
  (lambda (values acc)
    (cond
      ((atom values) (structural-kind empty-list) acc)
      ((atom values) (structural-kind atom) (sr-insert-string values acc))
      ((atom values) (structural-kind pair)
       (sr-sort-strings
         (cdr values)
         (sr-insert-string (car values) acc))))))

(def sr-join-space
  (lambda (values)
    (cond
      ((atom values) (structural-kind empty-list) "")
      ((atom values) (structural-kind atom) values)
      ((atom values) (structural-kind pair)
       (cond
         ((atom (cdr values)) (structural-kind empty-list) (car values))
         ((atom (cdr values)) (structural-kind atom)
          (string-append
            (car values)
            (string-append " " (cdr values))))
         ((atom (cdr values)) (structural-kind pair)
          (string-append
            (car values)
            (string-append
              " "
              (sr-join-space (cdr values))))))))))

(def sr-source
  (read-file "lib/surface/semantic-registry.lisp"))

(def sr-parsed
  (sr-parse-root (sr-tokenize sr-source)))

(cond
  ((sr-same? (car sr-parsed) "error")
   (sr-fail (second sr-parsed)))
  (t
   (let ((root (second sr-parsed)))
     (cond
       ((not (sr-nonempty-list? root))
        (sr-fail (list "registry-root-must-be-list")))
       ((not (sr-same? (car root) "sr/1"))
        (sr-fail (list "registry-must-start-with-sr/1" (car root))))
       (t
        (let* ((result
                 (sr-validate-entries
                   (cdr root)
                   (quote ())
                   (quote ())
                   0
                   0))
               (identity-count (second result))
               (surface-names (sr-sort-strings (third result) (quote ())))
               (symbolic-count (fourth result))
               (a (princ
                    (string-append
                      "semantic registry: "
                      (string-append
                        (number->string identity-count)
                        " identities\n"))))
               (b (princ
                    (string-append
                      "surfaces: "
                      (string-append
                        (sr-join-space surface-names)
                        "\n"))))
               (c (princ
                    (string-append
                      "shared symbolic identities: "
                      (string-append
                        (number->string symbolic-count)
                        "\n"))))
               (d (princ "numeric-only authority: CONFIRMED\n"))
               (e (princ "meaning-first shape: CONFIRMED\n")))
          (quote semantic-registry-ok)))))))
