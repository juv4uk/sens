# Swarm typed event topics — convention

Single source of truth for the topic vocabulary used by the
four-repository swarm (`my-lisp`, `cml`, `fpga-lisp`, `my-idea`) over
the TCP event channel (`my-lisp --tcp=9999 --protocol=sexpr`).

Each repo's `AGENTS.md` references this file instead of restating its
own (drifting) copy. This is a *convention*, not a protocol change —
`subscribe`/`publish` already accepts arbitrary string topics; this
document fixes the vocabulary so a publisher and a subscriber mean the
same thing.

Author: opencode, 2026-08-12. Reviewed by the `my-lisp` session
2026-08-12 (later): one correction below (the wire format didn't match
the actual `publish` implementation), otherwise as written. Supersedes
the "Typed event topics" section of `docs/swarm-coordination.md`.

## Two rules that everything else depends on

1. **Event = doorbell, artifact = truth.** A `publish`/`notify` payload
   is a *pointer* ("go look"), never the fact itself. If a message
   carries the fact inline, it has already drifted from the artifact —
   don't. Always include the `artifact` field (file path, task id, or
   commit) the receiver should go read.
2. **File first, pointer later.** Anything durable (a proposal, a
   design, a status that outlives the process) goes to a file
   (`NOTE-*.md`, `docs/`, `evidence/`) *before* any topic carries its
   pointer. Every swarm op (`notify`/`publish`/`presence`/`claim`/
   tasks) resets on server restart — the pointer costs nothing to
   resend; the content wouldn't have survived anyway.

## Canonical topic set

Topic names are lowercase, hyphenated, one word, one meaning:

```
agent-joined          an agent registered presence (op hello)
agent-left            an agent went away (heartbeat aged out)
agent-blocked         an agent hit a () it can't clear alone

task-created          a task was defined (op define-task)
claim-taken           a task was claimed (op claim)
claim-released        a task was released (op release)
task-completed        a task finished (op complete-task)

need-published        an agent published a need (op capability-request)
offer-published       an agent offers a capability it can help with
capability-request    help request that matched an agent's capabilities

handoff-created       a handoff artifact was produced (use with artifact)
dependency-satisfied  a dependency another agent waited on is now met
contract-changed      a contract file changed (language/ISA/compatibility)
evidence-created      an evidence file appeared under evidence/
```

## Required fields per topic

Every `publish` must carry `from` + `topic`; beyond that:

| topic                | required fields                          | example artifact            |
|----------------------|------------------------------------------|-----------------------------|
| `evidence-created`   | `artifact`, `requirement`                | `evidence/G8/fpga-lisp/a81c.lisp` |
| `handoff-created`    | `artifact`, `to`                         | `HANDOFF-ISA-RATIONAL-001`  |
| `contract-changed`   | `artifact`                               | `language-contract.lisp`      |
| `dependency-satisfied` | `artifact`, `for`                      | task id of the unblocked one|
| `need-published`     | `needs`, `task`                          | capability name             |
| `task-created`       | `task`, `priority`                       | task id                     |
| all others           | `artifact` when one exists, else `task`  | —                           |

`artifact` is always a pointer into the durable plane — a relative
repo path, a task id, or a commit. Payloads never restate the content
behind the pointer.

## Default subscriptions by agent

Per the design, each agent subscribes only to what wakes it up:

```
my-lisp:    (contract-changed evidence-created need-published agent-blocked)
cml:        (contract-changed handoff-created dependency-satisfied need-published)
fpga-lisp:  (isa-contract-changed evidence-created need-published)  ;; alias of contract-changed with scope isa
my-idea:    ()   ;; empty / `*` — the Observatory wants everything
opencode:   (agent-joined agent-blocked capability-request handoff-created)
```

`my-idea`'s Observatory is the designated "read everything" subscriber;
everyone else keeps a narrow list. If a topic genuinely needs to be
scoped (e.g. `isa-contract-changed` vs `language-contract-changed`),
use a `scope` field, don't invent a new free-form topic — the canonical
set stays closed, additions go through a docs change, not a payload.

## Wire format reminder

```lisp
(request (id 1) (op publish) (from "fpga-lisp") (topic "evidence-created")
         (requirement "G8") (artifact "evidence/G8/fpga-lisp/a81c.lisp"))
```

```lisp
(request (id 2) (op subscribe) (topics (handoff-created dependency-satisfied)))
```

## Adding a topic

Propose it in a file first (this doc or a `NOTE-*.md`), let the four
repos acknowledge, then start publishing it. The closed set is what
keeps "an event is a doorbell" honest — an open free-text topic space is
the first step back to a global chat nobody reads.
