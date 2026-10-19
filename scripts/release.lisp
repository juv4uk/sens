; Випуск підготовленого snapshot: sens scripts/release.lisp 0.42.0
; Версії семи Cargo.toml, Cargo.lock та packaging/install.sh оновлюються в PR.
; Скрипт перевіряє чистий checkout, відповідність origin/main, версії та
; зелений CI цього SHA. Не комітить файли й не пересуває наявні теги.
; Після push тегу workflow Release повторює focused test/clippy gates.
; Потрібні git, gh, timeout і cargo. Лише довірена CLI-сесія.

(визначити release-preflight-failed
  (функція ()
    (перше (як-є ()))))

(визначити release-require
  (функція (label actual expected)
    (за-умовою
      ((тотожне? actual expected) actual)
      ((атом? (як-є ()))
       ((функція ()
          (друкувати label)
          (друкувати actual)
          (release-preflight-failed)))))))

(визначити release-run
  (функція (program arguments)
    (нехай ((result (процес-запустити program arguments)))
      ((функція ()
         (release-require program (перше result) 0)
         (друге result))))))

(release-require "Потрібна одна версія: 0.42.0" (хибне? (відповідь-не (атом? *argv*)))
                 (як-є (0)))
(release-require "Потрібен рівно один аргумент" (хибне? (відповідь-не (атом? (решта *argv*))))
                 (як-є ()))
(визначити release-version (перше *argv*))
(визначити release-tag (рядок-додати "l" release-version))
(визначити release-tag-ref (рядок-додати "refs/tags/" release-tag))

(release-run "git" (список "check-ref-format" release-tag-ref))
(release-require "Checkout має бути чистим"
  (release-run "git" (як-є ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-require "Release запускається тільки з main"
  (release-run "git" (як-є ("branch" "--show-current"))) "main\n")
(release-run "timeout" (як-є ("60" "git" "fetch" "origin" "main")))
(release-require "HEAD має дорівнювати свіжому origin/main"
  (release-run "git" (як-є ("log" "-1" "--pretty=format:%H" "HEAD")))
  (release-run "git" (як-є ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-run "cargo"
  (як-є ("run" "--release" "--locked" "-p" "sens-cli" "--bin" "gen-fasl"
          "--" "lib/core4.lisp" "lib/core4.lisp.fasl")))
(визначити release-fasl-diff-status
  (перше (процес-запустити "git" (як-є ("diff" "--quiet" "--" "lib/core4.lisp.fasl")))))
(за-умовою
  ((тотожне? release-fasl-diff-status 0) (як-є ()))
  ((тотожне? release-fasl-diff-status 1)
   ((функція ()
      ; Never create an implicit commit while preparing an exact-SHA release.
      ; The snapshot must be reviewed and committed by the single main writer
      ; in a separate change, then all exact-SHA gates must be replayed.
      (друкувати "RELEASE_BLOCKED: Core4 FASL differs from pinned main; no automatic commit/push")
      (release-preflight-failed))))
  ((атом? (як-є ()))
   ((функція ()
      (друкувати "Не вдалося визначити стан regenerated FASL")
      (друкувати release-fasl-diff-status)
      (release-preflight-failed)))))
(release-run "timeout" (як-є ("60" "git" "fetch" "origin" "main")))
(визначити release-head (release-run "git" (як-є ("log" "-1" "--pretty=format:%H" "HEAD"))))
(release-require "HEAD має дорівнювати свіжому origin/main"
  release-head (release-run "git" (як-є ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))

(визначити release-check-manifests
  (функція (paths)
    (за-умовою
      ((атом? paths) (як-є ()))
      ((атом? (як-є ()))
       ((функція ()
          (release-require (перше paths)
            (рядок-містить?
              (рядок-додати "version = \"" (рядок-додати release-version "\""))
              (читати-файл (перше paths))) t)
          (release-check-manifests (решта paths))))))))

(release-check-manifests
  (як-є ("crates/sens/Cargo.toml" "crates/sens-cli/Cargo.toml"
          "crates/sens-literate/Cargo.toml" "crates/sens-wasm/Cargo.toml"
          "crates/sens-lsp/Cargo.toml" "crates/sens-host/Cargo.toml"
          "crates/sens-semantic/Cargo.toml")))
; pretty=format дає SHA без кінцевого newline.
; Active pre-tag gates must both complete green on this exact SHA.
; Release Preflight includes cargo test/clippy --workspace; Hosted CI provides
; separate strict Core/runtime witnesses. Do not rely on any older green run.
(release-require "Hosted CI не зелений на точному SHA"
  (release-run "timeout"
    (список "60" "gh" "run" "list" "--branch" "main" "--commit" release-head
          "--workflow" "ci-hosted.yml" "--limit" "1" "--json" "conclusion,status"
          "--jq" "length == 1 and .[0].status == \"completed\" and .[0].conclusion == \"success\""))
  "true\n")
(release-require "Release Preflight не зелений на точному SHA"
  (release-run "timeout"
    (список "60" "gh" "run" "list" "--branch" "main" "--commit" release-head
          "--workflow" "release-preflight.yml" "--limit" "1" "--json" "conclusion,status"
          "--jq" "length == 1 and .[0].status == \"completed\" and .[0].conclusion == \"success\""))
  "true\n")
; The owner must authorize the exact SHA and tag before this script creates a tag.
(release-require "Немає явного дозволу власника для поточного SHA"
  (release-run "gh" (як-є ("variable" "get" "SENS_RELEASE_GO_SHA" "--repo" "juv4uk/sens")))
  (рядок-додати release-head "\n"))
(release-require "Немає явного дозволу власника для поточного тегу"
  (release-run "gh" (як-є ("variable" "get" "SENS_RELEASE_GO_TAG" "--repo" "juv4uk/sens")))
  (рядок-додати release-tag "\n"))
; main міг змінитися під час попередніх перевірок.
(release-run "timeout" (як-є ("60" "git" "fetch" "origin" "main")))
(release-require "origin/main змінився; підготуй новий snapshot"
  release-head (release-run "git" (як-є ("log" "-1" "--pretty=format:%H" "FETCH_HEAD"))))
(release-require "Релізний тег уже існує"
  (release-run "timeout" (список "60" "git" "ls-remote" "--tags" "origin" release-tag-ref)) "")
(release-require "Checkout змінився під час перевірок"
  (release-run "git" (як-є ("status" "--porcelain" "--untracked-files=normal"))) "")
(release-run "git" (список "tag" release-tag release-head))
(release-run "timeout" (список "60" "git" "push" "origin" release-tag-ref))
(друкувати (рядок-додати "Тег опубліковано; очікуй завершення workflow Release: " release-tag))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити відповідь-не ANSWER-NOT)
(визначити список LIST)
(визначити процес-запустити PROCESS-RUN)
(визначити рядок-додати STRING-APPEND)
