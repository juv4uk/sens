# SENS core · Ядро SENS · SENS-Kern

> **A small language that grows itself. · Маленька мова, що вирощує себе. · Eine kleine Sprache, die sich selbst wachsen lässt.**

An independent, capability-free Rust library for **SENS**. It provides the Rust implementation of the language runtime without a host-application dependency.

Незалежна Rust-бібліотека без доступу до системних можливостей для **SENS**. Вона надає реалізацію мовного середовища виконання без залежності від хост-застосунку.

Eine unabhängige Rust-Bibliothek ohne Host-Fähigkeiten für **SENS**. Sie stellt die Rust-Implementierung der Laufzeit ohne Abhängigkeit von einer Host-Anwendung bereit.

Human-readable language projections use `.lisp`; encoded SENS streams use `.sens`. · Людські мовні проекції мають розширення `.lisp`, закодовані потоки SENS — `.sens`. · Menschenlesbare Sprachprojektionen verwenden `.lisp`, kodierte SENS-Ströme `.sens`.

## Contract · Контракт · Vertrag

- `quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond`
- UTF-8 symbols, comments, strings, numbers, lists, and `(quote ...)` syntax
- UTF-8-символи, коментарі, рядки, числа, списки та синтаксис `(quote ...)`
- UTF-8-Symbole, Kommentare, Zeichenketten, Zahlen, Listen und `(quote ...)`-Syntax
- structured errors with source spans · структуровані помилки з діапазонами коду · strukturierte Fehler mit Quellbereichen
- no Tauri, filesystem, network, or UI dependency · без залежності від Tauri, файлів, мережі чи UI · keine Abhängigkeit von Tauri, Dateisystem, Netzwerk oder UI

Rust contains the minimal semantic machinery, including lexical `lambda`. Derived forms and library functions will be bootstrapped in the language itself.

Rust містить мінімальну семантичну механіку, включно з лексичною `lambda`. Похідні форми та бібліотечні функції розгортатимуться самою мовою.

Rust enthält die minimale semantische Mechanik einschließlich lexikalischem `lambda`. Abgeleitete Formen und Bibliotheksfunktionen werden in der Sprache selbst gebootstrappt.

## Test · Тестування · Test

```sh
cargo test -p sens
```

The crate is versioned with the SENS workspace. The language contract is maintained in [`language-contract.lisp`](../../language-contract.lisp).

Версія крейта керується разом із робочим простором SENS. Контракт мови ведеться у [`language-contract.lisp`](../../language-contract.lisp).

Die Version des Crates wird gemeinsam mit dem SENS-Workspace verwaltet. Der Sprachvertrag liegt in [`language-contract.lisp`](../../language-contract.lisp).
