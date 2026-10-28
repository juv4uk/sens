//! Механічне читання незмінених байтів проєкцій, переданих pinned Zig.
//! Номер таблиці та довжина є метаданими build-потоку, не кодами SENS.

pub fn projection_sources(mut bytes: &[u8]) -> Result<Vec<&str>, &'static str> {
    let mut sources = Vec::with_capacity(10);
    for domain in 1..=10u8 {
        let header = bytes.get(..5).ok_or("truncated projection header")?;
        if header[0] != domain {
            return Err("missing, duplicate or out-of-order projection table");
        }
        let len = u32::from_be_bytes(header[1..5].try_into().unwrap()) as usize;
        if len == 0 || len > 8 * 1024 * 1024 {
            return Err("invalid projection byte length");
        }
        bytes = &bytes[5..];
        let source = bytes.get(..len).ok_or("truncated projection bytes")?;
        sources.push(std::str::from_utf8(source).map_err(|_| "invalid projection text")?);
        bytes = &bytes[len..];
    }
    if !bytes.is_empty() {
        return Err("trailing projection bytes");
    }
    Ok(sources)
}

