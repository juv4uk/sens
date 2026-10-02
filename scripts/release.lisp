; Випуск підготовленого snapshot: sens scripts/release.lisp 0.41.0
; Версії семи Cargo.toml, Cargo.lock та packaging/install.sh оновлюються в PR.
; Скрипт перевіряє чистий checkout, відповідність origin/main, версії та
; зелений CI цього SHA. Не комітить файли й не пересуває наявні теги.
; Після push тегу workflow Release повторює focused test/clippy gates.
; Потрібні git, gh, timeout і cargo. Лише довірена CLI-сесія.

(00001001 release-preflight-failed
  (00001000 ()
    (00000101 (00000001 ()))))

(00001001 release-require
  (00001000 (label actual expected)
    (00000111
      ((00100010 actual expected) (1) actual)
      ((00100010 actual expected) (0)
       ((00001000 ()
          (01001000 label)
          (01001000 actual)
          (release-preflight-failed)))))))

(00001001 release-run
  (00001000 (program arguments)
    (10011100 ((result (10100010 program arguments)))
      ((00001000 ()
         (release-require program (00000101 result) 0)
         (00101111 result))))))

(release-require "Потрібна одна версія: 0.41.0" (00100001 (10110001 (00000010 *argv*)))
                 (00000001 (0)))
(release-require "Потрібен рівно один аргумент" (00100001 (10110001 (00000010 (00000110 *argv*))))
                 (00000001 ()))
(00001001 release-version (00000101 *argv*))
(00001001 release-tag (00111010 "l" release-version))
(00001001 release-tag-ref (00111010 "refs/tags/" release-tag))

(release-run "git" (00100111 "check-ref-format" release-tag-ref))
(release-require "Checkout має бути чистим"
  (release-run "git" (00000001 ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-require "Release запускається тільки з main"
  (release-run "git" (00000001 ("branch" "--show-current"))) "main\n")
(release-run "timeout" (00000001 ("60" "git" "fetch" "origin" "main")))
(release-require "HEAD має дорівнювати свіжому origin/main"
  (release-run "git" (00000001 ("log" "-1" "--pretty=format:%H" "HEAD")))
  (release-run "git" (00000001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-run "cargo"
  (00000001 ("run" "--release" "--locked" "-p" "sens-cli" "--bin" "gen-fasl"
          "--" "lib/core.lisp" "lib/core4.lisp.fasl")))
(00001001 release-fasl-diff-status
  (00000101 (10100010 "git" (00000001 ("diff" "--quiet" "--" "lib/core4.lisp.fasl")))))
(00000111
  ((00000011 release-fasl-diff-status 0) (1) (00000001 ()))
  ((00000011 release-fasl-diff-status 1) (1)
   ((00001000 ()
      (release-run "git" (00000001 ("add" "lib/core4.lisp.fasl")))
      (release-run "git" (00000001 ("commit" "-m" "chore(fasl): regenerate Core4 snapshot")))
      (release-run "timeout" (00000001 ("60" "git" "push" "origin" "main")))))
  (t
   ((00001000 ()
      (01001000 "Не вдалося визначити стан regenerated FASL")
      (01001000 release-fasl-diff-status)
      (release-preflight-failed))))))
(release-run "timeout" (00000001 ("60" "git" "fetch" "origin" "main")))
(00001001 release-head (release-run "git" (00000001 ("log" "-1" "--pretty=format:%H" "HEAD"))))
(release-require "HEAD має дорівнювати свіжому origin/main"
  release-head (release-run "git" (00000001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))

(00001001 release-check-manifests
  (00001000 (paths)
    (00000111
      ((00000010 paths) () (00000001 ()))
      ((00000010 paths) (0)
       ((00001000 ()
          (release-require (00000101 paths)
            (00111110
              (00111010 "version = \"" (00111010 release-version "\""))
              (10100110 (00000101 paths))) t)
          (release-check-manifests (00000110 paths))))))))

(release-check-manifests
  (00000001 ("crates/sens/Cargo.toml" "crates/sens-cli/Cargo.toml"
          "crates/sens-literate/Cargo.toml" "crates/sens-wasm/Cargo.toml"
          "crates/sens-lsp/Cargo.toml" "crates/sens-host/Cargo.toml"
          "crates/sens-semantic/Cargo.toml")))
; pretty=format дає SHA без кінцевого newline.
(release-require "Потрібен успішний CI для точного HEAD на main"
  (release-run "timeout"
    (00100111 "60" "gh" "run" "list" "--branch" "main" "--commit" release-head
          "--workflow" "CI" "--limit" "20" "--json" "conclusion,status"
          "--jq" "any(.[]; .status == \"completed\" and .conclusion == \"success\")"))
  "true\n")
; main міг змінитися під час попередніх перевірок.
(release-run "timeout" (00000001 ("60" "git" "fetch" "origin" "main")))
(release-require "origin/main змінився; підготуй новий snapshot"
  release-head (release-run "git" (00000001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-require "Релізний тег уже існує"
  (release-run "timeout" (00100111 "60" "git" "ls-remote" "--tags" "origin" release-tag-ref)) "")
(release-require "Checkout змінився під час перевірок"
  (release-run "git" (00000001 ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-run "git" (00100111 "tag" release-tag release-head))
(release-run "timeout" (00100111 "60" "git" "push" "origin" release-tag-ref))
(01001000 (00111010 "Тег опубліковано; очікуй завершення workflow Release: " release-tag))
