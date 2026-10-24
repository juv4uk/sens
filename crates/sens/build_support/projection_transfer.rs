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

#[cfg(test)]
mod tests {
    use super::projection_sources;

    fn frames() -> Vec<u8> {
        let mut bytes = Vec::new();
        for domain in 1..=10u8 {
            bytes.push(domain);
            bytes.extend_from_slice(&3u32.to_be_bytes());
            bytes.extend_from_slice(b"a\nb");
        }
        bytes
    }

    #[test]
    fn opaque_multiline_bytes_survive_the_transfer() {
        let bytes = frames();
        assert_eq!(projection_sources(&bytes).unwrap(), vec!["a\nb"; 10]);
    }

    #[test]
    fn every_truncation_and_trailing_byte_is_rejected() {
        let mut bytes = frames();
        for end in 0..bytes.len() {
            assert!(projection_sources(&bytes[..end]).is_err(), "offset={end}");
        }
        bytes.push(0);
        assert_eq!(projection_sources(&bytes), Err("trailing projection bytes"));
    }

    #[test]
    fn table_substitution_and_invalid_lengths_are_rejected() {
        for (offset, value) in [(0, 2), (8, 1), (4, 0), (5, 0xff)] {
            let mut bytes = frames();
            bytes[offset] = value;
            assert!(projection_sources(&bytes).is_err(), "offset={offset}");
        }
        let mut bytes = frames();
        bytes[1..5].copy_from_slice(&u32::MAX.to_be_bytes());
        assert_eq!(
            projection_sources(&bytes),
            Err("invalid projection byte length")
        );
    }
}
