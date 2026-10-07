# D10 crossrepo my-idea v1

**Статус:** research / unratified  
**Central sweep:** #4182  
**Donor task:** juv4uk/my-idea#80  
**Single-stream authority:** #4162

my-idea розглядається не як окремий IDE namespace, а як donor language-visible laws до одного D10.

## Результат

```text
new meanings          13
D10 selected         540/1024
law-forced placed    256
unplaced selected    284
remaining            484
ratified D10           0
```

## Editor algebra

```text
EDITOR-REGISTER-COMMAND
EDITOR-SELECTION
EDITOR-BUFFER-TEXT
EDITOR-REPLACE-SELECTION
EDITOR-MESSAGE
EDITOR-REGISTER-KEYMAP
EDITOR-REGISTER-HANDLER
EDITOR-INVOKE-COMMAND
EDITOR-DISPATCH-KEY
EDITOR-EMIT-EVENT
```

Їхній meaning задається станом/ефектом/dispatch law, а не Tauri handle чи Rust pointer.

## Ecosystem/provenance laws

```text
SELF-BUILD-PLAN
EVIDENCE-LATEST-MATRIX
REPO-CAPABILITY-EDGES
```

SELF-BUILD-PLAN детерміновано будує план із явної provenance й обчислює digest.
EVIDENCE-LATEST-MATRIX залишає найновіший evidence record на пару requirement/implementation.
REPO-CAPABILITY-EDGES виводить ребра лише з явного imports/exports overlap.

## Що не стало residents

```text
plugins::load_plugins filesystem traversal
evidence::scan filesystem traversal
repo_graph::scan filesystem traversal
REPL actor channels
Tauri/window/process plumbing
canonical_plan_json
```

Serialization є projection; filesystem/process/Tauri — mechanism.

Усі 13 нових meanings лишаються UNPLACED. D10 не ратифікується.
