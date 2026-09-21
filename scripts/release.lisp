; Випуск підготовленого snapshot: my-lisp scripts/release.lisp 0.41.0
; Версії семи Cargo.toml, Cargo.lock та packaging/install.sh оновлюються в PR.
; Скрипт перевіряє чистий checkout, відповідність origin/main, версії та
; зелений CI цього SHA. Не комітить файли й не пересуває наявні теги.
; Після push тегу workflow Release повторює focused test/clippy gates.
; Потрібні git, gh, timeout і cargo. Лише довірена CLI-сесія.

(def release-preflight-failed
  (lambda ()
    (car (quote ()))))

(def release-require
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) (structural-relation same) actual)
      ((equal? actual expected) (structural-relation distinct)
       ((lambda ()
          (print label)
          (print actual)
          (release-preflight-failed)))))))

(def release-run
  (lambda (program arguments)
    (let ((result (process-run program arguments)))
      ((lambda ()
         (release-require program (car result) 0)
         (second result))))))

(release-require "Потрібна одна версія: 0.41.0" (atom *argv*)
                 (quote (structural-kind pair)))
(release-require "Потрібен рівно один аргумент" (atom (cdr *argv*))
                 (quote (structural-kind empty-list)))
(def release-version (car *argv*))
(def release-tag (string-append "l" release-version))
(def release-tag-ref (string-append "refs/tags/" release-tag))

(release-run "git" (list "check-ref-format" release-tag-ref))
(release-require "Checkout має бути чистим"
  (release-run "git" (quote ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-require "Release запускається тільки з main"
  (release-run "git" (quote ("branch" "--show-current"))) "main\n")
(release-run "timeout" (quote ("60" "git" "fetch" "origin" "main")))
(release-require "HEAD має дорівнювати свіжому origin/main"
  (release-run "git" (quote ("log" "-1" "--pretty=format:%H" "HEAD")))
  (release-run "git" (quote ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-run "cargo"
  (quote ("run" "--release" "--locked" "-p" "my-lisp-cli" "--bin" "gen-fasl"
          "--" "lib/core.lisp" "lib/core.lisp.fasl")))
(def release-fasl-diff-status
  (car (process-run "git" (quote ("diff" "--quiet" "--" "lib/core.lisp.fasl")))))
(cond
  ((eq release-fasl-diff-status 0) (identity-relation same) (quote ()))
  ((eq release-fasl-diff-status 1) (identity-relation same)
   ((lambda ()
      (release-run "git" (quote ("add" "lib/core.lisp.fasl")))
      (release-run "git" (quote ("commit" "-m" "chore(fasl): regenerate core snapshot")))
      (release-run "timeout" (quote ("60" "git" "push" "origin" "main")))))
  (t
   ((lambda ()
      (print "Не вдалося визначити стан regenerated FASL")
      (print release-fasl-diff-status)
      (release-preflight-failed))))))
(release-run "timeout" (quote ("60" "git" "fetch" "origin" "main")))
(def release-head (release-run "git" (quote ("log" "-1" "--pretty=format:%H" "HEAD"))))
(release-require "HEAD має дорівнювати свіжому origin/main"
  release-head (release-run "git" (quote ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))

(def release-check-manifests
  (lambda (paths)
    (cond
      ((atom paths) (structural-kind empty-list) (quote ()))
      ((atom paths) (structural-kind pair)
       ((lambda ()
          (release-require (car paths)
            (string-contains?
              (string-append "version = \"" (string-append release-version "\""))
              (read-file (car paths))) t)
          (release-check-manifests (cdr paths))))))))

(release-check-manifests
  (quote ("crates/my-lisp/Cargo.toml" "crates/my-lisp-cli/Cargo.toml"
          "crates/my-lisp-literate/Cargo.toml" "crates/my-lisp-wasm/Cargo.toml"
          "crates/my-lisp-lsp/Cargo.toml" "crates/my-lisp-host/Cargo.toml"
          "crates/my-lisp-semantic/Cargo.toml")))
; pretty=format дає SHA без кінцевого newline.
(release-require "Потрібен успішний CI для точного HEAD на main"
  (release-run "timeout"
    (list "60" "gh" "run" "list" "--branch" "main" "--commit" release-head
          "--workflow" "CI" "--limit" "20" "--json" "conclusion,status"
          "--jq" "any(.[]; .status == \"completed\" and .conclusion == \"success\")"))
  "true\n")
; main міг змінитися під час попередніх перевірок.
(release-run "timeout" (quote ("60" "git" "fetch" "origin" "main")))
(release-require "origin/main змінився; підготуй новий snapshot"
  release-head (release-run "git" (quote ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-require "Релізний тег уже існує"
  (release-run "timeout" (list "60" "git" "ls-remote" "--tags" "origin" release-tag-ref)) "")
(release-require "Checkout змінився під час перевірок"
  (release-run "git" (quote ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-run "git" (list "tag" release-tag release-head))
(release-run "timeout" (list "60" "git" "push" "origin" release-tag-ref))
(print (string-append "Тег опубліковано; очікуй завершення workflow Release: " release-tag))
