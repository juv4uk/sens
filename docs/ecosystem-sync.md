# Ecosystem sync channel · Канал синхронізації екосистеми · Ökosystem-Sync-Kanal

## English

`docs/ecosystem-roadmap.md` and `docs/versioning.md` already describe the target architecture — three independently versioned repositories (`my-lisp`, `fpga-lisp`, `cml`) kept compatible through explicit contract files (`language-contract.lisp`, a future `fpga-lisp` `ISA.md`, `cml`'s `compatibility.lisp`) plus a proposed non-blocking three-tier CI. That CI does not exist yet. This document records a cheaper interim channel that works today, without waiting on CI: a short, structured status exchange between the three repositories' active CCD sessions, persisted into [`../ecosystem-status.md`](../ecosystem-status.md) so later sessions can read current state without repeating the round-trip.

**Why this exists.** The guiding principle already stated in `docs/versioning.md` is "synchronize the boundaries, not the repositories." A live session-to-session message is the lightest possible boundary check — it costs nothing to build, and surfaces drift (a stale contract version, a newly blocking gap) immediately, long before any CI job would catch it.

**The request shape**, so a status ask/answer stays comparable across sessions over time:

1. Current contract version(s) on that repository's side — `language-contract.lisp`'s version for `my-lisp`, the ISA version for `fpga-lisp`, the pinned `(language contract, ISA)` pair for `cml`.
2. A concrete progress number where one exists — e.g. "N/M Tier-1 fixtures pass blind."
3. The next open gap(s) by name, not a vague "still working on things."
4. Whether anything on *this* repository's side is blocking the other — asked explicitly, so a () doesn't sit silently for weeks.

**How to use it.** From any session, use the CCD session-management message tool to find the other two repositories' active sessions (they show up as separate `cwd`s, typically `fpga-lisp` and `cml` next to this one) and send exactly this four-point ask. Then write the replies into [`../ecosystem-status.md`](../ecosystem-status.md) — one section per repository — so the next session (in this repo or another) can read current state from a file instead of repeating the same round-trip. Treat both the live replies and the file as a point-in-time status snapshot, not a persisted contract — the actual contract still lives in the versioned files (`language-contract.lisp`, `ISA.md`, `compatibility.lisp`), never in a chat message or in `ecosystem-status.md`.

**Not a replacement for the real thing.** This channel is deliberately informal and manual — a stopgap, not a substitute for the three-tier CI `docs/versioning.md` proposes. It should stop being needed once that CI exists; until then, it is cheaper than nothing and costs one message per side.

## Українська

`docs/ecosystem-roadmap.md` і `docs/versioning.md` уже описують цільову архітектуру — три незалежно версіоновані репозиторії (`my-lisp`, `fpga-lisp`, `cml`), узгоджені через явні контрактні файли (`language-contract.lisp`, майбутній `ISA.md` у `fpga-lisp`, `compatibility.lisp` у `cml`) плюс запропонований неблокуючий триярусний CI. Цей CI ще не існує. Цей документ фіксує дешевший тимчасовий канал, що працює вже сьогодні, не чекаючи CI: короткий, структурований обмін статусом між активними CCD-сесіями трьох репозиторіїв, зафіксований у [`../ecosystem-status.md`](../ecosystem-status.md), щоб наступні сесії могли читати поточний стан без повторення того самого round-trip.

**Навіщо це.** Провідний принцип уже сформульований у `docs/versioning.md`: "синхронізувати треба не репозиторії, а їхні межі". Живе повідомлення між сесіями — найлегша можлива перевірка межі: вона нічого не коштує побудувати й виявляє розсинхрон (застарілу версію контракту, новий блокуючий пробіл) одразу, задовго до того, як це піймав би будь-який CI.

**Форма запиту**, щоб статус був порівнюваний між сесіями з часом:

1. Поточна версія(ї) контракту на боці цього репозиторію — версія `language-contract.lisp` для `my-lisp`, версія ISA для `fpga-lisp`, зафіксована пара `(language contract, ISA)` для `cml`.
2. Конкретне число прогресу, де воно є — напр. "N/M Tier-1 fixtures проходять blind".
3. Наступний(і) відкритий(і) пробіл(и) на ім'я, не розпливчасте "ще працюємо".
4. Чи щось на боці *цього* репозиторію блокує інший — запитано явно, щоб блокер не лежав мовчки тижнями.

**Як користуватись.** З будь-якої сесії знайти активні сесії двох інших репозиторіїв (через session-management інструмент CCD; вони позначені окремими `cwd`, зазвичай `fpga-lisp` і `cml` поруч із цим) і надіслати саме ці чотири пункти. Відповіді — знімок статусу на момент часу, не постійний контракт: справжній контракт і далі живе у версіонованих файлах (`language-contract.lisp`, `ISA.md`, `compatibility.lisp`), ніколи в повідомленні чату.

**Не заміна справжньому механізму.** Цей канал навмисно неформальний і ручний — тимчасове рішення, не заміна триярусному CI з `docs/versioning.md`. Потреба в ньому має зникнути, щойно той CI з'явиться; до того часу він дешевший за нічого й коштує одне повідомлення з кожного боку.

## Deutsch

`docs/ecosystem-roadmap.md` und `docs/versioning.md` beschreiben bereits die Zielarchitektur — drei unabhängig versionierte Repositories (`my-lisp`, `fpga-lisp`, `cml`), kompatibel gehalten durch explizite Vertragsdateien (`language-contract.lisp`, ein zukünftiges `ISA.md` in `fpga-lisp`, `compatibility.lisp` in `cml`) plus eine vorgeschlagene, nicht blockierende dreistufige CI. Diese CI existiert noch nicht. Dieses Dokument hält einen günstigeren Übergangskanal fest, der schon heute funktioniert, ohne auf CI zu warten: einen kurzen, strukturierten Statusaustausch zwischen den aktiven CCD-Sitzungen der drei Repositories, festgehalten in [`../ecosystem-status.md`](../ecosystem-status.md), damit spätere Sitzungen den aktuellen Stand lesen können, ohne denselben Round-Trip zu wiederholen.

**Warum dies existiert.** Das bereits in `docs/versioning.md` formulierte Leitprinzip lautet: "synchronisiere die Grenzen, nicht die Repositories." Eine Sitzung-zu-Sitzung-Nachricht ist die leichtestmögliche Grenzprüfung — sie kostet nichts im Aufbau und deckt Drift (eine veraltete Vertragsversion, eine neue blockierende Lücke) sofort auf, lange bevor eine CI-Job das täte.

**Die Anfrageform**, damit eine Status-Anfrage/Antwort über Sitzungen hinweg vergleichbar bleibt:

1. Aktuelle Vertragsversion(en) auf der Seite dieses Repositories — `language-contract.lisp`s Version für `my-lisp`, die ISA-Version für `fpga-lisp`, das gepinnte Paar `(Sprachvertrag, ISA)` für `cml`.
2. Eine konkrete Fortschrittszahl, wo vorhanden — z. B. "N/M Tier-1-Fixtures bestehen blind."
3. Die nächste(n) offene(n) Lücke(n) namentlich, nicht ein vages "arbeiten noch daran."
4. Ob etwas auf der Seite *dieses* Repositories die andere blockiert — ausdrücklich gefragt, damit ein () nicht wochenlang still liegen bleibt.

**Verwendung.** Aus jeder Sitzung heraus die aktiven Sitzungen der beiden anderen Repositories finden (über das CCD-Sitzungsverwaltungswerkzeug; sie erscheinen mit eigenem `cwd`, typischerweise `fpga-lisp` und `cml` neben diesem) und genau diese vier Punkte senden. Die Antworten dann in [`../ecosystem-status.md`](../ecosystem-status.md) eintragen — ein Abschnitt pro Repository —, damit die nächste Sitzung den aktuellen Stand aus einer Datei lesen kann, statt denselben Round-Trip zu wiederholen. Sowohl die Live-Antworten als auch die Datei sind eine Momentaufnahme, kein dauerhafter Vertrag — der eigentliche Vertrag lebt weiterhin in den versionierten Dateien (`language-contract.lisp`, `ISA.md`, `compatibility.lisp`), nie in einer Chat-Nachricht oder in `ecosystem-status.md`.

**Kein Ersatz für das echte System.** Dieser Kanal ist bewusst informell und manuell — eine Übergangslösung, kein Ersatz für die in `docs/versioning.md` vorgeschlagene dreistufige CI. Der Bedarf dafür sollte verschwinden, sobald diese CI existiert; bis dahin ist er günstiger als nichts und kostet eine Nachricht pro Seite.
