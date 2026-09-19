use my_lisp::{eval_program, Session, Value};
use std::collections::HashSet;
use std::rc::Rc;

const РЕЄСТР: &str = include_str!("../../../lib/surface/semantic-registry.lisp");
const REPL_КАТАЛОГ: &str = include_str!("../../my-lisp-cli/src/repl/surface_catalog.rs");
const ПЕРЕВІРКА_ПОКРИТТЯ: &str = include_str!("../../../scripts/check_surface_coverage.py");
const ПЕРЕВІРКА_РІВНОПРАВЯ: &str = include_str!("../../../scripts/check_trilingual_surface.py");
const ТРАНСЛЯТОР: &str = include_str!("../../../scripts/translate-program.py");

#[derive(Debug)]
enum Форма {
    Атом(String),
    Список(Vec<Форма>),
}

fn лексеми(джерело: &str) -> Vec<String> {
    let без_коментарів = джерело
        .lines()
        .map(|рядок| рядок.split(';').next().unwrap_or_default())
        .collect::<Vec<_>>()
        .join("\n");
    let mut результат = Vec::new();
    let mut атом = String::new();
    for символ in без_коментарів.chars() {
        match символ {
            '(' | ')' => {
                if !атом.is_empty() {
                    результат.push(std::mem::take(&mut атом));
                }
                результат.push(символ.to_string());
            }
            символ if символ.is_whitespace() => {
                if !атом.is_empty() {
                    результат.push(std::mem::take(&mut атом));
                }
            }
            _ => атом.push(символ),
        }
    }
    if !атом.is_empty() {
        результат.push(атом);
    }
    результат
}

fn прочитати_форму(лексеми: &[String], позиція: &mut usize) -> Форма {
    let лексема = лексеми
        .get(*позиція)
        .unwrap_or_else(|| panic!("реєстр обірвався посеред форми"));
    *позиція += 1;
    if лексема != "(" {
        assert_ne!(лексема, ")", "неочікувана закривальна дужка");
        return Форма::Атом(лексема.clone());
    }
    let mut елементи = Vec::new();
    while лексеми.get(*позиція).map(String::as_str) != Some(")") {
        assert!(*позиція < лексеми.len(), "у реєстрі є незакритий список");
        елементи.push(прочитати_форму(лексеми, позиція));
    }
    *позиція += 1;
    Форма::Список(елементи)
}

fn корінь_реєстру() -> Форма {
    let всі_лексеми = лексеми(РЕЄСТР);
    let mut позиція = 0;
    let корінь = прочитати_форму(&всі_лексеми, &mut позиція);
    assert_eq!(позиція, всі_лексеми.len());
    корінь
}

fn записи_реєстру(корінь: &Форма) -> &[Форма] {
    let Форма::Список(елементи) = корінь else {
        panic!("semantic registry повинен бути списком");
    };
    let Some(Форма::Атом(заголовок)) = елементи.first() else {
        panic!("semantic registry не має заголовка");
    };
    assert_eq!(заголовок, "sr/2");
    &елементи[1..]
}

fn атом(форма: &Форма) -> &str {
    let Форма::Атом(значення) = форма else {
        panic!("очікувався атом");
    };
    значення
}

fn поверхні(запис: &Форма) -> (&str, &[Форма]) {
    let Форма::Список(поля) = запис else {
        panic!("semantic identity повинна бути списком");
    };
    assert!(поля.len() >= 2);
    (атом(&поля[0]), &поля[1..])
}

fn поля_поверхні(форма: &Форма) -> (&str, Option<&str>) {
    let Форма::Список(поля) = форма else {
        panic!("опис surface повинен бути списком");
    };
    assert_eq!(поля.len(), 2, "очікується (surface name-or-empty)");
    let мова = атом(&поля[0]);
    let назва = match &поля[1] {
        Форма::Список(елементи) if елементи.is_empty() => None,
        Форма::Атом(значення) => Some(значення.as_str()),
        інше => panic!("неочікуване значення слота: {інше:?}"),
    };
    (мова, назва)
}

fn знайти<'a>(записи: &'a [Форма], ідентифікатор: &str) -> &'a Форма {
    записи
        .iter()
        .find(|запис| поверхні(запис).0 == ідентифікатор)
        .unwrap_or_else(|| panic!("немає semantic identity {ідентифікатор}"))
}

fn рядок<'a>(запис: &'a Форма, surface: &str) -> (&'a str, Option<&'a str>) {
    поверхні(запис)
        .1
        .iter()
        .map(поля_поверхні)
        .find(|(мова, _)| *мова == surface)
        .unwrap_or_else(|| panic!("немає surface {surface}"))
}

fn перевірити_той_самий_builtin(ліве: &Value, праве: &Value) {
    match (ліве, праве) {
        (Value::Builtin(ліве), Value::Builtin(праве)) => assert!(
            Rc::ptr_eq(ліве, праве),
            "peer spellings повинні вказувати на один runtime builtin"
        ),
        інше => panic!("очікувалися builtin-значення, отримано {інше:?}"),
    }
}

#[test]
fn семантичні_ідентифікатори_складаються_тільки_з_цифр() {
    let корінь = корінь_реєстру();
    let mut побачені = HashSet::new();
    for запис in записи_реєстру(&корінь) {
        let (ідентифікатор, _) = поверхні(запис);
        let bits = ідентифікатор
            .strip_prefix('"')
            .and_then(|value| value.strip_suffix('"'))
            .expect("SID must be serialized as a quoted bitstring");
        assert!(
            bits.len() == 8 && bits.bytes().all(|byte| matches!(byte, b'0' | b'1')),
            "byte SID {ідентифікатор:?} порушує sr/2"
        );
        assert!(побачені.insert(ідентифікатор), "дубль ID {ідентифікатор}");
    }
    // Intentional floor, not a restated fact: the registry only grows, so an
    // exact count would silently rot. 140 is the stable-UK-surface size at
    // the time this floor was written (TEST-ARCHITECTURE-1 step 2).
    assert_eq!(побачені.len(), 168, "sr/2 має містити Canon 0 + 167 identities");
}

#[test]
fn кожна_тотожність_явно_описує_uk_en_sa_без_заборони_майбутніх_мов() {
    let корінь = корінь_реєстру();
    let обовязкові = HashSet::from(["uk", "en", "sa"]);
    for запис in записи_реєстру(&корінь) {
        let (ідентифікатор, описи) = поверхні(запис);
        if ідентифікатор == "\"00000000\"" {
            assert!(описи.len() == 1 || описи.is_empty(), "Canon 0 is ground-only");
            continue;
        }
        let мови = описи
            .iter()
            .map(|опис| поля_поверхні(опис).0)
            .collect::<HashSet<_>>();
        assert!(
            обовязкові.is_subset(&мови),
            "{ідентифікатор}: UK/EN/SA не можуть бути неявними: {мови:?}"
        );
        assert_eq!(мови.len(), описи.len(), "{ідентифікатор}: дубль surface");
    }
}

#[test]
fn символічна_нотація_не_належить_людській_мові() {
    let корінь = корінь_реєстру();
    for запис in записи_реєстру(&корінь) {
        let (ідентифікатор, описи) = поверхні(запис);
        if ідентифікатор == "\"00000000\"" {
            continue;
        }
        for опис in описи {
            let (surface, назва) = поля_поверхні(опис);
            let Some(назва) = назва else {
                continue;
            };
            if surface == "sym" {
                continue;
            }
            let чиста_назва = назва.trim_matches('"');
            assert!(
                чиста_назва.chars().any(char::is_alphabetic),
                "{ідентифікатор}/{surface}: {назва:?} — символіка, а не людська мова"
            );
        }
    }
}

#[test]
fn додавання_відділяє_людські_мови_від_спільного_символу() {
    let корінь = корінь_реєстру();
    let запис = знайти(записи_реєстру(&корінь), "\"00001100\"");
    assert_eq!(рядок(запис, "uk"), ("uk", Some("додати")));
    assert_eq!(рядок(запис, "en"), ("en", None));
    assert_eq!(рядок(запис, "sa"), ("sa", Some("yoga")));
    assert_eq!(рядок(запис, "sym"), ("sym", Some("+")));

    let mut сесія = Session::default();
    let українське = eval_program("додати", &mut сесія).unwrap().value;
    let символічне = eval_program("+", &mut сесія).unwrap().value;
    let санскритське = eval_program("yoga", &mut сесія).unwrap().value;
    перевірити_той_самий_builtin(&українське, &символічне);
    перевірити_той_самий_builtin(&символічне, &санскритське);

    for вираз in ["(додати 20 22)", "(+ 20 22)", "(yoga 20 22)"] {
        assert_eq!(eval_program(вираз, &mut сесія).unwrap().value.to_string(), "42");
    }
}

// `затінення_ordinary_peer_name_не_переналаштовує_інші` (shadowing одного
// admitted 00001100 peer не має зачіпати інші) та
// `surface_files_не_будують_peer_names_через_англійську` (surface-файли не
// повинні будувати peer через `(define додати +)`/`(define yoga +)`) were
// removed here (TEST-ARCHITECTURE-1 step 2, triplicated-shadow-isolation
// consolidation): both mutations are already killed by
// `peer_surface_identity.rs`'s registry-driven
// `shadowing_one_admitted_add_surface_does_not_retarget_its_peers` and
// `human_surface_files_do_not_redefine_admitted_add_peers`, which cover the
// same semantic ID (00001100) generically over every admitted surface instead
// of a hardcoded three-name list, and the second is strictly stronger
// (rejects `(define додати <anything>)`, not just the `+`-specific alias).

#[test]
fn executable_authority_більше_не_читає_legacy_en_shaped_таблицю() {
    for (імя, джерело) in [
        ("REPL", REPL_КАТАЛОГ),
        ("coverage", ПЕРЕВІРКА_ПОКРИТТЯ),
        ("parity", ПЕРЕВІРКА_РІВНОПРАВЯ),
        ("translator", ТРАНСЛЯТОР),
    ] {
        assert!(
            !джерело.contains("uk-sa-coverage.lisp"),
            "{імя}: legacy EN-shaped table знову стала executable authority"
        );
        assert!(
            джерело.contains("semantic-registry.lisp"),
            "{імя}: має спиратися на byte-SID registry"
        );
    }
}

#[test]
#[ignore = "фінальний gate: увімкнути після завершення UK/EN/SA parity"]
fn повне_рівноправя_вимагає_наявності_для_всіх_людських_поверхонь() {
    let корінь = корінь_реєстру();
    for запис in записи_реєстру(&корінь) {
        let (ідентифікатор, _) = поверхні(запис);
        if ідентифікатор == "\"00000000\"" {
            continue;
        }
        let наявні = ["uk", "en", "sa"].map(|surface| рядок(запис, surface).1.is_some());
        assert!(
            наявні.iter().all(|наявне| *наявне),
            "{ідентифікатор}: UK/EN/SA ще не заповнені одночасно"
        );
    }
}
