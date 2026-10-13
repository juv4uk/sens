; #528 — Lisp-owned replacement for scripts/check_semantic_registry.py.
; Tooling/governance validation only. Semantic authority remains
; lib/surface/semantic-registry.lisp.
;
; The outer pass tokenizes source text instead of using read-all because the
; canonical reader would turn lexical ID 0001 into numeric value 1 and erase
; the required "at least four digits" evidence.

(0011 sr-same?
  (0010 (left right)
    (110
      ((equal? left right) (structural-relation same) t)
      ((equal? left right) (structural-relation distinct) (001 ())))))

(0011 sr-nonempty-list?
  (0010 (value)
    (110
      ((010 value) (structural-kind pair) t)
      ((010 value) (structural-kind empty-list) (001 ()))
      ((010 value) (structural-kind atom) (001 ())))))

(0011 sr-member?
  (0010 (value values)
    (110
      ((010 values) (structural-kind empty-list) (001 ()))
      ((010 values) (structural-kind atom) (001 ()))
      ((010 values) (structural-kind pair)
       (110
         ((sr-same? value (100 values)) t)
         (t (sr-member? value (011 values))))))))

(0011 sr-uniq-add
  (0010 (value values)
    (110
      ((sr-member? value values) values)
      (t (111 value values)))))

(0011 sr-flush-token
  (0010 (current tokens)
    (110
      ((string-empty? current) tokens)
      (t (111 current tokens)))))

(0011 sr-whitespace?
  (0010 (ch)
    (or (sr-same? ch " ")
        (sr-same? ch "\n")
        (sr-same? ch "\r")
        (sr-same? ch "\t"))))

(0011 sr-tokenize-onto
  (0010 (text current tokens in-comment)
    (110
      ((string-empty? text)
       (10100 (sr-flush-token current tokens)))
      (t
       (001001 ((ch (string-first text))
              (rest (string-rest text)))
         (110
           (in-comment
            (110
              ((sr-same? ch "\n")
               (sr-tokenize-onto rest "" tokens (001 ())))
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
              (001 ())))
           ((or (sr-same? ch "(") (sr-same? ch ")"))
            (sr-tokenize-onto
              rest
              ""
              (111 ch (sr-flush-token current tokens))
              (001 ())))
           (t
            (sr-tokenize-onto
              rest
              (string-append current ch)
              tokens
              (001 ())))))))))

(0011 sr-tokenize
  (0010 (text)
    (sr-tokenize-onto text "" (001 ()) (001 ()))))

; Parse result shapes:
;   ("ok" value remaining-tokens)
;   ("error" message)
(0011 sr-parse-list
  (0010 (tokens acc)
    (110
      ((010 tokens) (structural-kind empty-list)
       (1110 "error" "unclosed-list"))
      ((010 tokens) (structural-kind atom)
       (1110 "error" "malformed-token-stream"))
      ((010 tokens) (structural-kind pair)
       (110
         ((sr-same? (100 tokens) ")")
          (1110 "ok" (10100 acc) (011 tokens)))
         (t
          (001000 ((parsed (sr-parse-one tokens)))
            (110
              ((sr-same? (100 parsed) "error") parsed)
              (t
               (sr-parse-list
                 (third parsed)
                 (111 (second parsed) acc)))))))))))

(0011 sr-parse-one
  (0010 (tokens)
    (110
      ((010 tokens) (structural-kind empty-list)
       (1110 "error" "unexpected-eof"))
      ((010 tokens) (structural-kind atom)
       (1110 "error" "malformed-token-stream"))
      ((010 tokens) (structural-kind pair)
       (001000 ((token (100 tokens)))
         (110
           ((sr-same? token "(")
            (sr-parse-list (011 tokens) (001 ())))
           ((sr-same? token ")")
            (1110 "error" "unexpected-closing-paren"))
           (t
            (1110 "ok" token (011 tokens)))))))))

(0011 sr-parse-root
  (0010 (tokens)
    (001000 ((parsed (sr-parse-one tokens)))
      (110
        ((sr-same? (100 parsed) "error") parsed)
        (t
         (001000 ((remaining (third parsed)))
           (110
             ((010 remaining) (structural-kind empty-list)
              (1110 "ok" (second parsed)))
             ((010 remaining) (structural-kind atom)
              (1110 "error" "malformed-token-stream"))
             ((010 remaining) (structural-kind pair)
              (1110 "error" "extra-top-level-forms")))))))))

(0011 sr-digit?
  (0010 (ch)
    (sr-member? ch (001 ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(0011 sr-all-digits?
  (0010 (text)
    (110
      ((string-empty? text) t)
      (t
       (110
         ((sr-digit? (string-first text))
          (sr-all-digits? (string-rest text)))
         (t (001 ())))))))

(0011 sr-at-least-four-chars?
  (0010 (text)
    (110
      ((string-empty? text) (001 ()))
      (t
       (001000 ((a (string-rest text)))
         (110
           ((string-empty? a) (001 ()))
           (t
            (001000 ((b (string-rest a)))
              (110
                ((string-empty? b) (001 ()))
                (t
                 (001000 ((c (string-rest b)))
                   (110
                     ((string-empty? c) (001 ()))
                     (t t)))))))))))))

(0011 sr-valid-id?
  (0010 (text)
    (and (sr-at-least-four-chars? text)
         (sr-all-digits? text))))

(0011 sr-between?
  (0010 (value low high)
    (and (>= value low) (<= value high))))

; Alphabetic coverage for every current human surface, including Latin
; Extended Additional used by Sanskrit transliteration (ṃ/ṇ/ṛ/ṣ), plus common
; future scripts. The guarded law is that punctuation-only spellings may not
; live under a human-language surface.
(0011 sr-letter-codepoint?
  (0010 (cp)
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

(0011 sr-has-letter?
  (0010 (text)
    (110
      ((string-empty? text) (001 ()))
      (t
       (110
         ((sr-letter-codepoint? (string->codepoint (string-first text))) t)
         (t (sr-has-letter? (string-rest text))))))))

(0011 sr-status?
  (0010 (status)
    (sr-member?
      status
      (001 ("stable" "candidate" "missing" "compatibility-only")))))

(0011 sr-first-wave-present?
  (0010 (languages)
    (and (sr-member? "uk" languages)
         (sr-member? "en" languages)
         (sr-member? "sa" languages))))

(0011 sr-fail
  (0010 (detail)
    (001000 ((a (princ "semantic registry error: "))
          (b (princ (write-to-string detail)))
          (c (princ "\n")))
      ; Deliberately cross a real UnknownSymbol boundary after printing the
      ; diagnostic. The dynamically constructed missing symbol carries the
      ; rejection payload in the error itself, so redirected stdout buffering
      ; cannot erase the useful detail before the non-zero process exit.
      (0001
        (1110
          (string->symbol
            (string-append
              "semantic-registry-check-failed:"
              (write-to-string detail))))))))

; Result: ("ok" updated-all-surfaces has-sym), or sr-fail.
(0011 sr-validate-surfaces
  (0010 (identity surfaces entry-languages all-surfaces has-sym)
    (110
      ((010 surfaces) (structural-kind empty-list)
       (110
         ((sr-first-wave-present? entry-languages)
          (1110 "ok" all-surfaces has-sym))
         (t
          (sr-fail
            (1110 identity "missing-explicit-first-wave-surface"
                  entry-languages)))))
      ((010 surfaces) (structural-kind atom)
       (sr-fail (1110 identity "surface-tail-not-list" surfaces)))
      ((010 surfaces) (structural-kind pair)
       (001000 ((surface (100 surfaces)))
         (110
           ((sr-nonempty-list? surface)
            (110
              ((= (000000 surface) 3)
               (001001 ((language (100 surface))
                      (name (second surface))
                      (status (third surface)))
                 (110
                   ((or (0100 (string? language))
                        (0100 (string? name))
                        (0100 (string? status)))
                    (sr-fail (1110 identity "surface-fields-must-be-atoms" surface)))
                   ((sr-member? language entry-languages)
                    (sr-fail (1110 identity "duplicate-surface" language)))
                   ((0100 (sr-status? status))
                    (sr-fail (1110 identity language "unknown-status" status)))
                   ((and (sr-same? status "missing")
                         (0100 (sr-same? name "—")))
                    (sr-fail (1110 identity language "missing-requires-dash" name)))
                   ((and (0100 (or (sr-same? status "missing")
                                  (sr-same? status "compatibility-only")))
                         (sr-same? name "—"))
                    (sr-fail (1110 identity language status "requires-name")))
                   ((sr-same? name identity)
                    (sr-fail (1110 identity language "surface-name-equals-id")))
                   ((and (0100 (sr-same? language "sym"))
                         (0100 (sr-same? name "—"))
                         (0100 (sr-has-letter? name)))
                    (sr-fail
                      (1110 identity language
                            "punctuation-belongs-under-sym" name)))
                   (t
                    (sr-validate-surfaces
                      identity
                      (011 surfaces)
                      (111 language entry-languages)
                      (sr-uniq-add language all-surfaces)
                      (or has-sym (sr-same? language "sym")))))))
              (t
               (sr-fail (1110 identity "surface-must-have-three-fields" surface)))))
           (t
            (sr-fail (1110 identity "surface-must-be-list" surface)))))))))

(0011 sr-validate-entries
  (0010 (entries seen-ids all-surfaces symbolic-count count)
    (110
      ((010 entries) (structural-kind empty-list)
       (110
         ((= count 0)
          (sr-fail (1110 "registry-has-no-semantic-identities")))
         (t
          (1110 "ok" count all-surfaces symbolic-count))))
      ((010 entries) (structural-kind atom)
       (sr-fail (1110 "registry-tail-not-list" entries)))
      ((010 entries) (structural-kind pair)
       (001000 ((entry (100 entries)))
         (110
           ((sr-nonempty-list? entry)
            (110
              ((>= (000000 entry) 2)
               (001000 ((identity (100 entry)))
                 (110
                   ((0100 (string? identity))
                    (sr-fail (1110 "semantic-id-must-be-token" identity)))
                   ((0100 (sr-valid-id? identity))
                    (sr-fail (1110 "semantic-id-must-be-four-plus-digits" identity)))
                   ((sr-member? identity seen-ids)
                    (sr-fail (1110 "duplicate-semantic-id" identity)))
                   (t
                    (001000 ((surface-result
                            (sr-validate-surfaces
                              identity
                              (011 entry)
                              (001 ())
                              all-surfaces
                              (001 ()))))
                      (sr-validate-entries
                        (011 entries)
                        (111 identity seen-ids)
                        (second surface-result)
                        (110
                          ((third surface-result) (01010 symbolic-count 1))
                          (t symbolic-count))
                        (01010 count 1)))))))
              (t
               (sr-fail (1110 "malformed-semantic-entry" entry)))))
           (t
            (sr-fail (1110 "malformed-semantic-entry" entry)))))))))

(0011 sr-insert-string
  (0010 (value sorted)
    (110
      ((010 sorted) (structural-kind empty-list) (1110 value))
      ((010 sorted) (structural-kind atom) (1110 value sorted))
      ((010 sorted) (structural-kind pair)
       (110
         ((string<? value (100 sorted)) (111 value sorted))
         (t
          (111 (100 sorted)
                (sr-insert-string value (011 sorted)))))))))

(0011 sr-sort-strings
  (0010 (values acc)
    (110
      ((010 values) (structural-kind empty-list) acc)
      ((010 values) (structural-kind atom) (sr-insert-string values acc))
      ((010 values) (structural-kind pair)
       (sr-sort-strings
         (011 values)
         (sr-insert-string (100 values) acc))))))

(0011 sr-join-space
  (0010 (values)
    (110
      ((010 values) (structural-kind empty-list) "")
      ((010 values) (structural-kind atom) values)
      ((010 values) (structural-kind pair)
       (110
         ((010 (011 values)) (structural-kind empty-list) (100 values))
         ((010 (011 values)) (structural-kind atom)
          (string-append
            (100 values)
            (string-append " " (011 values))))
         ((010 (011 values)) (structural-kind pair)
          (string-append
            (100 values)
            (string-append
              " "
              (sr-join-space (011 values))))))))))

(0011 sr-source
  (read-file "lib/surface/semantic-registry.lisp"))

(0011 sr-parsed
  (sr-parse-root (sr-tokenize sr-source)))

(110
  ((sr-same? (100 sr-parsed) "error")
   (sr-fail (second sr-parsed)))
  (t
   (001000 ((root (second sr-parsed)))
     (110
       ((0100 (sr-nonempty-list? root))
        (sr-fail (1110 "registry-root-must-be-list")))
       ((0100 (sr-same? (100 root) "sr/1"))
        (sr-fail (1110 "registry-must-start-with-sr/1" (100 root))))
       (t
        (001001 ((result
                 (sr-validate-entries
                   (011 root)
                   (001 ())
                   (001 ())
                   0
                   0))
               (identity-count (second result))
               (surface-names (sr-sort-strings (third result) (001 ())))
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
          (001 semantic-registry-ok)))))))
