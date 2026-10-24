//! Диференційний свідок поверхневої паритетності.
//!
//! Принцип мови: «одна семантична реалізація, кілька людських проєкцій».
//! Поверхня може змінювати ІМЕНА та ПОДАННЯ — і не може змінювати ЗНАЧЕННЯ.
//!
//! Першопричина: `src/lib.rs:258-261` — єдине місце, де `state.surface`
//! змінює ШЛЯХ обчислення: українські поверхні проходять
//! `project_ukr_decimal_integer_literals`, а `core`/`en`/`sa` — ні. Рушій же
//! розрізняє точнодоменне значення (`BinaryNumber`) і гостьове число
//! (`Number`), тож та сама програма може дати різний результат.
//!
//! Ці тести потребують wasm-середовища (публічний API повертає JsValue):
//!   wasm-pack test --headless --chrome crates/sens-wasm

#![cfg(target_arch = "wasm32")]

use wasm_bindgen::JsValue;
use wasm_bindgen_test::wasm_bindgen_test;

fn value_of(surface: &str, source: &str) -> String {
    sens_wasm::reset_session();
    sens_wasm::set_surface(surface).expect("surface accepted");
    let result = sens_wasm::evaluate(source, JsValue::NULL).expect("evaluation");
    js_sys::Reflect::get(&result, &JsValue::from_str("value"))
        .expect("value field")
        .as_string()
        .expect("string value")
}

/// ІНВАРІАНТ, який мусить триматися: програма в ТОЧНОДОМЕННІЙ формі
/// (лише бітові носії) дає те саме значення на кожній поверхні.
#[wasm_bindgen_test]
fn exact_domain_program_is_surface_invariant() {
    let source = "(тотожне? #d3:100 #d3:100)";
    let baseline = value_of("core", source);
    for surface in ["en", "ук", "укр", "sa"] {
        assert_eq!(
            value_of(surface, source),
            baseline,
            "exact-domain program must be surface-invariant, diverged on {surface}"
        );
    }
}

/// ВІДОМА РОЗБІЖНІСТЬ — задокументована, не прихована.
///
/// `(число? 5)` на ук/укр дає #t (літерал спроєктовано в точнодоменне D24+),
/// а на core/en/sa — #f (літерал лишається гостьовим числом). Це різниця в
/// ОБЧИСЛЕНОМУ ЗНАЧЕННІ, а не в поданні.
///
/// Тест позначено `ignore` навмисно: виправлення змінює семантику
/// (lib.rs:258 — прибрати умову поверхні й проєктувати завжди, як роблять
/// `eval_program` і `eval_literate_ukr`), а важливі зміни семантичних законів
/// — рішення власника. Запуск: `--include-ignored`.
#[wasm_bindgen_test]
#[ignore = "known surface-value divergence at src/lib.rs:258; owner decision required"]
fn decimal_literal_kind_diverges_across_surfaces() {
    let ukrainian = value_of("укр", "(число? 5)");
    let canonical = value_of("core", "(число? 5)");
    assert_ne!(
        ukrainian, canonical,
        "if this now passes, the divergence was fixed — remove the ignore"
    );
}
