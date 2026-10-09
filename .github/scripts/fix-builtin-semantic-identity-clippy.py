from pathlib import Path

path = Path("crates/my-lisp/src/value.rs")
text = path.read_text()

old = '''pub struct Builtin {
    pub name: &'static str,
    semantic_id: Option<&'static str>,
    #[allow(clippy::type_complexity)]
    pub func: std::rc::Rc<
        dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
    >,
}
'''
new = '''pub type BuiltinFunction = dyn Fn(
    &[Value],
    &crate::Environment,
    crate::Span,
) -> Result<Value, crate::LanguageError>;

pub struct Builtin {
    pub name: &'static str,
    semantic_id: Option<&'static str>,
    pub func: std::rc::Rc<BuiltinFunction>,
}
'''
if new not in text:
    if old not in text:
        raise SystemExit("Builtin struct anchor missing")
    text = text.replace(old, new, 1)

old = '''    pub(crate) fn local(
        name: &'static str,
        func: std::rc::Rc<
            dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
        >,
    ) -> Self {
'''
new = '''    pub(crate) fn local(name: &'static str, func: std::rc::Rc<BuiltinFunction>) -> Self {
'''
if new not in text:
    if old not in text:
        raise SystemExit("Builtin::local anchor missing")
    text = text.replace(old, new, 1)

old = '''    pub(crate) fn semantic(
        name: &'static str,
        semantic_id: &'static str,
        func: std::rc::Rc<
            dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
        >,
    ) -> Self {
'''
new = '''    pub(crate) fn semantic(
        name: &'static str,
        semantic_id: &'static str,
        func: std::rc::Rc<BuiltinFunction>,
    ) -> Self {
'''
if new not in text:
    if old not in text:
        raise SystemExit("Builtin::semantic anchor missing")
    text = text.replace(old, new, 1)

old = '''    fn function() -> std::rc::Rc<
        dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>,
    > {
'''
new = '''    fn function() -> std::rc::Rc<BuiltinFunction> {
'''
if new not in text:
    if old not in text:
        raise SystemExit("test function anchor missing")
    text = text.replace(old, new, 1)

path.write_text(text)
