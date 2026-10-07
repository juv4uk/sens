# D10 × wsm-os-lisp — межа власності

**Статус:** research / unratified  
**SENS issue:** #4045  
**WSM issue:** juv4uk/wsm-os-lisp#74

`wsm-os-lisp` — не просто backend. Це Target Runtime/OS і Lisp-machine package.

Тому D10 не повинен автоматично поглинати його machine/OS operations.

## Що лишається на Core-review

```text
SIGNAL-CONDITION
RESTART-AVAILABLE?
INVOKE-RESTART
USE-VALUE
```

Поки **0 нових D10 residents**.

Причина: поточний WSM condition record M5G навмисно non-resumable. D8 уже має ERROR/ERRORSET, D9 — DEFINE-CONDITION/DEHANDLER. Окремий continuable/restart law ще не доведений.

## Що належить wsm-os-lisp

### Debugger / live definitions
INSTALL-DEFINITION, DESCRIBE-DEFINITION, INSPECT-OBJECT, BACKTRACE-TASK, HEAP-SUMMARY, DISASSEMBLE-DEFINITION.

### Tasks
TASK-STATE, SUSPEND-TASK, RESUME-TASK, ABORT-TASK.

### Live image
SAVE-LIVE-IMAGE, RESTORE-LIVE-IMAGE, REBIND-CAPABILITIES.

### History
EVENT-HISTORY, EVENT-RING-APPEND.

### Devices
MMIO-CAPABILITY, MMIO-READ, MMIO-WRITE, PCI-CONFIG-READ, BLOCK-READ, BLOCK-WRITE, BLOCK-FLUSH.

### Memory
GC-COLLECT, ROOT-ENUMERATION.

Ці operations можуть бути першокласними в Lisp machine, але не займають D10 Core slots.

## Mechanism-only

RDTSC lowering, page-table walk, BAR discovery, VirtIO ring mechanics, UART polling, UEFI/QEMU handoff, native stack layout, конкретний copying-GC algorithm.

## Поточний ефект на D10

```text
before     400/1024
after      400/1024

new Core residents       0
WSM package semantics   24
mechanism-only           8
restart rows on HOLD     4
```

Ключова архітектура:

```text
SENS Core -> meaning
CML       -> lowering
WSM OS    -> living machine / image / debugger / devices
x86/UEFI  -> physical mechanism
```
