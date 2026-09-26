# Приватні залежності Core1

Workflow-и Core1 читають закріплені ревізії із приватних сусідніх репозиторіїв.
Вони мають залишатися приватними. Cross-repository автентифікація є лише
транспортним механізмом і не надає зовнішнім репозиторіям семантичної влади
над СЕНС.

## Схема облікових даних

Використовуємо **окремий read-only SSH deploy key для кожного приватного
репозиторію-залежності**.

| Залежність | Secret у `juv4uk/sens` |
| --- | --- |
| `juv4uk/mccarthy-eval` | `MCCARTHY_EVAL_SSH_KEY` |
| `juv4uk/wsm-my-lisp` | `WSM_MY_LISP_SSH_KEY` |

Для кожної залежності:

1. створити окрему SSH-пару ключів лише для цього checkout-шляху;
2. додати публічний ключ у **Deploy keys** цільового репозиторію, не
   вмикаючи write access;
3. приватний ключ зберегти в Actions secret з іменем із таблиці вище;
4. не використовувати особистий SSH-ключ, широкий PAT або ключ із правом запису;
5. у workflow залишати точний pinned commit SHA залежності.

Ключ передається лише в зовнішній крок `actions/checkout`. Для нього задано
`persist-credentials: false`, тому наступні команди не успадковують checkout
credentials.

## Межа pull request

Приватний checkout дозволений тільки для:

- `workflow_dispatch`; або
- pull request, у якого head repository збігається з base repository
  (`github.event.pull_request.head.repo.full_name == github.repository`).

Для fork/untrusted pull request приватний checkout та всі залежні від нього
кроки пропускаються. Локальні SENS-owned preflight-перевірки все одно
виконуються першими, після чого workflow завершується fail-closed з явною
діагностикою, а не видає неповний результат за Core1 evidence.

Не переводити ці workflow на `pull_request_target` із виконанням коду з head
pull request. Не робити приватні dependency-репозиторії публічними заради CI.

## Доказ

Приватний checkout має лишатися pinned і read-only. GREEN Core1 run доводить
лише роботу з конкретними закріпленими байтами залежності; це не робить
зовнішній репозиторій джерелом значення СЕНС.

## English

Core1 workflows consume pinned snapshots from private sibling repositories.
Keep one read-only SSH deploy key per dependency, store only the matching
private key in the named Actions secret, keep dependency SHAs pinned, and use
`persist-credentials: false`.

Private checkout is allowed only for manual dispatch or same-repository pull
requests. Fork or otherwise untrusted pull requests run local preflight checks,
skip private dependencies, and then fail closed. Do not use
`pull_request_target` to execute untrusted head code with these credentials.
