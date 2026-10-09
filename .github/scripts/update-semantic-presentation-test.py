from pathlib import Path

p = Path("crates/my-lisp/src/presentation.rs")
text = p.read_text()
old = '''    #[test]
    fn ukrainian_presentation_localizes_builtin_and_function_markers() {
        let mut session = Session::default();
        let builtin = eval_program("atom", &mut session)
            .expect("atom value")
            .value;
        assert_eq!(
            render_value_for_presentation(&builtin, PresentationLanguage::Ukrainian),
            "#<вбудована атом?>"
        );
'''
new = '''    #[test]
    fn ukrainian_presentation_localizes_semantic_and_function_markers() {
        let mut session = Session::default();
        let semantic = eval_program("atom", &mut session)
            .expect("atom semantic value")
            .value;
        assert_eq!(
            render_value_for_presentation(&semantic, PresentationLanguage::Ukrainian),
            "#<семантична-операція 0002>"
        );
'''
if new not in text:
    if old not in text:
        raise SystemExit("presentation test anchor changed unexpectedly")
    p.write_text(text.replace(old, new, 1))
