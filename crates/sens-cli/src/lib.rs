//! Shared, feature-gated host access to the sterile Zig transport ABI.
//!
//! Keeping this module in the crate library avoids compiling one private
//! copy into every CLI target. All semantics remain owned by `sens`.
//! No fallback path exists when the Zig transport feature is disabled.

#[cfg(feature = "zig-transport")]
pub mod zig_transport;

/// Load the F6 reasoning and filesystem libraries from their committed
/// physical T5M assets. Core4 must already be active in `session`.
#[cfg(feature = "zig-transport")]
pub fn bootstrap_f6_t5m_libraries(session: &mut sens::Session) -> Result<(), String> {
    let mut assets = zig_transport::repl_reasoning_t5m_assets()?;
    assets.push((
        "persistent-map",
        zig_transport::persistent_map_t5m_bytes()?,
    ));
    assets.push(("world", zig_transport::f6_world_t5m_bytes()?));
    assets.push((
        "content-store",
        zig_transport::f6_content_store_t5m_bytes()?,
    ));
    assets.push(("lisp-fs", zig_transport::f6_lisp_fs_t5m_bytes()?));

    for (label, physical) in assets {
        execute_t5m_asset(session, &physical, label)?;
    }
    Ok(())
}

#[cfg(feature = "zig-transport")]
pub fn execute_f6_producer_witness(
    session: &mut sens::Session,
) -> Result<sens::EvalResult, String> {
    let physical = zig_transport::f6_producer_witness_t5m_bytes()?;
    execute_t5m_asset(session, &physical, "F6 producer witness")
}

#[cfg(feature = "zig-transport")]
fn execute_t5m_asset(
    session: &mut sens::Session,
    physical: &[u8],
    label: &str,
) -> Result<sens::EvalResult, String> {
    let words = zig_transport::decode_t5m_exact_words(physical)?
        .into_iter()
        .map(|word| {
            sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits)
                .map_err(|error| format!("{label} exact SENS word: {error}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let program = sens::PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|error| format!("{label} SENS binary reader: {}", error.message))?;
    program
        .execute(session)
        .map_err(|error| format!("{label} SENS binary evaluator: {}", error.message))
}

#[cfg(not(feature = "zig-transport"))]
pub fn bootstrap_f6_t5m_libraries(_session: &mut sens::Session) -> Result<(), String> {
    Err("RUST_ZIG_ONLY: F6 libraries require physical T5M through Zig".into())
}

#[cfg(not(feature = "zig-transport"))]
pub fn execute_f6_producer_witness(
    _session: &mut sens::Session,
) -> Result<sens::EvalResult, String> {
    Err("RUST_ZIG_ONLY: F6 producer witness requires physical T5M through Zig".into())
}
