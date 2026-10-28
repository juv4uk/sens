use sens::syntax::Expr;
use sens::{parse, ExprKind};
use std::collections::HashMap;
use std::sync::OnceLock;

const HUMAN_SURFACES: [&str; 4] = ["ук", "укр", "en", "san"];
const FIXED_SURFACES: [&str; 6] = ["ук", "укр", "san", "en", "LISP", "sym"];

#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceName {
    surface: String,
    name: Option<String>,
    symbolic_name: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceEntry {
    identity: String,
    names: Vec<SurfaceName>,
}

#[cfg(test)]
#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceDoc {
    category: String,
    identity: String,
    kind: String,
    call: String,
    description: String,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct Counts {
    present: usize,
    empty: usize,
}

impl Counts {
    fn add(&mut self, present: bool) {
        if present {
            self.present += 1;
        } else {
            self.empty += 1;
        }
    }
}

fn normalize_surface(surface: &str) -> &str {
    match surface {
        "sa" => "san",
        _ => surface,
    }
}

// The REPL is the human-projection exception: Rust reads these Lisp tables
// only to render/resolve UI names; they do not enter the binary backend.
// A table is an immutable, build-embedded projection. Parsing all eleven
// tables on every invoked head makes large executable .lisp programs needlessly slow.
static SURFACE_ENTRIES: OnceLock<Result<Vec<SurfaceEntry>, String>> = OnceLock::new();

fn registry_entries() -> Result<&'static [SurfaceEntry], String> {
    SURFACE_ENTRIES
        .get_or_init(load_registry_entries)
        .as_ref()
        .map(Vec::as_slice)
        .map_err(Clone::clone)
}

fn load_registry_entries() -> Result<Vec<SurfaceEntry>, String> {
    let mut entries = Vec::new();
    for width in 1u8..=11 {
        let source = domain_table_source(width)
            .map_err(|error| format!("D{width}: не вдалося отримати таблицю проєкцій: {error}"))?;
        let forms = parse(&source).map_err(|error| {
            format!(
                "не вдалося розібрати таблицю D{width}: {}",
                error.render(&source)
            )
        })?;
        let root = forms
            .first()
            .and_then(expr_list)
            .ok_or_else(|| format!("D{width}: очікувався корінь domain-table-1"))?;
        if root.first().and_then(expr_symbol) != Some("domain-table-1") {
            return Err(format!("D{width}: невідомий формат таблиці"));
        }
        for row in root.iter().skip(1) {
            let row_fields = expr_list(row)
                .ok_or_else(|| format!("D{width}: рядок таблиці має бути списком"))?;
            let key = row_fields
                .first()
                .ok_or_else(|| format!("D{width}: порожній рядок"))?;
            let bits = source
                .get(key.span.start..key.span.end)
                .ok_or_else(|| format!("D{width}: некоректний діапазон ключа"))?;
            if bits.len() != usize::from(width)
                || !bits.bytes().all(|bit| matches!(bit, b'0' | b'1'))
            {
                return Err(format!(
                    "D{width}: ключ {bits:?} не має точної ширини домену"
                ));
            }
            let mut names = FIXED_SURFACES
                .iter()
                .map(|surface| SurfaceName {
                    surface: (*surface).to_string(),
                    name: None,
                    symbolic_name: false,
                })
                .collect::<Vec<_>>();
            for field in row_fields.iter().skip(1) {
                let parts = expr_list(field)
                    .ok_or_else(|| format!("D{width}:{bits}: проєкція має бути списком"))?;
                if parts.len() != 2 {
                    return Err(format!("D{width}:{bits}: очікував пару назва/значення"));
                }
                let surface = expr_symbol(&parts[0])
                    .ok_or_else(|| format!("D{width}:{bits}: назва проєкції має бути символом"))?;
                let slot = names
                    .iter_mut()
                    .find(|slot| slot.surface == surface)
                    .ok_or_else(|| format!("D{width}:{bits}: невідома проєкція {surface}"))?;
                slot.name = projection_value(&parts[1]).map(str::to_string);
                slot.symbolic_name = matches!(&parts[1].kind, ExprKind::Symbol(_));
            }
            entries.push(SurfaceEntry {
                identity: format!("D{width}:{bits}"),
                names,
            });
        }
    }

    if entries.is_empty() {
        return Err("D1–D11 таблиці не містять жодної координати".to_string());
    }
    Ok(entries)
}

fn domain_table_source(width: u8) -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = crate::zig_transport::domain_table_source_bytes(width)?;
        String::from_utf8(bytes)
            .map_err(|error| format!("ZIG_DOMAIN_TABLE_CARRIER invalid UTF-8: {error}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err(format!(
            "RUST_ZIG_ONLY: domain table D{width} requires Zig; no Rust source fallback"
        ))
    }
}

fn projection_value(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(value) | ExprKind::String(value) => Some(value.as_ref()),
        ExprKind::List(items) if items.is_empty() => None,
        _ => None,
    }
}

fn surface_name<'a>(entry: &'a SurfaceEntry, surface: &str) -> Option<&'a SurfaceName> {
    let surface = normalize_surface(surface);
    entry.names.iter().find(|name| name.surface == surface)
}

fn counts_for(entries: &[SurfaceEntry], surface: &str) -> Counts {
    let mut counts = Counts::default();
    for entry in entries {
        let present = surface_name(entry, surface)
            .and_then(|name| name.name.as_deref())
            .is_some();
        counts.add(present);
    }
    counts
}

fn public_denominator(entries: &[SurfaceEntry]) -> usize {
    entries.len()
}

fn find_entries<'a>(entries: &'a [SurfaceEntry], requested: &str) -> Vec<&'a SurfaceEntry> {
    entries
        .iter()
        .filter(|entry| {
            entry.identity == requested
                || entry
                    .names
                    .iter()
                    .any(|surface| surface.name.as_deref() == Some(requested))
        })
        .collect()
}

// Repeated lookups during a real T5M mint must be constant-time even for large
// Lisp libraries; every entry remains owned by the exact Dn coordinate.
type SurfaceIndex = HashMap<(String, String), Option<String>>;

static SURFACE_INDEX: OnceLock<Result<SurfaceIndex, String>> = OnceLock::new();
static UKR_INDEX: OnceLock<Result<HashMap<String, String>, String>> = OnceLock::new();

fn surface_index() -> Result<&'static SurfaceIndex, String> {
    SURFACE_INDEX
        .get_or_init(|| {
            let mut index = HashMap::new();
            for entry in registry_entries()? {
                for name in &entry.names {
                    if let Some(spelling) = name.name.as_ref() {
                        let key = (name.surface.clone(), spelling.clone());
                        // Keep ambiguous names uncallable; do not assign arbitrary
                        // priority to one of two distinct exact domains.
                        match index.entry(key) {
                            std::collections::hash_map::Entry::Vacant(slot) => {
                                slot.insert(Some(entry.identity.clone()));
                            }
                            std::collections::hash_map::Entry::Occupied(mut slot) => {
                                *slot.get_mut() = None;
                            }
                        }
                    }
                }
            }
            Ok(index)
        })
        .as_ref()
        .map_err(Clone::clone)
}

fn ukr_index() -> Result<&'static HashMap<String, String>, String> {
    UKR_INDEX
        .get_or_init(|| {
            let mut index = HashMap::new();
            for entry in registry_entries()? {
                if let Some(name) = surface_name(entry, "укр").and_then(|name| name.name.as_ref())
                {
                    index.insert(entry.identity.clone(), name.clone());
                }
            }
            Ok(index)
        })
        .as_ref()
        .map_err(Clone::clone)
}

/// Resolve a spelling only in the selected projection column. Ambiguous names
/// fail closed; the returned coordinate is still only a table projection, not
/// proof that the resident is callable.
pub(super) fn identity_for_surface_name(
    surface: &str,
    requested: &str,
) -> Result<Option<String>, String> {
    let key = (normalize_surface(surface).to_owned(), requested.to_owned());
    Ok(surface_index()?.get(&key).cloned().flatten())
}

/// Return every exact identity whose `sym` column contains an unquoted
/// symbolic alias. Quoted strings in that column describe text glyphs; they
/// must not become callable surface names. Callability filtering belongs to
/// the REPL admission boundary.
pub(super) fn identities_for_surface_name(
    surface: &str,
    requested: &str,
) -> Result<Vec<String>, String> {
    let surface = normalize_surface(surface);
    Ok(registry_entries()?
        .iter()
        .filter(|entry| {
            surface_name(entry, surface).is_some_and(|name| {
                name.symbolic_name && name.name.as_deref() == Some(requested)
            })
        })
        .map(|entry| entry.identity.clone())
        .collect())
}

/// Return the full Ukrainian spelling paired with one exact table identity.
pub(super) fn ukr_name_for_identity(identity: &str) -> Result<Option<String>, String> {
    Ok(ukr_index()?.get(identity).cloned())
}

/// Return one exact projection spelling for a known table identity.
pub(super) fn name_for_identity(surface: &str, identity: &str) -> Result<Option<String>, String> {
    Ok(registry_entries()?
        .iter()
        .find(|entry| entry.identity == identity)
        .and_then(|entry| surface_name(entry, surface))
        .and_then(|name| name.name.clone()))
}

fn rendered_name(surface: Option<&SurfaceName>) -> String {
    surface
        .and_then(|surface| surface.name.as_deref())
        .unwrap_or("()")
        .to_string()
}

fn expr_list(expr: &Expr) -> Option<&[Expr]> {
    match &expr.kind {
        ExprKind::List(items) => Some(items.as_ref()),
        _ => None,
    }
}

fn expr_symbol(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(symbol) => Some(symbol.as_ref()),
        _ => None,
    }
}

#[cfg(test)]
fn expr_string(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::String(text) => Some(text.as_ref()),
        _ => None,
    }
}

/// Documentation key is an exact D1..D10 domain coordinate, not legacy SID8.
#[cfg(test)]
fn expr_documentation_key(expr: &Expr) -> Option<String> {
    let symbol = expr_symbol(expr)?;
    let (domain, bits) = symbol.split_once(':')?;
    let width = domain.strip_prefix('D')?.parse::<usize>().ok()?;
    if (1..=10).contains(&width)
        && bits.len() == width
        && bits.bytes().all(|bit| matches!(bit, b'0' | b'1'))
    {
        Some(symbol.to_string())
    } else {
        None
    }
}

#[cfg(test)]
fn uk_docs_source_zig_only() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = crate::zig_transport::uk_docs_source_bytes()?;
        String::from_utf8(bytes).map_err(|err| format!("ZIG_UK_DOCS_CARRIER invalid UTF-8: {err}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: uk-docs requires Zig; no Rust source fallback".into())
    }
}

#[cfg(test)]
fn ukrainian_docs() -> Result<Vec<SurfaceDoc>, String> {
    let source = uk_docs_source_zig_only()?;
    let program = parse(&source).map_err(|error| {
        format!(
            "не вдалося прочитати uk-docs.wsm: {}",
            error.render(&source)
        )
    })?;
    let root = program
        .first()
        .and_then(expr_list)
        .ok_or_else(|| "uk-docs.wsm: очікувався кореневий список".to_string())?;
    if root.first().and_then(expr_symbol) != Some("uk-api-docs") {
        return Err("uk-docs.wsm: невідомий кореневий тег".to_string());
    }
    let docs_form = root
        .iter()
        .filter_map(expr_list)
        .find(|items| items.first().and_then(expr_symbol) == Some("docs"))
        .ok_or_else(|| "uk-docs.wsm: відсутня секція docs".to_string())?;

    docs_form
        .iter()
        .skip(1)
        .map(|entry| {
            let fields =
                expr_list(entry).ok_or_else(|| "uk-docs.wsm: doc має бути списком".to_string())?;
            if fields.len() != 7 || fields.first().and_then(expr_symbol) != Some("doc") {
                return Err("uk-docs.wsm: некоректний doc-запис".to_string());
            }
            if expr_symbol(&fields[3]).is_none() {
                return Err("uk-docs.wsm: немає повної української проєкції".to_string());
            }
            Ok(SurfaceDoc {
                category: expr_symbol(&fields[1])
                    .ok_or_else(|| "uk-docs.wsm: category має бути символом".to_string())?
                    .to_string(),
                identity: expr_documentation_key(&fields[2]).ok_or_else(|| {
                    "uk-docs.wsm: потрібен точний домен D1–D10 з власною шириною".to_string()
                })?,
                kind: expr_symbol(&fields[4])
                    .ok_or_else(|| "uk-docs.wsm: kind має бути символом".to_string())?
                    .to_string(),
                call: expr_string(&fields[5])
                    .ok_or_else(|| "uk-docs.wsm: call має бути рядком".to_string())?
                    .to_string(),
                description: expr_string(&fields[6])
                    .ok_or_else(|| "uk-docs.wsm: description має бути рядком".to_string())?
                    .to_string(),
            })
        })
        .collect()
}

pub(crate) fn render_status() -> Result<String, String> {
    let entries = registry_entries()?;
    let denominator = public_denominator(entries);
    let uk = counts_for(entries, "ук");
    let en = counts_for(entries, "en");
    let ukr = counts_for(entries, "укр");
    let san = counts_for(entries, "san");
    let lisp = counts_for(entries, "LISP");
    let symbolic = entries
        .iter()
        .filter(|entry| {
            surface_name(entry, "sym")
                .and_then(|item| item.name.as_deref())
                .is_some()
        })
        .count();
    let four_projection_rows = entries
        .iter()
        .filter(|entry| {
            HUMAN_SURFACES.iter().all(|surface| {
                surface_name(entry, surface)
                    .and_then(|name| name.name.as_deref())
                    .is_some()
            })
        })
        .count();

    Ok(format!(
        "Проєкції таблиць D1–D11 · доменні координати: {denominator}\n\
         UK  present {:>3} · empty {:>3}\n\
         UKR present {:>3} · empty {:>3}\n\
         EN  present {:>3} · empty {:>3}\n\
         SAN present {:>3} · empty {:>3}\n\
         LISP present {:>3} · empty {:>3}\n\
         shared sym identities: {symbolic}\n\
         rows with all four human projections: {four_projection_rows}/{denominator}",
        uk.present,
        uk.empty,
        ukr.present,
        ukr.empty,
        en.present,
        en.empty,
        san.present,
        san.empty,
        lisp.present,
        lisp.empty,
    ))
}

pub(crate) fn render_names(surface: &str) -> Result<String, String> {
    let entries = registry_entries()?;
    if surface == "core" {
        let mut output = format!(
            "core: exact domain identities D1–D11 · {}\n",
            public_denominator(entries)
        );
        for (index, entry) in entries.iter().enumerate() {
            if index > 0 {
                output.push_str(if index % 12 == 0 { "\n" } else { " · " });
            }
            output.push_str(&entry.identity);
        }
        output
            .push_str("\n\ncore показує machine handles; людські назви дивіться через :ім'я <ID>.");
        return Ok(output);
    }

    let surface = normalize_surface(surface);
    let counts = counts_for(entries, surface);
    let mut output = format!(
        "surface {surface}: present {} · empty {} · total {}\n  ",
        counts.present,
        counts.empty,
        entries.len()
    );
    let mut first = true;
    for entry in entries {
        let Some(slot) = surface_name(entry, surface) else {
            continue;
        };
        if !first {
            output.push_str(" · ");
        }
        first = false;
        match slot.name.as_deref() {
            Some(name) => output.push_str(name),
            None => {
                output.push_str("(){");
                output.push_str(&entry.identity);
                output.push('}');
            }
        }
    }
    Ok(output)
}

pub(crate) fn render_name(surface: &str, requested: &str) -> Result<String, String> {
    let entries = registry_entries()?;
    let matches = find_entries(entries, requested);
    if matches.is_empty() {
        return Ok(format!(
            "«{requested}» не знайдено серед координат таблиць D1–D11; викличність з цього каталогу не випливає."
        ));
    };

    if matches.len() > 1 {
        let identities = matches
            .iter()
            .map(|entry| entry.identity.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        return Ok(format!(
            "«{requested}» неоднозначне; уточніть домен: {identities}"
        ));
    }
    let entry = matches[0];

    let mut output = format!(
        "identity: {}\n  UK: {}\n  UKR: {}\n  EN: {}\n  SAN: {}\n  LISP: {}\n  SYM: {}",
        entry.identity,
        rendered_name(surface_name(entry, "ук")),
        rendered_name(surface_name(entry, "укр")),
        rendered_name(surface_name(entry, "en")),
        rendered_name(surface_name(entry, "san")),
        rendered_name(surface_name(entry, "LISP")),
        rendered_name(surface_name(entry, "sym")),
    );
    output.push_str("\n  current: ");
    output.push_str(surface);

    Ok(output)
}

