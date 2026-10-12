; Випуск підготовленого snapshot: sens scripts/release.lisp 0.41.0
; Версії семи Cargo.toml, Cargo.lock та packaging/install.sh оновлюються в PR.
; Скрипт перевіряє чистий checkout, відповідність origin/main, версії та
; зелений CI цього SHA. Не комітить файли й не пересуває наявні теги.
; Після push тегу workflow Release повторює focused test/clippy gates.
; Потрібні git, gh, timeout і cargo. Лише довірена CLI-сесія.

(0011 release-preflight-failed
  (0010 ()
    (100 (001 ()))))

(0011 release-require
  (0010 (label actual expected)
    (110
      ((11110111 actual expected) (1) actual)
      ((11110111 actual expected) (0)
       ((0010 ()
          (11011011 label)
          (11011011 actual)
          (release-preflight-failed)))))))

(0011 release-run
  (0010 (program arguments)
    (001000 ((result (110101111 program arguments)))
      ((0010 ()
         (release-require program (100 result) 0)
         (1001 result))))))

(release-require "Потрібна одна версія: 0.41.0" (0100 (110111011 (010 *argv*)))
                 (001 (0)))
(release-require "Потрібен рівно один аргумент" (0100 (110111011 (010 (011 *argv*))))
                 (001 ()))
(0011 release-version (100 *argv*))
(0011 release-tag (110011110 "l" release-version))
(0011 release-tag-ref (110011110 "refs/tags/" release-tag))

(release-run "git" (1110 "check-ref-format" release-tag-ref))
(release-require "Checkout має бути чистим"
  (release-run "git" (001 ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-require "Release запускається тільки з main"
  (release-run "git" (001 ("branch" "--show-current"))) "main\n")
(release-run "timeout" (001 ("60" "git" "fetch" "origin" "main")))
(release-require "HEAD має дорівнювати свіжому origin/main"
  (release-run "git" (001 ("log" "-1" "--pretty=format:%H" "HEAD")))
  (release-run "git" (001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-run "cargo"
  (001 ("run" "--release" "--locked" "-p" "sens-cli" "--bin" "gen-fasl"
          "--" "lib/core4.lisp" "lib/core4.lisp.fasl")))
(0011 release-fasl-diff-status
  (100 (110101111 "git" (001 ("diff" "--quiet" "--" "lib/core4.lisp.fasl")))))
(110
  ((101 release-fasl-diff-status 0) (1) (001 ()))
  ((101 release-fasl-diff-status 1) (1)
   ((0010 ()
      ; Never create an implicit commit while preparing an exact-SHA release.
      ; The snapshot must be reviewed and committed by the single main writer
      ; in a separate change, then all exact-SHA gates must be replayed.
      (11011011 "RELEASE_BLOCKED: Core4 FASL differs from pinned main; no automatic commit/push")
      (release-preflight-failed)))
  (t
   ((0010 ()
      (11011011 "Не вдалося визначити стан regenerated FASL")
      (11011011 release-fasl-diff-status)
      (release-preflight-failed))))))
(release-run "timeout" (001 ("60" "git" "fetch" "origin" "main")))
(0011 release-head (release-run "git" (001 ("log" "-1" "--pretty=format:%H" "HEAD"))))
(release-require "HEAD має дорівнювати свіжому origin/main"
  release-head (release-run "git" (001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))

(0011 release-check-manifests
  (0010 (paths)
    (110
      ((010 paths) () (001 ()))
      ((010 paths) (0)
       ((0010 ()
          (release-require (100 paths)
            (110101000
              (110011110 "version = \"" (110011110 release-version "\""))
              (110110111 (100 paths))) t)
          (release-check-manifests (011 paths))))))))

(release-check-manifests
  (001 ("crates/sens/Cargo.toml" "crates/sens-cli/Cargo.toml"
          "crates/sens-literate/Cargo.toml" "crates/sens-wasm/Cargo.toml"
          "crates/sens-lsp/Cargo.toml" "crates/sens-host/Cargo.toml"
          "crates/sens-semantic/Cargo.toml")))
; pretty=format дає SHA без кінцевого newline.
(release-require "Потрібен успішний CI для точного HEAD на main"
  (release-run "timeout"
    (1110 "60" "gh" "run" "list" "--branch" "main" "--commit" release-head
          "--workflow" "CI" "--limit" "20" "--json" "conclusion,status"
          "--jq" "any(.[]; .status == \"completed\" and .conclusion == \"success\")"))
  "true\n")
; main міг змінитися під час попередніх перевірок.
(release-run "timeout" (001 ("60" "git" "fetch" "origin" "main")))
(release-require "origin/main змінився; підготуй новий snapshot"
  release-head (release-run "git" (001 ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-require "Релізний тег уже існує"
  (release-run "timeout" (1110 "60" "git" "ls-remote" "--tags" "origin" release-tag-ref)) "")
(release-require "Checkout змінився під час перевірок"
  (release-run "git" (001 ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-run "git" (1110 "tag" release-tag release-head))
(release-run "timeout" (1110 "60" "git" "push" "origin" release-tag-ref))
(11011011 (110011110 "Тег опубліковано; очікуй завершення workflow Release: " release-tag))
