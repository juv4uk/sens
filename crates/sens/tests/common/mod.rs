//! Спільні test-only ресурси для integration-тестів crate `sens`.

const META_EVAL_SOURCE: &str = include_str!("../../../../lib/meta-eval.lisp");

pub fn load_meta_evaluator_library(
    session: &mut sens::Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    sens::load_meta_evaluator_library_from_source(session, META_EVAL_SOURCE)
}
