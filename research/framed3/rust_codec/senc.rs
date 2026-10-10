//! Спільний дослідний фізичний кодек SENS: Рамка-3 (F3) і Tb-33 (F4).
//!
//! Канонічний `.sens` **лишається T5**; цей модуль ані змінює, ані підмінює
//! канонічне читання T5. Він надає окремий носій `.senc` за явно заданим
//! профілем і перевіреною міткою — **без автовизначення вмісту**.
//!
//! Джерело досліду (тут семантично не авторське):
//! `research/framed3/{research_codec.py,tb33_tail_research.py,adaptive_encoder.py}`
//! на базовому SHA PR #5429 `f7079c792f1c81f9318a9372f40f650bfb1c31d6`.
//!
//! Модуль навмисно **без залежностей** (лише `std`), щоб його правильність
//! міг незалежно перевірити Rust-оракул поза збіркою всього ядра.
//! Тут немає семантичних таблиць D1–D9, перенумерації доменів чи зміни
//! фізичного T5. Трити `2` — лише транспортні розділювачі й фізична межа.
//!
//! Мітки `F3`/`F4` навмисно поза доменом T5 (0..242, п'ять тритів на байт),
//! тож хибний маршрут не дасть непомітного успіху канонічного T5-декодера.
//! Але сама мітка **не** доводить безпомилковість пошкодженого `.senc`:
//! кожен декод мусить канонічно перекодуватися в ті самі байти.

use std::cmp::Ordering;
use std::sync::OnceLock;

/// Мітка профілю «Рамка-3» у байтовому носії `.senc`.
pub const FRAME_LABEL: u8 = 0xF3;
/// Мітка профілю «Tb-33» у байтовому носії `.senc`.
pub const TB33_LABEL: u8 = 0xF4;
/// Основа тернарного транспорту.
pub const BASE: u32 = 3;
/// П'ять тритів на фізичний байт канонічного T5 (0..242).
pub const TRITS_PER_BYTE: usize = 5;
/// Скінченна межа однієї зовнішньої D2-рамки в дослідному профілі.
pub const FRAME_MAX_TRITS: usize = 128;
/// Тритів у повному блоці Tb-33.
pub const TB33_BLOCK_TRITS: usize = 33;
/// Байтів у повному блоці Tb-33 (48 біт).
pub const TB33_BLOCK_BYTES: usize = 6;

/// Помилка дослідного носія: формат, довжина або відновлення точних слів
/// не відповідають контракту. Ніколи не є підставою підмінити T5.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SencError {
    /// Слово не є точним двійковим кодом ширини D1–D9.
    InvalidWord,
    /// Порушено зовнішню рамку `10 … 01` або правило без сусідніх `22`.
    FrameShape,
    /// Довжина/номер поза обмеженим дослідним профілем Рамки-3.
    FrameRange,
    /// Відновлений потік Рамки-3 не канонічний.
    FrameCanonical,
    /// Порушено межу Tb-33, кінцеве `01` або правило без сусідніх `22`.
    TailShape,
    /// Номер/довжина поза діапазоном Tb-33.
    TailRange,
    /// Байти Tb-33 не канонічні.
    TailCanonical,
    /// Невідома пара профілю й розширення, або порожній носій.
    CarrierShape,
    /// Мітка не відповідає заявленому профілю.
    UnknownLabel,
    /// Точне зворотне перетворення не збігається (підміна/пошкодження).
    NotCanonical,
}

// ---------------------------------------------------------------------------
// Мінімальний беззнаковий big-int (основа 2^32). Потрібен лише для Рамки-3:
// код/місткість до 128 тритів сягають ~23 байт, тобто понад `u128`.
// Потрібні лише додавання, віднімання, порівняння й конверсія байтів —
// без множення чи ділення.
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, Eq, PartialEq)]
struct BigUint {
    /// Молодші лімби попереду; нормалізовано (без провідних нульових лімбе).
    limbs: Vec<u32>,
}

impl BigUint {
    fn zero() -> Self {
        BigUint { limbs: Vec::new() }
    }

    fn one() -> Self {
        BigUint { limbs: vec![1] }
    }

    #[cfg(test)]
    fn is_zero(&self) -> bool {
        self.limbs.is_empty()
    }

    fn one_shl(bits: usize) -> Self {
        let limb = bits / 32;
        let shift = bits % 32;
        let mut limbs = vec![0u32; limb + 1];
        limbs[limb] = 1u32 << shift;
        BigUint { limbs }
    }

    fn normalize(mut self) -> Self {
        while matches!(self.limbs.last(), Some(&0)) {
            self.limbs.pop();
        }
        self
    }

    fn cmp_big(&self, other: &Self) -> Ordering {
        if self.limbs.len() != other.limbs.len() {
            return self.limbs.len().cmp(&other.limbs.len());
        }
        for i in (0..self.limbs.len()).rev() {
            match self.limbs[i].cmp(&other.limbs[i]) {
                Ordering::Equal => continue,
                ord => return ord,
            }
        }
        Ordering::Equal
    }

    fn add(&self, other: &Self) -> Self {
        let len = self.limbs.len().max(other.limbs.len());
        let mut out = Vec::with_capacity(len + 1);
        let mut carry: u64 = 0;
        for i in 0..len {
            let a = self.limbs.get(i).copied().unwrap_or(0) as u64;
            let b = other.limbs.get(i).copied().unwrap_or(0) as u64;
            let sum = a + b + carry;
            out.push(sum as u32);
            carry = sum >> 32;
        }
        if carry != 0 {
            out.push(carry as u32);
        }
        BigUint { limbs: out }.normalize()
    }

    /// Самозадовільне віднімання: передбачає `self >= other`.
    fn sub(&self, other: &Self) -> Self {
        let mut out = Vec::with_capacity(self.limbs.len());
        let mut borrow: i64 = 0;
        for i in 0..self.limbs.len() {
            let a = self.limbs[i] as i64;
            let b = other.limbs.get(i).copied().unwrap_or(0) as i64;
            let mut diff = a - b - borrow;
            if diff < 0 {
                diff += 1i64 << 32;
                borrow = 1;
            } else {
                borrow = 0;
            }
            out.push(diff as u32);
        }
        BigUint { limbs: out }.normalize()
    }

    /// Великий кінець: `width` байтів. Передбачає, що значення вміщається.
    fn to_bytes_be(&self, width: usize) -> Vec<u8> {
        let mut le = Vec::with_capacity(self.limbs.len() * 4);
        for &limb in &self.limbs {
            le.extend_from_slice(&limb.to_le_bytes());
        }
        while le.len() < width {
            le.push(0);
        }
        le.truncate(width);
        le.reverse();
        le
    }

    fn from_bytes_be(bytes: &[u8]) -> Self {
        let mut limbs = Vec::new();
        let mut cur: u32 = 0;
        let mut shift = 0u32;
        for &byte in bytes.iter().rev() {
            cur |= (byte as u32) << shift;
            shift += 8;
            if shift == 32 {
                limbs.push(cur);
                cur = 0;
                shift = 0;
            }
        }
        if shift > 0 {
            limbs.push(cur);
        }
        BigUint { limbs }.normalize()
    }
}

// ---------------------------------------------------------------------------
// Спільні точні слова D1–D9 і транспортні трити.
// ---------------------------------------------------------------------------

/// Загальна перевірка точних двійкових слів D1–D9 (без вимоги рамки).
fn check_words(words: &[String]) -> Result<Vec<String>, SencError> {
    let result = words.to_vec();
    for word in &result {
        if word.is_empty() || word.len() > 9 || !word.bytes().all(|b| b == b'0' || b == b'1') {
            return Err(SencError::InvalidWord);
        }
    }
    Ok(result)
}

/// Транспортні трити: точні слова, розділені одиничним `2`, без зайвих `2`.
fn transport_trits(words: &[String]) -> Vec<u8> {
    let mut trits = Vec::new();
    for (position, word) in words.iter().enumerate() {
        if position != 0 {
            trits.push(2);
        }
        for byte in word.bytes() {
            trits.push(byte - b'0');
        }
    }
    trits
}

/// Розбити транспортний потік на точні слова за розділювачем `2`.
fn split_trits(trits: &[u8]) -> Vec<String> {
    let mut words = Vec::new();
    let mut current = String::new();
    for &trit in trits {
        if trit == 2 {
            words.push(std::mem::take(&mut current));
        } else {
            current.push((b'0' + trit) as char);
        }
    }
    words.push(current);
    words
}

// ---------------------------------------------------------------------------
// Канонічний T5 (механічна локальна копія для самодостатності).
// Незалежний оракул (`ternary_transport`) має дати побайтовий збіг — тести ядра.
// ---------------------------------------------------------------------------

fn t5_encode(words: &[String]) -> Result<Vec<u8>, SencError> {
    let words = check_words(words)?;
    let mut trits = transport_trits(&words);
    while trits.len() % TRITS_PER_BYTE != 0 {
        trits.push(2);
    }
    Ok(trits
        .chunks(TRITS_PER_BYTE)
        .map(|chunk| chunk.iter().fold(0u8, |acc, &trit| acc * 3 + trit))
        .collect())
}

fn t5_decode(data: &[u8]) -> Result<Vec<String>, SencError> {
    let mut trits = Vec::with_capacity(data.len() * TRITS_PER_BYTE);
    for &byte in data {
        if byte as u32 >= BASE.pow(TRITS_PER_BYTE as u32) {
            return Err(SencError::InvalidWord);
        }
        let mut value = byte;
        let mut chunk = [0u8; TRITS_PER_BYTE];
        for slot in chunk.iter_mut().rev() {
            *slot = value % 3;
            value /= 3;
        }
        trits.extend_from_slice(&chunk);
    }
    while matches!(trits.last(), Some(&2)) {
        trits.pop();
    }
    let words = if trits.is_empty() {
        Vec::new()
    } else {
        check_words(&split_trits(&trits))?
    };
    if t5_encode(&words)? != data {
        return Err(SencError::NotCanonical);
    }
    Ok(words)
}

// ---------------------------------------------------------------------------
// Профіль «Рамка-3» (F3): одна зовнішня D2-рамка `10 … 01`, без сусідніх `22`.
// ---------------------------------------------------------------------------

const OPEN_TABLE: [u8; 3] = [1, 0, 2];
const CLOSE_TABLE: [u8; 3] = [2, 0, 1];

fn frame_allowed(n: usize, position: usize) -> Vec<u8> {
    if position < 3 {
        return vec![OPEN_TABLE[position]];
    }
    if position >= n - 3 {
        return vec![CLOSE_TABLE[position - (n - 3)]];
    }
    vec![0, 1, 2]
}

/// Кількість допустимих суфіксів з позиції `position` за попереднього трита.
fn frame_ways_table(n: usize) -> Vec<[BigUint; 4]> {
    let mut table: Vec<[BigUint; 4]> = (0..=n)
        .map(|_| {
            [
                BigUint::zero(),
                BigUint::zero(),
                BigUint::zero(),
                BigUint::zero(),
            ]
        })
        .collect();
    for slot in table[n].iter_mut() {
        *slot = BigUint::one();
    }
    let mut position = n;
    while position > 0 {
        position -= 1;
        let allowed = frame_allowed(n, position);
        for previous_index in 0..4usize {
            let previous = previous_index as i32 - 1;
            let mut acc = BigUint::zero();
            for &digit in &allowed {
                if previous == 2 && digit == 2 {
                    continue;
                }
                acc = acc.add(&table[position + 1][digit as usize + 1]);
            }
            table[position][previous_index] = acc;
        }
    }
    table
}

/// Верхня межа кількості транспортних послідовностей довжини `n`.
fn frame_capacity(n: usize) -> BigUint {
    if n == 5 {
        return BigUint::one();
    }
    if n < 7 || n > FRAME_MAX_TRITS {
        return BigUint::zero();
    }
    frame_ways_table(n)[0][0].clone()
}

fn frame_rank(n: usize, trits: &[u8]) -> Result<BigUint, SencError> {
    if n == 5 {
        return if trits == [1, 0, 2, 0, 1] {
            Ok(BigUint::zero())
        } else {
            Err(SencError::FrameShape)
        };
    }
    if !(7..=FRAME_MAX_TRITS).contains(&n) {
        return Err(SencError::FrameRange);
    }
    let table = frame_ways_table(n);
    let mut index = BigUint::zero();
    let mut previous: i32 = -1;
    for (position, &digit) in trits.iter().enumerate() {
        let allowed = frame_allowed(n, position);
        if !allowed.contains(&digit) || (previous == 2 && digit == 2) {
            return Err(SencError::FrameShape);
        }
        for &smaller in &allowed {
            if previous == 2 && smaller == 2 {
                continue;
            }
            if smaller == digit {
                break;
            }
            index = index.add(&table[position + 1][smaller as usize + 1]);
        }
        previous = digit as i32;
    }
    Ok(index)
}

fn frame_unrank(n: usize, index: &BigUint) -> Result<Vec<u8>, SencError> {
    if index.cmp_big(&frame_capacity(n)) != Ordering::Less {
        return Err(SencError::FrameRange);
    }
    if n == 5 {
        return Ok(vec![1, 0, 2, 0, 1]);
    }
    let table = frame_ways_table(n);
    let mut remaining = index.clone();
    let mut previous: i32 = -1;
    let mut out = Vec::with_capacity(n);
    for position in 0..n {
        let allowed = frame_allowed(n, position);
        let mut chosen = false;
        for &digit in &allowed {
            if previous == 2 && digit == 2 {
                continue;
            }
            let possible = &table[position + 1][digit as usize + 1];
            if remaining.cmp_big(possible) == Ordering::Less {
                out.push(digit);
                previous = digit as i32;
                chosen = true;
                break;
            }
            remaining = remaining.sub(possible);
        }
        if !chosen {
            return Err(SencError::FrameRange);
        }
    }
    Ok(out)
}

/// Найкоротші групи за кількістю байтів і довжиною у тритах.
fn frame_buckets() -> &'static Vec<(usize, usize, usize)> {
    static BUCKETS: OnceLock<Vec<(usize, usize, usize)>> = OnceLock::new();
    BUCKETS.get_or_init(|| {
        let mut result = Vec::new();
        let mut n = 5usize;
        let mut byte_count = 1usize;
        while n <= FRAME_MAX_TRITS {
            let start = n;
            let mut capacity_left = BigUint::one_shl(8 * byte_count);
            while n <= FRAME_MAX_TRITS {
                let count = frame_capacity(n);
                if count.cmp_big(&capacity_left) == Ordering::Greater {
                    break;
                }
                capacity_left = capacity_left.sub(&count);
                n += 1;
            }
            assert!(n > start, "byte bucket cannot hold any length");
            result.push((byte_count, start, n - 1));
            byte_count += 1;
        }
        result
    })
}

/// Перевірити зовнішню рамку `10 … 01` і повернути транспортні трити.
fn frame_transport(words: &[String]) -> Result<Vec<u8>, SencError> {
    if words.len() < 2 || words[0] != "10" || words[words.len() - 1] != "01" {
        return Err(SencError::FrameShape);
    }
    let mut nesting: i32 = 0;
    for (position, word) in words.iter().enumerate() {
        if word.is_empty() || word.len() > 9 || !word.bytes().all(|b| b == b'0' || b == b'1') {
            return Err(SencError::InvalidWord);
        }
        if word == "10" {
            nesting += 1;
        } else if word == "01" {
            nesting -= 1;
            if nesting < 0 || (nesting == 0 && position < words.len() - 1) {
                return Err(SencError::FrameShape);
            }
        }
    }
    if nesting != 0 {
        return Err(SencError::FrameShape);
    }
    let trits = transport_trits(words);
    if trits.len() > FRAME_MAX_TRITS {
        return Err(SencError::FrameRange);
    }
    frame_rank(trits.len(), &trits)?;
    Ok(trits)
}

fn frame_encode(words: &[String]) -> Result<Vec<u8>, SencError> {
    let trits = frame_transport(words)?;
    let n = trits.len();
    for &(width, lo, hi) in frame_buckets() {
        if lo <= n && n <= hi {
            let mut offset = BigUint::zero();
            for length in lo..n {
                offset = offset.add(&frame_capacity(length));
            }
            let code = offset.add(&frame_rank(n, &trits)?);
            return Ok(code.to_bytes_be(width));
        }
    }
    Err(SencError::FrameRange)
}

fn frame_decode(data: &[u8]) -> Result<Vec<String>, SencError> {
    for &(width, lo, hi) in frame_buckets() {
        if data.len() == width {
            let mut code = BigUint::from_bytes_be(data);
            for length in lo..=hi {
                let count = frame_capacity(length);
                if code.cmp_big(&count) == Ordering::Less {
                    let trits = frame_unrank(length, &code)?;
                    let words = split_trits(&trits);
                    if frame_transport(&words)? != trits || frame_encode(&words)? != data {
                        return Err(SencError::FrameCanonical);
                    }
                    return Ok(words);
                }
                code = code.sub(&count);
            }
            return Err(SencError::FrameRange);
        }
    }
    Err(SencError::FrameShape)
}

// ---------------------------------------------------------------------------
// Tb-33 (F4): блоки по 33 трити / 48 біт з окремим ранжуванням фінального
// хвоста. Усі величини вміщаються в `u128` (48 біт), big-int не потрібен.
// ---------------------------------------------------------------------------

fn tb_ways_table() -> &'static [[u128; 4]; TB33_BLOCK_TRITS + 1] {
    static TABLE: OnceLock<[[u128; 4]; TB33_BLOCK_TRITS + 1]> = OnceLock::new();
    TABLE.get_or_init(|| {
        let mut table = [[0u128; 4]; TB33_BLOCK_TRITS + 1];
        for slot in table[0].iter_mut() {
            *slot = 1;
        }
        for remaining in 1..=TB33_BLOCK_TRITS {
            for previous_index in 0..4usize {
                let previous = previous_index as i32 - 1;
                let mut acc = 0u128;
                for digit in 0usize..3 {
                    if previous == 2 && digit == 2 {
                        continue;
                    }
                    acc += table[remaining - 1][digit + 1];
                }
                table[remaining][previous_index] = acc;
            }
        }
        table
    })
}

fn tb_ways(remaining: usize, previous: i32) -> u128 {
    tb_ways_table()[remaining][(previous + 1) as usize]
}

fn tb_rank(trits: &[u8]) -> Result<u128, SencError> {
    let mut result = 0u128;
    let mut previous: i32 = -1;
    for (position, &digit) in trits.iter().enumerate() {
        if digit > 2 || (previous == 2 && digit == 2) {
            return Err(SencError::TailShape);
        }
        for smaller in 0..digit {
            if previous == 2 && smaller == 2 {
                continue;
            }
            result += tb_ways(trits.len() - position - 1, smaller as i32);
        }
        previous = digit as i32;
    }
    Ok(result)
}

fn tb_unrank(length: usize, code: u128) -> Result<Vec<u8>, SencError> {
    if code >= tb_ways(length, -1) {
        return Err(SencError::TailRange);
    }
    let mut remaining = code;
    let mut previous: i32 = -1;
    let mut out = Vec::with_capacity(length);
    for position in 0..length {
        let left = length - position - 1;
        let mut chosen = false;
        for digit in 0..3u8 {
            if previous == 2 && digit == 2 {
                continue;
            }
            let width = tb_ways(left, digit as i32);
            if remaining < width {
                out.push(digit);
                previous = digit as i32;
                chosen = true;
                break;
            }
            remaining -= width;
        }
        if !chosen {
            return Err(SencError::TailRange);
        }
    }
    Ok(out)
}

fn tb_tail_count(length: usize) -> u128 {
    if length == 1 {
        return 1;
    }
    if (2..=TB33_BLOCK_TRITS).contains(&length) {
        return tb_ways(length - 2, -1);
    }
    0
}

fn tb_tail_capacity() -> u128 {
    static CAPACITY: OnceLock<u128> = OnceLock::new();
    *CAPACITY.get_or_init(|| (1..=TB33_BLOCK_TRITS).map(tb_tail_count).sum())
}

fn tb_final_rank(tail: &[u8]) -> Result<u128, SencError> {
    let length = tail.len();
    if tb_tail_count(length) == 0 {
        return Err(SencError::TailShape);
    }
    let inside = if length == 1 {
        if tail[0] != 1 {
            return Err(SencError::TailShape);
        }
        0
    } else {
        if tail[length - 2] != 0 || tail[length - 1] != 1 {
            return Err(SencError::TailShape);
        }
        tb_rank(&tail[..length - 2])?
    };
    let mut base = 0u128;
    for n in 1..length {
        base += tb_tail_count(n);
    }
    Ok(base + inside)
}

fn tb_final_unrank(code: u128) -> Result<Vec<u8>, SencError> {
    if code >= tb_tail_capacity() {
        return Err(SencError::TailRange);
    }
    let mut remaining = code;
    for length in 1..=TB33_BLOCK_TRITS {
        let count = tb_tail_count(length);
        if remaining < count {
            if length == 1 {
                return Ok(vec![1]);
            }
            let mut out = tb_unrank(length - 2, remaining)?;
            out.push(0);
            out.push(1);
            return Ok(out);
        }
        remaining -= count;
    }
    Err(SencError::TailRange)
}

fn tb_validate(trits: &[u8]) -> Result<(), SencError> {
    if trits.len() < 2 || trits[trits.len() - 2] != 0 || trits[trits.len() - 1] != 1 {
        return Err(SencError::TailShape);
    }
    if trits.iter().any(|&digit| digit > 2) {
        return Err(SencError::TailShape);
    }
    if trits.windows(2).any(|pair| pair[0] == 2 && pair[1] == 2) {
        return Err(SencError::TailShape);
    }
    Ok(())
}

fn tb_block_from_bytes(slice: &[u8]) -> u128 {
    let mut buffer = [0u8; 16];
    buffer[16 - TB33_BLOCK_BYTES..].copy_from_slice(slice);
    u128::from_be_bytes(buffer)
}

fn tb_encode(trits: &[u8]) -> Result<Vec<u8>, SencError> {
    tb_validate(trits)?;
    let full_before_last = (trits.len() - 1) / TB33_BLOCK_TRITS;
    let mut out = Vec::new();
    let mut offset = 0usize;
    for _ in 0..full_before_last {
        let block = &trits[offset..offset + TB33_BLOCK_TRITS];
        out.extend_from_slice(&tb_rank(block)?.to_be_bytes()[16 - TB33_BLOCK_BYTES..]);
        offset += TB33_BLOCK_TRITS;
    }
    let tail = &trits[offset..];
    out.extend_from_slice(&tb_final_rank(tail)?.to_be_bytes()[16 - TB33_BLOCK_BYTES..]);
    Ok(out)
}

fn tb_decode(data: &[u8]) -> Result<Vec<u8>, SencError> {
    if data.is_empty() || data.len() % TB33_BLOCK_BYTES != 0 {
        return Err(SencError::TailShape);
    }
    let mut trits = Vec::new();
    let full_blocks = data.len() / TB33_BLOCK_BYTES - 1;
    for index in 0..full_blocks {
        let start = index * TB33_BLOCK_BYTES;
        let code = tb_block_from_bytes(&data[start..start + TB33_BLOCK_BYTES]);
        trits.extend(tb_unrank(TB33_BLOCK_TRITS, code)?);
    }
    let last = tb_block_from_bytes(&data[data.len() - TB33_BLOCK_BYTES..]);
    trits.extend(tb_final_unrank(last)?);
    tb_validate(&trits)?;
    if tb_encode(&trits)? != data {
        return Err(SencError::TailCanonical);
    }
    Ok(trits)
}

// ---------------------------------------------------------------------------
// Адаптивний вибір і явний (за міткою) маршрут.
// ---------------------------------------------------------------------------

/// Дослідний фізичний профіль носія.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Profile {
    /// Канонічний T5 (`.sens`), без заголовка.
    T5,
    /// Рамка-3 (`.senc`, мітка `F3`).
    Frame3,
    /// Tb-33 (`.senc`, мітка `F4`).
    Tb33,
}

/// Обраний носій: профіль, фізичні байти та очікуване розширення.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Carrier {
    pub profile: Profile,
    pub data: Vec<u8>,
    pub extension: &'static str,
}

/// Мінімум фізичних байтів серед трьох маршрутів. За рівності перемагає T5.
/// Повертає `.sens` (T5) або саморозрізнюваний `.senc` з однобайтовою міткою.
/// Це **не** доказ глобальної оптимальності всіх можливих кодеків.
pub fn encode_smallest(words: &[String]) -> Result<Carrier, SencError> {
    let words = check_words(words)?;
    let t5 = t5_encode(&words)?;
    let mut best = Carrier {
        profile: Profile::T5,
        data: t5,
        extension: ".sens",
    };
    if let Ok(body) = frame_encode(&words) {
        let mut data = Vec::with_capacity(body.len() + 1);
        data.push(FRAME_LABEL);
        data.extend_from_slice(&body);
        if data.len() < best.data.len() {
            best = Carrier {
                profile: Profile::Frame3,
                data,
                extension: ".senc",
            };
        }
    }
    if let Ok(body) = tb_encode(&transport_trits(&words)) {
        let mut data = Vec::with_capacity(body.len() + 1);
        data.push(TB33_LABEL);
        data.extend_from_slice(&body);
        if data.len() < best.data.len() {
            best = Carrier {
                profile: Profile::Tb33,
                data,
                extension: ".senc",
            };
        }
    }
    if read_carrier(&best)? != words {
        return Err(SencError::NotCanonical);
    }
    Ok(best)
}

/// Маршрут визначений профілем, розширенням і перевіреною міткою, не
/// евристикою. Кожен `.senc` канонічно перекодовується в ті самі байти.
pub fn read_carrier(carrier: &Carrier) -> Result<Vec<String>, SencError> {
    if carrier.profile == Profile::T5 {
        if carrier.extension != ".sens" {
            return Err(SencError::CarrierShape);
        }
        return t5_decode(&carrier.data);
    }
    if carrier.extension != ".senc" || carrier.data.is_empty() {
        return Err(SencError::CarrierShape);
    }
    let label = carrier.data[0];
    let body = &carrier.data[1..];
    match carrier.profile {
        Profile::Frame3 => {
            if label != FRAME_LABEL {
                return Err(SencError::UnknownLabel);
            }
            let words = frame_decode(body)?;
            let mut reencoded = vec![FRAME_LABEL];
            reencoded.extend_from_slice(&frame_encode(&words)?);
            if reencoded == carrier.data {
                Ok(words)
            } else {
                Err(SencError::NotCanonical)
            }
        }
        Profile::Tb33 => {
            if label != TB33_LABEL {
                return Err(SencError::UnknownLabel);
            }
            let trits = tb_decode(body)?;
            let words = check_words(&split_trits(&trits))?;
            let mut reencoded = vec![TB33_LABEL];
            reencoded.extend_from_slice(&tb_encode(&trits)?);
            if reencoded == carrier.data {
                Ok(words)
            } else {
                Err(SencError::NotCanonical)
            }
        }
        Profile::T5 => unreachable!("T5 handled above"),
    }
}

/// Явний маршрут читання `.senc` за оголошеною міткою (без автовизначення
/// за вмістом): `F3` → Рамка-3, `F4` → Tb-33, інша мітка → відмова.
pub fn decode_senc(data: &[u8]) -> Result<Vec<String>, SencError> {
    if data.is_empty() {
        return Err(SencError::CarrierShape);
    }
    let profile = match data[0] {
        FRAME_LABEL => Profile::Frame3,
        TB33_LABEL => Profile::Tb33,
        _ => return Err(SencError::UnknownLabel),
    };
    read_carrier(&Carrier {
        profile,
        data: data.to_vec(),
        extension: ".senc",
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn words(list: &[&str]) -> Vec<String> {
        list.iter().map(|word| word.to_string()).collect()
    }

    fn hex(bytes: &[u8]) -> String {
        bytes.iter().map(|byte| format!("{byte:02x}")).collect()
    }

    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self) -> u64 {
            self.0 = self
                .0
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            self.0
        }
    }

    #[test]
    fn known_t5_and_frame_examples() {
        let cases = [
            (words(&["10", "01"]), "64", "00"),
            (words(&["10", "001", "00", "000", "01"]), "638906a1", "23d0"),
            (
                words(&["10", "100", "00", "10", "111", "00", "1", "00", "0", "01", "01"]),
                "66386789893b35",
                "2109895eb5",
            ),
        ];
        for (case, t5_hex, frame_hex) in cases {
            assert_eq!(hex(&t5_encode(&case).unwrap()), t5_hex);
            assert_eq!(hex(&frame_encode(&case).unwrap()), frame_hex);
            assert_eq!(
                frame_decode(&frame_encode(&case).unwrap()).unwrap(),
                case
            );
            assert_eq!(t5_decode(&t5_encode(&case).unwrap()).unwrap(), case);
        }
    }

    #[test]
    fn buckets_first_three() {
        let buckets = frame_buckets();
        assert_eq!(&buckets[..3], &[(1, 5, 11), (2, 12, 17), (3, 18, 22)]);
    }

    #[test]
    fn frame_rank_unrank_boundaries() {
        for n in [5usize, 7, 9, 18, 33, 64, 128] {
            let capacity = frame_capacity(n);
            if capacity.is_zero() {
                continue;
            }
            let last = capacity.sub(&BigUint::one());
            for index in [BigUint::zero(), last] {
                let trits = frame_unrank(n, &index).unwrap();
                assert_eq!(frame_rank(n, &trits).unwrap(), index);
            }
        }
    }

    fn random_below(rng: &mut Lcg, capacity: &BigUint) -> BigUint {
        let limbs = capacity.limbs.len();
        if limbs == 0 {
            return BigUint::zero();
        }
        let mut raw = vec![0u8; limbs * 4];
        for byte in raw.iter_mut() {
            *byte = rng.next() as u8;
        }
        let candidate = BigUint::from_bytes_be(&raw);
        if candidate.cmp_big(capacity) == Ordering::Less {
            candidate
        } else {
            capacity.sub(&BigUint::one())
        }
    }

    #[test]
    fn frame_rank_unrank_random_and_exhaustive() {
        let mut rng = Lcg(20261010);
        for n in [5usize, 7, 10, 18, 33, 64, 127, 128] {
            let capacity = frame_capacity(n);
            if capacity.is_zero() {
                continue;
            }
            for _ in 0..16 {
                let candidate = random_below(&mut rng, &capacity);
                let trits = frame_unrank(n, &candidate).unwrap();
                assert_eq!(trits.len(), n);
                assert_eq!(frame_rank(n, &trits).unwrap(), candidate);
            }
        }
        // Вичерпний доказ на замкненому просторі малих довжин:
        // trit-інваріант тримається для КОЖНОГО індексу, а канонічний
        // word-roundtrip — лише для індексів, чиї трити є точною рамкою слів.
        for n in [5usize, 7, 9, 11, 12] {
            let capacity = frame_capacity(n);
            assert!(!capacity.is_zero(), "capacity({n}) must be non-zero");
            let mut index = BigUint::zero();
            let mut canonical = 0usize;
            while index.cmp_big(&capacity) == Ordering::Less {
                let trits = frame_unrank(n, &index).unwrap();
                assert_eq!(frame_rank(n, &trits).unwrap(), index);
                let words = split_trits(&trits);
                if let Ok(encoded) = frame_encode(&words) {
                    assert_eq!(frame_decode(&encoded).unwrap(), words);
                    canonical += 1;
                }
                index = index.add(&BigUint::one());
            }
            assert!(canonical > 0, "no canonical word frames at n={n}");
        }
    }

    #[test]
    fn unused_physical_code_rejected() {
        let mut used = BigUint::zero();
        for length in 5..=11 {
            used = used.add(&frame_capacity(length));
        }
        assert!(used.cmp_big(&BigUint::one_shl(8)) == Ordering::Less);
        assert!(frame_decode(&used.to_bytes_be(1)).is_err());
    }

    #[test]
    fn tb_ways_matches_recurrence() {
        // g(n) = 2*g(n-1) + 2*g(n-2), g(0)=1, g(1)=3 — потік без сусідніх 22.
        let mut expected = [0u128; TB33_BLOCK_TRITS + 1];
        expected[0] = 1;
        expected[1] = 3;
        for n in 2..=TB33_BLOCK_TRITS {
            expected[n] = 2 * expected[n - 1] + 2 * expected[n - 2];
        }
        for n in 0..=TB33_BLOCK_TRITS {
            assert_eq!(tb_ways(n, -1), expected[n], "ways({n})");
        }
    }

    #[test]
    fn tb33_exhaustive_small_lengths() {
        for length in 2..=9usize {
            let total = 3usize.pow(length as u32);
            for code in 0..total {
                let mut trits = vec![0u8; length];
                let mut value = code;
                for slot in trits.iter_mut().rev() {
                    *slot = (value % 3) as u8;
                    value /= 3;
                }
                if trits[length - 2] != 0 || trits[length - 1] != 1 {
                    continue;
                }
                if trits.windows(2).any(|pair| pair[0] == 2 && pair[1] == 2) {
                    continue;
                }
                let encoded = tb_encode(&trits).unwrap();
                assert_eq!(tb_decode(&encoded).unwrap(), trits);
            }
        }
    }

    #[test]
    fn tb33_negative_mutants() {
        assert!(tb_encode(&[1, 0, 2]).is_err());
        assert!(tb_encode(&[2, 2, 0, 1]).is_err());
        assert!(tb_decode(&[]).is_err());
        assert!(tb_decode(&[0, 1]).is_err());
        let trits = vec![1u8, 0, 1, 0, 1, 0, 1];
        let encoded = tb_encode(&trits).unwrap();
        let mut broken = encoded.clone();
        let last = broken.len() - 1;
        broken[last] = encoded[last].wrapping_add(7);
        match tb_decode(&broken) {
            Err(_) => {}
            Ok(decoded) => assert_ne!(decoded, trits),
        }
    }

    #[test]
    fn tb33_roundtrips_and_tail() {
        let samples: Vec<Vec<u8>> = vec![
            vec![0, 1],
            vec![1, 0, 1],
            vec![1, 0, 0, 0, 0, 1],
            (0..33).map(|i| (i % 2) as u8).chain([0, 1]).collect(),
            vec![1, 0, 1, 0, 1, 0, 1],
        ];
        for sample in samples {
            let encoded = tb_encode(&sample).unwrap();
            assert_eq!(encoded.len() % TB33_BLOCK_BYTES, 0);
            assert_eq!(tb_decode(&encoded).unwrap(), sample);
        }
        assert_eq!(tb_tail_count(1), 1);
        assert!(tb_tail_capacity() < (1u128 << 48));
    }

    #[test]
    fn adaptive_smallest_prefers_t5_on_tie() {
        let empty = words(&["10", "01"]);
        let carrier = encode_smallest(&empty).unwrap();
        assert_eq!(carrier.profile, Profile::T5);
        assert_eq!(carrier.extension, ".sens");
        assert_eq!(carrier.data, t5_encode(&empty).unwrap());

        let quote = words(&["10", "001", "00", "000", "01"]);
        let carrier = encode_smallest(&quote).unwrap();
        assert_eq!(carrier.profile, Profile::Frame3);
        assert_eq!(carrier.extension, ".senc");
        assert_eq!(carrier.data[0], FRAME_LABEL);
        assert_eq!(read_carrier(&carrier).unwrap(), quote);
        assert_eq!(decode_senc(&carrier.data).unwrap(), quote);
    }

    #[test]
    fn negatives_reject_unknown_and_noncanonical() {
        assert_eq!(decode_senc(&[]).unwrap_err(), SencError::CarrierShape);
        assert_eq!(
            decode_senc(&[0x00, 0x00]).unwrap_err(),
            SencError::UnknownLabel
        );
        let carrier = Carrier {
            profile: Profile::Frame3,
            data: vec![TB33_LABEL, 1, 2, 3, 4, 5, 6],
            extension: ".senc",
        };
        assert_eq!(read_carrier(&carrier).unwrap_err(), SencError::UnknownLabel);
        let empty_body = Carrier {
            profile: Profile::Frame3,
            data: vec![FRAME_LABEL],
            extension: ".senc",
        };
        assert!(read_carrier(&empty_body).is_err());
    }
}
