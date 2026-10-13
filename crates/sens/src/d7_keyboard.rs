//! D7 v2 keyboard projection: ratified migration DATA profile.
//! Machine identity is the exact W7 coordinate, never a glyph.
//! The enclosing SENS value provides the projection and exact bit length.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode { En, Uk, San }
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Unmapped(char), OutOfRange(u8), BadBitLength(usize), BadByteLength, NonzeroPadding, Overflow }
pub const UK: [char; 128] = [
    '\u{0}', '\u{1}', '\u{2}', '\u{3}', '\u{4}', '\u{5}', '\u{6}', '\u{7}',
    '\u{8}', '\u{9}', '\u{a}', '\u{b}', '\u{c}', '\u{d}', '\u{e}', '\u{f}',
    '\u{10}', '\u{11}', '\u{12}', '\u{13}', '\u{14}', '\u{15}', '\u{16}', '\u{17}',
    '\u{18}', '\u{19}', '\u{1a}', '\u{1b}', '\u{1c}', '\u{1d}', '\u{1e}', '\u{1f}',
    '\u{20}', '\u{21}', '\u{22}', '\u{2116}', '\u{3b}', '\u{25}', '\u{3f}', '\u{27}',
    '\u{28}', '\u{29}', '\u{2a}', '\u{2b}', '\u{431}', '\u{2d}', '\u{44e}', '\u{2e}',
    '\u{30}', '\u{31}', '\u{32}', '\u{33}', '\u{34}', '\u{35}', '\u{36}', '\u{37}',
    '\u{38}', '\u{39}', '\u{416}', '\u{436}', '\u{411}', '\u{3d}', '\u{42e}', '\u{2c}',
    '\u{20b4}', '\u{424}', '\u{418}', '\u{421}', '\u{412}', '\u{423}', '\u{410}', '\u{41f}',
    '\u{420}', '\u{428}', '\u{41e}', '\u{41b}', '\u{414}', '\u{42c}', '\u{422}', '\u{429}',
    '\u{417}', '\u{419}', '\u{41a}', '\u{406}', '\u{415}', '\u{413}', '\u{41c}', '\u{426}',
    '\u{427}', '\u{41d}', '\u{42f}', '\u{445}', '\u{491}', '\u{457}', '\u{3a}', '\u{5f}',
    '\u{454}', '\u{444}', '\u{438}', '\u{441}', '\u{432}', '\u{443}', '\u{430}', '\u{43f}',
    '\u{440}', '\u{448}', '\u{43e}', '\u{43b}', '\u{434}', '\u{44c}', '\u{442}', '\u{449}',
    '\u{437}', '\u{439}', '\u{43a}', '\u{456}', '\u{435}', '\u{433}', '\u{43c}', '\u{446}',
    '\u{447}', '\u{43d}', '\u{44f}', '\u{425}', '\u{490}', '\u{407}', '\u{404}', '\u{7f}',
];
pub const SAN: [char; 128] = [
    '\u{0}', '\u{1}', '\u{2}', '\u{3}', '\u{4}', '\u{5}', '\u{6}', '\u{7}',
    '\u{8}', '\u{9}', '\u{a}', '\u{b}', '\u{c}', '\u{d}', '\u{e}', '\u{f}',
    '\u{10}', '\u{11}', '\u{12}', '\u{13}', '\u{14}', '\u{15}', '\u{16}', '\u{17}',
    '\u{18}', '\u{19}', '\u{1a}', '\u{1b}', '\u{1c}', '\u{1d}', '\u{1e}', '\u{1f}',
    '\u{20}', '\u{21}', '\u{920}', '\u{23}', '\u{24}', '\u{25}', '\u{26}', '\u{91f}',
    '\u{28}', '\u{29}', '\u{2a}', '\u{90b}', '\u{2c}', '\u{903}', '\u{2e}', '\u{92f}',
    '\u{30}', '\u{31}', '\u{32}', '\u{33}', '\u{34}', '\u{35}', '\u{36}', '\u{37}',
    '\u{38}', '\u{39}', '\u{91b}', '\u{91a}', '\u{937}', '\u{943}', '\u{964}', '\u{95f}',
    '\u{40}', '\u{913}', '\u{934}', '\u{923}', '\u{905}', '\u{906}', '\u{907}', '\u{909}',
    '\u{92b}', '\u{918}', '\u{931}', '\u{916}', '\u{925}', '\u{936}', '\u{933}', '\u{927}',
    '\u{91d}', '\u{914}', '\u{908}', '\u{90f}', '\u{90a}', '\u{919}', '\u{929}', '\u{910}',
    '\u{901}', '\u{92d}', '\u{911}', '\u{921}', '\u{5c}', '\u{93c}', '\u{5e}', '\u{960}',
    '\u{60}', '\u{94b}', '\u{935}', '\u{92e}', '\u{94d}', '\u{93e}', '\u{93f}', '\u{941}',
    '\u{92a}', '\u{917}', '\u{930}', '\u{915}', '\u{924}', '\u{938}', '\u{932}', '\u{926}',
    '\u{91c}', '\u{94c}', '\u{940}', '\u{947}', '\u{942}', '\u{939}', '\u{928}', '\u{948}',
    '\u{902}', '\u{92c}', '\u{949}', '\u{922}', '\u{7c}', '\u{91e}', '\u{7e}', '\u{7f}',
];
pub fn decode(codes: &[u8], mode: Mode) -> Result<String, Error> {
    let mut result = String::new();
    for &code in codes {
        if code > 127 { return Err(Error::OutOfRange(code)); }
        result.push(match mode {
            Mode::En => char::from(code),
            Mode::Uk => UK[code as usize],
            Mode::San => SAN[code as usize],
        });
    }
    Ok(result)
}
pub fn encode(src: &str, mode: Mode) -> Result<Vec<u8>, Error> {
    src.chars().map(|ch| {
        match mode {
            Mode::En => if ch.is_ascii() { Ok(ch as u8) } else { Err(Error::Unmapped(ch)) },
            Mode::Uk | Mode::San => {
                let table = if mode == Mode::Uk { &UK } else { &SAN };
                table.iter().position(|&g| g == ch).map(|n| n as u8).ok_or(Error::Unmapped(ch))
            }
        }
    }).collect()
}
/// Pack exact W7 cells MSB-first; no interior byte padding.
pub fn pack7(codes: &[u8]) -> Result<Vec<u8>, Error> {
    let nbits = codes.len().checked_mul(7).ok_or(Error::Overflow)?;
    let byte_len = nbits.checked_add(7).ok_or(Error::Overflow)? / 8;
    let mut out = vec![0u8; byte_len];
    for (i, &code) in codes.iter().enumerate() {
        if code > 127 { return Err(Error::OutOfRange(code)); }
        for j in 0..7 {
            let pos = i * 7 + j;
            out[pos / 8] |= ((code >> (6-j)) & 1) << (7-(pos%8));
        }
    }
    Ok(out)
}
pub fn unpack7(bytes: &[u8], nbits: usize) -> Result<Vec<u8>, Error> {
    if nbits % 7 != 0 { return Err(Error::BadBitLength(nbits)); }
    let needed = nbits.checked_add(7).ok_or(Error::Overflow)? / 8;
    if bytes.len() != needed { return Err(Error::BadByteLength); }
    if nbits % 8 != 0 && !bytes.is_empty() {
        let pad = 8-nbits%8;
        if bytes[bytes.len()-1] & ((1u8 << pad)-1) != 0 { return Err(Error::NonzeroPadding); }
    }
    let mut out = Vec::with_capacity(nbits/7);
    for i in 0..nbits/7 {
        let mut x = 0u8;
        for j in 0..7 {
            let pos=i*7+j;
            x = (x << 1) | ((bytes[pos/8] >> (7-pos%8)) & 1);
        }
        out.push(x);
    }
    Ok(out)
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;
    #[test] fn all_128_coordinates_roundtrip() {
        let codes: Vec<u8> = (0u8..=127).collect();
        for mode in [Mode::En, Mode::Uk, Mode::San] {
            let text=decode(&codes,mode).unwrap();
            assert_eq!(encode(&text,mode).unwrap(),codes);
            assert_eq!(text.chars().collect::<HashSet<_>>().len(),128);
        }
    }
    #[test] fn multilingual_examples() {
        for (text,mode) in [
            ("Привіт, друже! ім'я ґанок Європа №1 ₴.",Mode::Uk),
            ("संस्कृतम्",Mode::San),
            ("(quote data)",Mode::En),
        ] {
            let data=encode(text,mode).unwrap();
            let packed=pack7(&data).unwrap();
            assert_eq!(decode(&unpack7(&packed,data.len()*7).unwrap(),mode).unwrap(),text);
        }
        assert_eq!(encode("'",Mode::Uk).unwrap(),vec![39]);
        assert_eq!(decode(&encode("Привіт",Mode::Uk).unwrap(),Mode::En).unwrap(),"Ghbdsn");
    }
    #[test] fn malformed_values_fail_closed() {
        assert_eq!(encode("🙂",Mode::Uk),Err(Error::Unmapped('🙂')));
        assert_eq!(pack7(&[128]),Err(Error::OutOfRange(128)));
        assert_eq!(unpack7(&[0],8),Err(Error::BadBitLength(8)));
        assert_eq!(unpack7(&[1],7),Err(Error::NonzeroPadding));
        assert_eq!(unpack7(&[],7),Err(Error::BadByteLength));
    }
}
