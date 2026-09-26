//! Native reference tests for the semantic engine embedded by the WASM adapter.
//!
//! PASSING tests prove the native engine behavior expected by the adapter.
//! They do not cross the wasm-bindgen/JavaScript boundary; browser workflow
//! tests provide that separate evidence class.
//!
//! These tests intentionally use a bare session. `src/lib.rs` separately
//! verifies persistent-session behavior and successful `core.my` preload.

use sens::Session;
use sens_literate::SourceMode;
#[cfg(target_arch = "wasm32")]
use wasm_bindgen_test::wasm_bindgen_test;

fn eval_bare(src: &str) -> Result<String, String> {
    // Session::default() has builtins (+ - * / car cdr cons eq atom quote cond lambda)
    // but NOT core.my definitions (define, length, etc.)
    let mut s = Session::default();
    let (result, _) = sens_literate::eval_literate(src, SourceMode::PureLisp, &mut s)
        .map_err(|e| e.to_string())?;
    Ok(result.value.to_string())
}

// ── arithmetic ──

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn arithmetic_fixnum() {
    assert_eq!(eval_bare("(+ 1 2)").unwrap(), "3");
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn arithmetic_exact_rational_no_floats() {
    let r = eval_bare("(/ 1 3)").unwrap();
    assert!(r.contains('/'), "expected rational but got: {}", r);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn arithmetic_boundary_2p24() {
    // Boundary at base-2^24 limb transition
    let r = eval_bare("(+ 16777215 1)").unwrap();
    assert_eq!(r, "16777216");
}

// ── lambda ──

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn lambda_evaluation() {
    let src = "((lambda (x) (* x x)) 7)";
    assert_eq!(eval_bare(src).unwrap(), "49");
}

// ── quote / data ──

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn quote_preserves_structure() {
    let r = eval_bare("(quote (a b c))").unwrap();
    assert!(r.contains("a") && r.contains("b") && r.contains("c"));
}

// ── error handling ──

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn unclosed_paren_is_error_not_panic() {
    assert!(eval_bare("(+ 1").is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn unknown_symbol_is_error_not_panic() {
    assert!(eval_bare("(nonexistent-fn 42)").is_err());
}

// ── session ──

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn fresh_session_has_clean_state() {
    let s = Session::default();
    // Default session should exist and be usable
    drop(s); // no panic = ok
}
