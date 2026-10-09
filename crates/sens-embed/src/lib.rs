//! Stateful C ABI embedding boundary for the canonical sens evaluator.
//!
//! This crate is deliberately a transport boundary only.  Parsing, bootstrap,
//! evaluation, output, error rendering, and session state all come from
//! `sens`; no second evaluator lives here.

use sens::{
    eval_parsed_expressions_incremental, load_core_library, parse, Environment, Session,
};
use std::{
    ffi::{CStr, CString},
    os::raw::{c_char, c_void},
    panic::{catch_unwind, AssertUnwindSafe},
    ptr,
};

/// C ABI contract version.  Hosts must compare this value before using the
/// session exports, rather than treating matching symbol names as proof of
/// compatibility.
pub const MY_LISP_EMBED_ABI_VERSION: u32 = 4;

/// Result tags that a nullary or typed-unary host mechanism may return
/// through the C ABI.
pub const MY_LISP_EMBED_NIL: u32 = 0;
pub const MY_LISP_EMBED_TRUE: u32 = 1;

/// One atomic host mechanism. It must only observe or perform the requested
/// action; the caller's Lisp program keeps all policy and orchestration.
pub type MyLispEmbedNullaryFn = unsafe extern "C" fn(*mut c_void, *mut u32) -> i32;

/// One atomic host mechanism that takes exactly one opaque host-handle
/// argument of a fixed, registration-time `kind`. `token` is the handle's
/// bound `u64` (the same value passed to `my_lisp_embed_bind_host_handle`);
/// the mechanism never receives a raw handle any other Lisp value could
/// have produced, since `kind` is checked before this callback runs.
///
/// v1 keeps the result space identical to the nullary mechanism's
/// (nil/true only, via `out_result`) rather than also allowing a typed
/// unary mechanism to hand back a fresh opaque handle -- ABI#181 left that
/// open as a later increment; nothing here forecloses adding it once a
/// concrete downstream need exists.
pub type MyLispEmbedUnaryFn = unsafe extern "C" fn(*mut c_void, u64, *mut u32) -> i32;

/// Opaque owner of one canonical, persistent sens session.
pub struct MyLispEmbedSession {
    session: Session,
}

fn new_session() -> Result<MyLispEmbedSession, String> {
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core_library(&mut session).map_err(|error| error.render(sens::CORE_LIBRARY_SOURCE))?;
    Ok(MyLispEmbedSession { session })
}

fn response_for(session: &mut MyLispEmbedSession, source: &str) -> String {
    match parse(source) {
        Ok(expressions) => {
            match eval_parsed_expressions_incremental(&expressions, &mut session.session) {
                Ok(result) => {
                    let mut response = result.output.join("\n");
                    if !response.is_empty() {
                        response.push('\n');
                    }
                    response.push_str(&result.value.to_string());
                    response
                }
                Err(error) => format!("error: {}", error.render(source)),
            }
        }
        Err(error) => format!("error: {}", error.render(source)),
    }
}

fn into_c_string(response: String) -> *mut c_char {
    CString::new(response)
        .unwrap_or_else(|_| {
            CString::new("error: result contains a NUL byte").expect("static C string")
        })
        .into_raw()
}

fn invoke_nullary(
    callback: MyLispEmbedNullaryFn,
    context: *mut c_void,
    surface: &str,
    arguments: &[sens::Value],
    span: sens::Span,
) -> Result<sens::Value, sens::LanguageError> {
    if !arguments.is_empty() {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface} expects exactly 0 arguments"),
            span,
        ));
    }
    let mut raw_result = MY_LISP_EMBED_NIL;
    let status = unsafe { callback(context, &mut raw_result) };
    if status != 0 {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface}: host mechanism failed with status {status}"),
            span,
        ));
    }
    match raw_result {
        MY_LISP_EMBED_NIL => Ok(sens::Value::Nil),
        MY_LISP_EMBED_TRUE => Ok(sens::Value::predicate_bit(true)),
        _ => Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface}: host returned an unknown result tag {raw_result}"),
            span,
        )),
    }
}

fn invoke_unary(
    callback: MyLispEmbedUnaryFn,
    context: *mut c_void,
    expected_kind: &str,
    surface: &str,
    arguments: &[sens::Value],
    span: sens::Span,
) -> Result<sens::Value, sens::LanguageError> {
    let [argument] = arguments else {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!(
                "{surface} expects exactly 1 argument, an opaque {expected_kind} handle"
            ),
            span,
        ));
    };
    let Some((actual_kind, token)) = argument.as_host_handle() else {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface} expects an opaque {expected_kind} handle, not {argument}"),
            span,
        ));
    };
    if actual_kind != expected_kind {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!(
                "{surface} expects a {expected_kind} handle, but received a {actual_kind} handle"
            ),
            span,
        ));
    }

    let mut raw_result = MY_LISP_EMBED_NIL;
    let status = unsafe { callback(context, token, &mut raw_result) };
    if status != 0 {
        return Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface}: host mechanism failed with status {status}"),
            span,
        ));
    }
    match raw_result {
        MY_LISP_EMBED_NIL => Ok(sens::Value::Nil),
        MY_LISP_EMBED_TRUE => Ok(sens::Value::predicate_bit(true)),
        _ => Err(sens::LanguageError::new(
            sens::ErrorKind::InvalidForm,
            format!("{surface}: host returned an unknown result tag {raw_result}"),
            span,
        )),
    }
}

/// Returns the version of the C embedding contract implemented by this DLL.
#[no_mangle]
pub extern "C" fn my_lisp_embed_abi_version() -> u32 {
    MY_LISP_EMBED_ABI_VERSION
}

/// Binds an embedding-owned opaque handle. Lisp may pass this value to a host
/// mechanism, but source syntax cannot construct or inspect its token.
///
/// # Safety
///
/// `session` must be null or a live pointer returned by `my_lisp_embed_session_new`.
/// `surface` and `kind` must be null or valid NUL-terminated strings for this call.
/// Calls using one session must remain on its owning host thread.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_bind_host_handle(
    session: *mut MyLispEmbedSession,
    surface: *const c_char,
    kind: *const c_char,
    token: u64,
) -> i32 {
    if session.is_null() || surface.is_null() || kind.is_null() {
        return -1;
    }
    let decode = |text: *const c_char| {
        CStr::from_ptr(text)
            .to_str()
            .ok()
            .filter(|text| !text.is_empty())
            .map(str::to_owned)
    };
    let (Some(surface), Some(kind)) = (decode(surface), decode(kind)) else {
        return -2;
    };
    (&mut *session)
        .session
        .environment
        .define(surface, sens::Value::host_handle(kind, token));
    0
}

/// Binds a zero-argument host mechanism into one canonical session.
///
/// Returns zero on success. Negative results indicate an invalid session,
/// surface, or callback. A non-zero result from the host callback becomes a
/// Lisp error for that evaluation and leaves the session usable.
///
/// # Safety
///
/// `session` must be null or a live pointer returned by `my_lisp_embed_session_new`.
/// `surface` must be null or a valid NUL-terminated string for this call. When
/// present, `callback` and `context` must remain valid for later invocations from
/// this session. Calls using one session must remain on its owning host thread.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_register_nullary(
    session: *mut MyLispEmbedSession,
    surface: *const c_char,
    callback: Option<MyLispEmbedNullaryFn>,
    context: *mut c_void,
) -> i32 {
    if session.is_null() || surface.is_null() || callback.is_none() {
        return -1;
    }
    let surface = match CStr::from_ptr(surface).to_str() {
        Ok(surface) if !surface.is_empty() => surface.to_owned(),
        _ => return -2,
    };
    let callback = callback.expect("validated above");
    let diagnostic_surface = surface.clone();
    let function = std::rc::Rc::new(
        move |arguments: &[sens::Value], _environment: &sens::Environment, span| {
            invoke_nullary(callback, context, &diagnostic_surface, arguments, span)
        },
    );
    (&mut *session)
        .session
        .environment
        .define(surface, sens::Value::host_function(function));
    0
}

/// Binds a one-argument host mechanism into one canonical session. The
/// mechanism's single argument must be an opaque host handle bound via
/// `my_lisp_embed_bind_host_handle` whose `kind` matches `kind` exactly;
/// any other value (wrong kind, or not a handle at all) becomes an
/// ordinary Lisp-catchable error, not a host-side abort.
///
/// Returns zero on success. Negative results indicate an invalid session,
/// surface, kind, or callback. A non-zero result from the host callback
/// becomes a Lisp error for that evaluation and leaves the session usable.
///
/// # Safety
///
/// `session` must be null or a live pointer returned by `my_lisp_embed_session_new`.
/// `surface` and `kind` must be null or valid NUL-terminated strings for this call.
/// When present, `callback` and `context` must remain valid for later invocations
/// from this session. Calls using one session must remain on its owning host thread.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_register_unary(
    session: *mut MyLispEmbedSession,
    surface: *const c_char,
    kind: *const c_char,
    callback: Option<MyLispEmbedUnaryFn>,
    context: *mut c_void,
) -> i32 {
    if session.is_null() || surface.is_null() || kind.is_null() || callback.is_none() {
        return -1;
    }
    let decode = |text: *const c_char| {
        CStr::from_ptr(text)
            .to_str()
            .ok()
            .filter(|text| !text.is_empty())
            .map(str::to_owned)
    };
    let (Some(surface), Some(kind)) = (decode(surface), decode(kind)) else {
        return -2;
    };
    let callback = callback.expect("validated above");
    let diagnostic_surface = surface.clone();
    let function = std::rc::Rc::new(
        move |arguments: &[sens::Value], _environment: &sens::Environment, span| {
            invoke_unary(callback, context, &kind, &diagnostic_surface, arguments, span)
        },
    );
    (&mut *session)
        .session
        .environment
        .define(surface, sens::Value::host_function(function));
    0
}

/// Creates a persistent canonical sens session with the ordinary core
/// library loaded.  Returns null only if bootstrap unexpectedly panics.
#[no_mangle]
pub extern "C" fn my_lisp_embed_session_new() -> *mut MyLispEmbedSession {
    catch_unwind(AssertUnwindSafe(new_session))
        .ok()
        .and_then(Result::ok)
        .map(Box::new)
        .map(Box::into_raw)
        .unwrap_or(ptr::null_mut())
}

/// Evaluates UTF-8 source against this session and returns caller-owned UTF-8
/// text.  The returned pointer must be freed with `my_lisp_embed_free_string`.
/// Null source or a null session return null.
///
/// # Safety
///
/// `session` must be null or a live pointer returned by `my_lisp_embed_session_new`.
/// `source` must be null or a valid NUL-terminated byte sequence for this call.
/// Calls using one session must remain on its owning host thread.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_eval(
    session: *mut MyLispEmbedSession,
    source: *const c_char,
) -> *mut c_char {
    if session.is_null() || source.is_null() {
        return ptr::null_mut();
    }

    let source = match CStr::from_ptr(source).to_str() {
        Ok(source) => source,
        Err(_) => return into_c_string("error: source is not valid UTF-8".to_owned()),
    };

    catch_unwind(AssertUnwindSafe(|| response_for(&mut *session, source)))
        .map(into_c_string)
        .unwrap_or_else(|_| into_c_string("error: canonical session panicked".to_owned()))
}

/// Frees a string returned by `my_lisp_embed_eval`.  A null pointer is a no-op.
///
/// # Safety
///
/// `value` must be null or a pointer returned by `my_lisp_embed_eval` that has
/// not already been freed; it must not come from another allocator or API.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_free_string(value: *mut c_char) {
    if !value.is_null() {
        drop(CString::from_raw(value));
    }
}

/// Frees a session returned by `my_lisp_embed_session_new`.  A null pointer is
/// a no-op.  All calls for a session must remain on its owning host thread.
///
/// # Safety
///
/// `session` must be null or a live pointer returned by `my_lisp_embed_session_new`
/// that has not already been freed; it must not come from another allocator or API.
#[no_mangle]
pub unsafe extern "C" fn my_lisp_embed_session_free(session: *mut MyLispEmbedSession) {
    if !session.is_null() {
        drop(Box::from_raw(session));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static NULLARY_CALLS: AtomicUsize = AtomicUsize::new(0);

    unsafe extern "C" fn true_fact(_context: *mut c_void, out_result: *mut u32) -> i32 {
        NULLARY_CALLS.fetch_add(1, Ordering::SeqCst);
        *out_result = MY_LISP_EMBED_TRUE;
        0
    }

    fn eval(session: *mut MyLispEmbedSession, source: &str) -> String {
        let source = CString::new(source).unwrap();
        let raw_result = unsafe { my_lisp_embed_eval(session, source.as_ptr()) };
        assert!(!raw_result.is_null());
        let result = unsafe { CStr::from_ptr(raw_result) }
            .to_str()
            .unwrap()
            .to_owned();
        unsafe { my_lisp_embed_free_string(raw_result) };
        result
    }

    #[test]
    fn reports_the_documented_abi_version() {
        assert_eq!(my_lisp_embed_abi_version(), MY_LISP_EMBED_ABI_VERSION);
        assert_eq!(MY_LISP_EMBED_ABI_VERSION, 4);
    }

    #[test]
    fn nullary_host_mechanism_returns_canonical_truth_to_lisp() {
        NULLARY_CALLS.store(0, Ordering::SeqCst);
        let session = my_lisp_embed_session_new();
        assert_eq!(
            unsafe {
                my_lisp_embed_register_nullary(
                    session,
                    CString::new("гравець-присутній?").unwrap().as_ptr(),
                    Some(true_fact),
                    ptr::null_mut(),
                )
            },
            0
        );

        assert_eq!(eval(session, "(гравець-присутній?)"), "t");
        assert_eq!(NULLARY_CALLS.load(Ordering::SeqCst), 1);
        assert!(eval(session, "(гравець-присутній? 1)").starts_with("error: "));
        assert_eq!(eval(session, "(гравець-присутній?)"), "t");
        assert_eq!(NULLARY_CALLS.load(Ordering::SeqCst), 2);

        unsafe { my_lisp_embed_session_free(session) };
    }

    static UNARY_CALLS: AtomicUsize = AtomicUsize::new(0);
    static LAST_UNARY_TOKEN: AtomicUsize = AtomicUsize::new(0);

    unsafe extern "C" fn player_present_fact(
        _context: *mut c_void,
        token: u64,
        out_result: *mut u32,
    ) -> i32 {
        UNARY_CALLS.fetch_add(1, Ordering::SeqCst);
        LAST_UNARY_TOKEN.store(token as usize, Ordering::SeqCst);
        *out_result = MY_LISP_EMBED_TRUE;
        0
    }

    #[test]
    fn typed_unary_host_mechanism_receives_matching_handle_token_and_returns_canonical_truth() {
        UNARY_CALLS.store(0, Ordering::SeqCst);
        let session = my_lisp_embed_session_new();
        assert_eq!(
            unsafe {
                my_lisp_embed_bind_host_handle(
                    session,
                    CString::new("гравець").unwrap().as_ptr(),
                    CString::new("player").unwrap().as_ptr(),
                    777,
                )
            },
            0
        );
        assert_eq!(
            unsafe {
                my_lisp_embed_register_unary(
                    session,
                    CString::new("гравець-живий?").unwrap().as_ptr(),
                    CString::new("player").unwrap().as_ptr(),
                    Some(player_present_fact),
                    ptr::null_mut(),
                )
            },
            0
        );

        assert_eq!(eval(session, "(гравець-живий? гравець)"), "t");
        assert_eq!(UNARY_CALLS.load(Ordering::SeqCst), 1);
        assert_eq!(LAST_UNARY_TOKEN.load(Ordering::SeqCst), 777);

        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn typed_unary_host_mechanism_rejects_wrong_kind_handle_as_lisp_error() {
        let session = my_lisp_embed_session_new();
        unsafe {
            my_lisp_embed_bind_host_handle(
                session,
                CString::new("зброя").unwrap().as_ptr(),
                CString::new("weapon").unwrap().as_ptr(),
                1,
            );
            my_lisp_embed_register_unary(
                session,
                CString::new("гравець-живий?").unwrap().as_ptr(),
                CString::new("player").unwrap().as_ptr(),
                Some(player_present_fact),
                ptr::null_mut(),
            );
        }

        let outcome = eval(session, "(гравець-живий? зброя)");
        assert!(outcome.starts_with("error: "), "got: {outcome}");
        assert!(outcome.contains("player") && outcome.contains("weapon"), "got: {outcome}");

        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn typed_unary_host_mechanism_rejects_non_handle_argument_and_wrong_arity() {
        let session = my_lisp_embed_session_new();
        unsafe {
            my_lisp_embed_register_unary(
                session,
                CString::new("гравець-живий?").unwrap().as_ptr(),
                CString::new("player").unwrap().as_ptr(),
                Some(player_present_fact),
                ptr::null_mut(),
            );
        }

        assert!(eval(session, "(гравець-живий? 42)").starts_with("error: "));
        assert!(eval(session, "(гравець-живий?)").starts_with("error: "));
        assert!(eval(session, "(гравець-живий? 1 2)").starts_with("error: "));

        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn host_handle_binding_is_opaque_to_lisp_source() {
        let session = my_lisp_embed_session_new();
        assert_eq!(
            unsafe {
                my_lisp_embed_bind_host_handle(
                    session,
                    CString::new("гравець").unwrap().as_ptr(),
                    CString::new("cyberpunk.IScriptable").unwrap().as_ptr(),
                    42,
                )
            },
            0
        );
        assert_eq!(
            eval(session, "гравець"),
            "#<host-handle cyberpunk.IScriptable>"
        );
        assert!(!eval(session, "гравець").contains("42"));
        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn ukrainian_definition_persists_in_one_canonical_session() {
        let session = my_lisp_embed_session_new();
        assert!(!session.is_null());

        assert_eq!(eval(session, "(визначити repl-перевірка 42)"), "42");
        assert_eq!(eval(session, "repl-перевірка"), "42");

        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn ukrainian_closure_persists_in_one_canonical_session() {
        let session = my_lisp_embed_session_new();
        assert!(!session.is_null());

        let definition = eval(
            session,
            "(визначити подвоїти (функція (значення) (+ значення значення)))",
        );
        assert_eq!(definition, "<lambda>");
        assert_eq!(eval(session, "(подвоїти 21)"), "42");

        unsafe { my_lisp_embed_session_free(session) };
    }

    #[test]
    fn language_errors_return_text_without_destroying_the_session() {
        let session = my_lisp_embed_session_new();
        assert!(!session.is_null());

        assert!(eval(session, "(car 7)").starts_with("error: "));
        assert_eq!(eval(session, "(+ 20 22)"), "42");

        unsafe { my_lisp_embed_session_free(session) };
    }
}
