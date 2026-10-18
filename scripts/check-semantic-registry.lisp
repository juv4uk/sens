; #528 — Lisp-owned replacement for scripts/check_semantic_registry.py.
; Tooling/governance validation only. Semantic authority remains
; lib/surface/semantic-registry.lisp.
;
; The outer pass tokenizes source text instead of using read-all because the
; canonical reader would turn lexical ID 0001 into numeric value 1 and erase
; the required "at least four digits" evidence.

(визначити sr-same?
  (функція (left right)
    (за-умовою
      ((equal? left right) (structural-relation same) t)
      ((equal? left right) (structural-relation distinct) (як-є ())))))

(визначити sr-nonempty-list?
  (функція (value)
    (за-умовою
      ((атом? value) (structural-kind pair) t)
      ((атом? value) (structural-kind empty-list) (як-є ()))
      ((атом? value) (structural-kind atom) (як-є ())))))

(визначити sr-member?
  (функція (value values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) (як-є ()))
      ((атом? values) (structural-kind atom) (як-є ()))
      ((атом? values) (structural-kind pair)
       (за-умовою
         ((sr-same? value (перше values)) t)
         (t (sr-member? value (решта values))))))))

(визначити sr-uniq-add
  (функція (value values)
    (за-умовою
      ((sr-member? value values) values)
      (t (сполучити value values)))))

(визначити sr-flush-token
  (функція (current tokens)
    (за-умовою
      ((рядок-порожній? current) tokens)
      (t (сполучити current tokens)))))

(визначити sr-whitespace?
  (функція (ch)
    (або (sr-same? ch " ")
        (sr-same? ch "\n")
        (sr-same? ch "\r")
        (sr-same? ch "\t"))))

(визначити sr-tokenize-onto
  (функція (text current tokens in-comment)
    (за-умовою
      ((рядок-порожній? text)
       (зворот (sr-flush-token current tokens)))
      (t
       (нехай-послідовно ((ch (рядок-перший text))
              (rest (рядок-решта text)))
         (за-умовою
           (in-comment
            (за-умовою
              ((sr-same? ch "\n")
               (sr-tokenize-onto rest "" tokens (як-є ())))
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
              (як-є ())))
           ((або (sr-same? ch "(") (sr-same? ch ")"))
            (sr-tokenize-onto
              rest
              ""
              (сполучити ch (sr-flush-token current tokens))
              (як-є ())))
           (t
            (sr-tokenize-onto
              rest
              (рядок-додати current ch)
              tokens
              (як-є ())))))))))

(визначити sr-tokenize
  (функція (text)
    (sr-tokenize-onto text "" (як-є ()) (як-є ()))))

; Parse result shapes:
;   ("ok" value remaining-tokens)
;   ("error" message)
(визначити sr-parse-list
  (функція (tokens acc)
    (за-умовою
      ((атом? tokens) (structural-kind empty-list)
       (список "error" "unclosed-list"))
      ((атом? tokens) (structural-kind atom)
       (список "error" "malformed-token-stream"))
      ((атом? tokens) (structural-kind pair)
       (за-умовою
         ((sr-same? (перше tokens) ")")
          (список "ok" (зворот acc) (решта tokens)))
         (t
          (нехай ((parsed (sr-parse-one tokens)))
            (за-умовою
              ((sr-same? (перше parsed) "error") parsed)
              (t
               (sr-parse-list
                 (third parsed)
                 (сполучити (second parsed) acc)))))))))))

(визначити sr-parse-one
  (функція (tokens)
    (за-умовою
      ((атом? tokens) (structural-kind empty-list)
       (список "error" "unexpected-eof"))
      ((атом? tokens) (structural-kind atom)
       (список "error" "malformed-token-stream"))
      ((атом? tokens) (structural-kind pair)
       (нехай ((token (перше tokens)))
         (за-умовою
           ((sr-same? token "(")
            (sr-parse-list (решта tokens) (як-є ())))
           ((sr-same? token ")")
            (список "error" "unexpected-closing-paren"))
           (t
            (список "ok" token (решта tokens)))))))))

(визначити sr-parse-root
  (функція (tokens)
    (нехай ((parsed (sr-parse-one tokens)))
      (за-умовою
        ((sr-same? (перше parsed) "error") parsed)
        (t
         (нехай ((remaining (third parsed)))
           (за-умовою
             ((атом? remaining) (structural-kind empty-list)
              (список "ok" (second parsed)))
             ((атом? remaining) (structural-kind atom)
              (список "error" "malformed-token-stream"))
             ((атом? remaining) (structural-kind pair)
              (список "error" "extra-top-level-forms")))))))))

(визначити sr-digit?
  (функція (ch)
    (sr-member? ch (як-є ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(визначити sr-all-digits?
  (функція (text)
    (за-умовою
      ((рядок-порожній? text) t)
      (t
       (за-умовою
         ((sr-digit? (рядок-перший text))
          (sr-all-digits? (рядок-решта text)))
         (t (як-є ())))))))

(визначити sr-at-least-four-chars?
  (функція (text)
    (за-умовою
      ((рядок-порожній? text) (як-є ()))
      (t
       (нехай ((a (рядок-решта text)))
         (за-умовою
           ((рядок-порожній? a) (як-є ()))
           (t
            (нехай ((b (рядок-решта a)))
              (за-умовою
                ((рядок-порожній? b) (як-є ()))
                (t
                 (нехай ((c (рядок-решта b)))
                   (за-умовою
                     ((рядок-порожній? c) (як-є ()))
                     (t t)))))))))))))

(визначити sr-valid-id?
  (функція (text)
    (and (sr-at-least-four-chars? text)
         (sr-all-digits? text))))

(визначити sr-between?
  (функція (value low high)
    (and (>= value low) (<= value high))))

; Alphabetic coverage for every current human surface, including Latin
; Extended Additional used by Sanskrit transliteration (ṃ/ṇ/ṛ/ṣ), plus common
; future scripts. The guarded law is that punctuation-only spellings may not
; live under a human-language surface.
(визначити sr-letter-codepoint?
  (функція (cp)
    (або
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

(визначити sr-has-letter?
  (функція (text)
    (за-умовою
      ((рядок-порожній? text) (як-є ()))
      (t
       (за-умовою
         ((sr-letter-codepoint? (string->codepoint (рядок-перший text))) t)
         (t (sr-has-letter? (рядок-решта text))))))))

(визначити sr-status?
  (функція (status)
    (sr-member?
      status
      (як-є ("stable" "candidate" "missing" "compatibility-only")))))

(визначити sr-first-wave-present?
  (функція (languages)
    (and (sr-member? "uk" languages)
         (sr-member? "en" languages)
         (sr-member? "sa" languages))))

(визначити sr-fail
  (функція (detail)
    (нехай ((a (показати "semantic registry error: "))
          (b (показати (значення-у-текст detail)))
          (c (показати "\n")))
      ; Deliberately cross a real UnknownSymbol boundary after printing the
      ; diagnostic. The dynamically constructed missing symbol carries the
      ; rejection payload in the error itself, so redirected stdout buffering
      ; cannot erase the useful detail before the non-zero process exit.
      (обчислити
        (список
          (текст-у-символ
            (рядок-додати
              "semantic-registry-check-failed:"
              (значення-у-текст detail))))))))

; Result: ("ok" updated-all-surfaces has-sym), or sr-fail.
(визначити sr-validate-surfaces
  (функція (identity surfaces entry-languages all-surfaces has-sym)
    (за-умовою
      ((атом? surfaces) (structural-kind empty-list)
       (за-умовою
         ((sr-first-wave-present? entry-languages)
          (список "ok" all-surfaces has-sym))
         (t
          (sr-fail
            (список identity "missing-explicit-first-wave-surface"
                  entry-languages)))))
      ((атом? surfaces) (structural-kind atom)
       (sr-fail (список identity "surface-tail-not-list" surfaces)))
      ((атом? surfaces) (structural-kind pair)
       (нехай ((surface (перше surfaces)))
         (за-умовою
           ((sr-nonempty-list? surface)
            (за-умовою
              ((= (довжина surface) 3)
               (нехай-послідовно ((language (перше surface))
                      (name (second surface))
                      (status (third surface)))
                 (за-умовою
                   ((або (хибне? (string? language))
                        (хибне? (string? name))
                        (хибне? (string? status)))
                    (sr-fail (список identity "surface-fields-must-be-atoms" surface)))
                   ((sr-member? language entry-languages)
                    (sr-fail (список identity "duplicate-surface" language)))
                   ((хибне? (sr-status? status))
                    (sr-fail (список identity language "unknown-status" status)))
                   ((and (sr-same? status "missing")
                         (хибне? (sr-same? name "—")))
                    (sr-fail (список identity language "missing-requires-dash" name)))
                   ((and (хибне? (або (sr-same? status "missing")
                                  (sr-same? status "compatibility-only")))
                         (sr-same? name "—"))
                    (sr-fail (список identity language status "requires-name")))
                   ((sr-same? name identity)
                    (sr-fail (список identity language "surface-name-equals-id")))
                   ((and (хибне? (sr-same? language "sym"))
                         (хибне? (sr-same? name "—"))
                         (хибне? (sr-has-letter? name)))
                    (sr-fail
                      (список identity language
                            "punctuation-belongs-under-sym" name)))
                   (t
                    (sr-validate-surfaces
                      identity
                      (решта surfaces)
                      (сполучити language entry-languages)
                      (sr-uniq-add language all-surfaces)
                      (або has-sym (sr-same? language "sym")))))))
              (t
               (sr-fail (список identity "surface-must-have-three-fields" surface)))))
           (t
            (sr-fail (список identity "surface-must-be-list" surface)))))))))

(визначити sr-validate-entries
  (функція (entries seen-ids all-surfaces symbolic-count count)
    (за-умовою
      ((атом? entries) (structural-kind empty-list)
       (за-умовою
         ((= count 0)
          (sr-fail (список "registry-has-no-semantic-identities")))
         (t
          (список "ok" count all-surfaces symbolic-count))))
      ((атом? entries) (structural-kind atom)
       (sr-fail (список "registry-tail-not-list" entries)))
      ((атом? entries) (structural-kind pair)
       (нехай ((entry (перше entries)))
         (за-умовою
           ((sr-nonempty-list? entry)
            (за-умовою
              ((>= (довжина entry) 2)
               (нехай ((identity (перше entry)))
                 (за-умовою
                   ((хибне? (string? identity))
                    (sr-fail (список "semantic-id-must-be-token" identity)))
                   ((хибне? (sr-valid-id? identity))
                    (sr-fail (список "semantic-id-must-be-four-plus-digits" identity)))
                   ((sr-member? identity seen-ids)
                    (sr-fail (список "duplicate-semantic-id" identity)))
                   (t
                    (нехай ((surface-result
                            (sr-validate-surfaces
                              identity
                              (решта entry)
                              (як-є ())
                              all-surfaces
                              (як-є ()))))
                      (sr-validate-entries
                        (решта entries)
                        (сполучити identity seen-ids)
                        (second surface-result)
                        (за-умовою
                          ((third surface-result) (додати symbolic-count 1))
                          (t symbolic-count))
                        (додати count 1)))))))
              (t
               (sr-fail (список "malformed-semantic-entry" entry)))))
           (t
            (sr-fail (список "malformed-semantic-entry" entry)))))))))

(визначити sr-insert-string
  (функція (value sorted)
    (за-умовою
      ((атом? sorted) (structural-kind empty-list) (список value))
      ((атом? sorted) (structural-kind atom) (список value sorted))
      ((атом? sorted) (structural-kind pair)
       (за-умовою
         ((текст-передує? value (перше sorted)) (сполучити value sorted))
         (t
          (сполучити (перше sorted)
                (sr-insert-string value (решта sorted)))))))))

(визначити sr-sort-strings
  (функція (values acc)
    (за-умовою
      ((атом? values) (structural-kind empty-list) acc)
      ((атом? values) (structural-kind atom) (sr-insert-string values acc))
      ((атом? values) (structural-kind pair)
       (sr-sort-strings
         (решта values)
         (sr-insert-string (перше values) acc))))))

(визначити sr-join-space
  (функція (values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) "")
      ((атом? values) (structural-kind atom) values)
      ((атом? values) (structural-kind pair)
       (за-умовою
         ((атом? (решта values)) (structural-kind empty-list) (перше values))
         ((атом? (решта values)) (structural-kind atom)
          (рядок-додати
            (перше values)
            (рядок-додати " " (решта values))))
         ((атом? (решта values)) (structural-kind pair)
          (рядок-додати
            (перше values)
            (рядок-додати
              " "
              (sr-join-space (решта values))))))))))

(визначити sr-source
  (read-file "lib/surface/semantic-registry.lisp"))

(визначити sr-parsed
  (sr-parse-root (sr-tokenize sr-source)))

(за-умовою
  ((sr-same? (перше sr-parsed) "error")
   (sr-fail (second sr-parsed)))
  (t
   (нехай ((root (second sr-parsed)))
     (за-умовою
       ((хибне? (sr-nonempty-list? root))
        (sr-fail (список "registry-root-must-be-list")))
       ((хибне? (sr-same? (перше root) "sr/1"))
        (sr-fail (список "registry-must-start-with-sr/1" (перше root))))
       (t
        (нехай-послідовно ((result
                 (sr-validate-entries
                   (решта root)
                   (як-є ())
                   (як-є ())
                   0
                   0))
               (identity-count (second result))
               (surface-names (sr-sort-strings (third result) (як-є ())))
               (symbolic-count (fourth result))
               (a (показати
                    (рядок-додати
                      "semantic registry: "
                      (рядок-додати
                        (число-рядок identity-count)
                        " identities\n"))))
               (b (показати
                    (рядок-додати
                      "surfaces: "
                      (рядок-додати
                        (sr-join-space surface-names)
                        "\n"))))
               (c (показати
                    (рядок-додати
                      "shared symbolic identities: "
                      (рядок-додати
                        (число-рядок symbolic-count)
                        "\n"))))
               (d (показати "numeric-only authority: CONFIRMED\n"))
               (e (показати "meaning-first shape: CONFIRMED\n")))
          (як-є semantic-registry-ok)))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити число-рядок number->string)
(визначити показати princ)
(визначити текст-у-символ string->symbol)
(визначити рядок-додати string-append)
(визначити рядок-порожній? string-empty?)
(визначити рядок-перший string-first)
(визначити рядок-решта string-rest)
(визначити текст-передує? string<?)
(визначити значення-у-текст write-to-string)
