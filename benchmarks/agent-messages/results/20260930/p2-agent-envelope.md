# P2 — мінімальний binary envelope для agent bus

**Issue:** #1845  
**Статус:** research / design only — **не** новий semantic authority, **не** зміна `lower.rs`  
**Опора:** існуючий SENS wire (`SW\\x01` у `syntax.rs`), harness `agent_bench`, виміри `report.md` / `p1-wire-as-transport.md`

## Мета

Зафіксувати найменший чесний шар для обміну **маленькою програмою** між агентами:

1. стабільна ідентичність операцій (Function8),
2. компактне тіло програми (wire),
3. місце під 1-bit predicate result (коли absolute-binary Predicate1 стабільний),
4. без претензії «portable як marshal».

## Що вже є в коді (не винаходити)

### Framing (зовнішній запис потоку)

`agent_bench` / `run.py`:

```text
record ::= u32_le(length) || payload_bytes
stream ::= record*
```

Це **transport framing**, не частина мови.

### Payload = SENS wire

```text
wire_program ::= "SW" 0x01 || expr*
```

Ключові теги (з `syntax.rs` mod `wire`):

| код | сенс |
|-----|------|
| `0x00..0x3F` | мале ціле 0..63 |
| `0x40..0x4F` | короткий список 0..15 елементів |
| `0x51` + 1 байт | **Function8 / Sid** |
| `0x50` + varint | довгий список |
| `0x52`… | integer / number / rational / string / symbol / pair / local |

Function identity у payload = **тег + 1 байт**, не рядок.

### Fasl — не envelope для bus

Fasl (`MYF1` + version + **32-byte source hash** + …) — кеш розбору ядра.  
Середній розмір повідомлення ~154 B vs wire ~34 B — hash/заголовок, не Function8.  
Для agent bus **не** рекомендується як default envelope.

## Пропонований мінімальний envelope (v0 research)

Не новий codec і не новий Function8. Лише **узгодження шарів**:

```text
agent_record_v0 =
    u32_le(body_len)
  || body

body =
    wire_program          ; SW\x01 … (виконуване тіло)
  [ || result_trailer ]   ; опційно, окремим record або суфіксом — див. нижче
```

### Варіант A — request/response як два record’и (рекомендований v0)

```text
→  record{ wire_program }           ; програма
←  record{ result_encoding }        ; відповідь
```

`result_encoding` v0 (research, fail-closed):

```text
RESULT1 magic = "SR" 0x01

  "SR" 0x01
  || kind:u8
       0x00 = PredicateBit   + 1 byte (0=NO, 1=YES)     ; лише якщо runtime вже Predicate1
       0x01 = Number exact   + wire number encoding     ; reuse wire number tags
       0x02 = WireExpr       + wire expr                ; довільне значення як data
       0xFF = Error          + varint len + utf8        ; host/debug only, не semantic core
```

Поки PredicateBit **не** в canonical wire (#1818 area): не серіалізувати predicate як Number `0`/`1`.  
Краще: `0x02 WireExpr` для звичайних відповідей бенчу; `0x00` увімкнути лише після стабільного Predicate1 contract.

### Варіант B — один record (програма only)

Як зараз у `agent-messages`: лише програма, результат лишається в-процесі.  
Достатньо для decode+execute бенчу; недостатньо для міжпроцесного bus.

## Ідентичність

| шар | хто власник |
|-----|-------------|
| Function8 у тілі програми | language contract / registry |
| framing u32 length | host / bus |
| RESULT1 kind tags | **bus convention** (research), не Function8 table |
| human names / JSON | surface only, до lower |

Заборона (SENS-primary):
- не робити англійське ім’я каноном відповіді;
- не оголошувати RESULT1 «мовою» — це envelope поверх wire;
- не підміняти wire на py-marshal «бо швидше».

## Виміряний контекст (чому wire)

З `20260930/report.md` (payload-only):

| форма | B | decode | together |
|-------|--:|-------:|---------:|
| sens-wire | **34** | 12k | 56k |
| py-json | 48 | 25k | 70k |
| sens-fasl | 154 | 10k | 53k |
| py-marshal | 196 | 9k | **14k** |

- Envelope для **portable agent program** → **wire**.  
- Marshal швидший warm execute, але bytecode прив’язаний до версії CPython — **не** чесний portable agent format (явна межа #1845).

## Wall-clock TCP latency

P2 дозволяв secondary metric. **У цьому документі не міряємо** wall-clock:

- Cachegrind уже фіксує decode+execute;
- TCP loopback додає OS/noise, погано порівнюється між host’ами;
- окремий harness (listen/accept/write record / read record) — follow-up agent з мережею, не blocker для envelope design.

Якщо хтось мірятиме: окремий файл `results/YYYYMMDD/tcp-wallclock.md`, median ≥30, без змішування з I-refs.

## Acceptance P2 (research)

- [x] мінімальний envelope описаний поверх **існуючого** wire + u32 framing
- [x] identity / result / framing розділені
- [x] fasl і marshal явно не default для portable bus
- [x] Predicate1 trailer — опція з fail-closed, не Number coercion
- [ ] (optional follow-up) TCP wall-clock harness — out of scope цього PR

## Наступні кроки (не цей PR)

1. Коли Predicate1 стабільний у runtime+wire policy — додати RESULT1 `0x00` + тести round-trip.  
2. Окремий example `agent_bus_smoke` (encode wire → decode → eval → RESULT1) без зміни evaluator semantics.  
3. Не розширювати Function8 table під bus tags.
