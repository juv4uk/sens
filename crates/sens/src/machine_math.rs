//! Оптимізовані математичні механізми для наближених `f64`.
//! Не створюють семантики SENS: точні D24+ / Rational сюди не переводяться.
//! Єдине джерело ASM використовується також у бенчмарках.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Backend {
    Scalar,
    Avx2Fma,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MathError {
    LengthMismatch { left: usize, right: usize },
}

#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
core::arch::global_asm!(include_str!("machine_math_skylake.S"), options(att_syntax));

#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
unsafe extern "C" {
    fn sens_dot_avx2(a: *const f64, b: *const f64, n: usize) -> f64;
}

#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
unsafe extern "C" {
    fn sens_i24_add_exact(left: i64, right: i64) -> i64;
    fn sens_i24_sub_exact(left: i64, right: i64) -> i64;
    fn sens_i24_mul_exact(left: i64, right: i64) -> i64;
    fn sens_i48_mul_exact(left: i64, right: i64, high: *mut i64) -> i64;
    fn sens_i64_divrem_exact(left: i64, right: i64, remainder: *mut i64) -> i64;
    fn sens_i96_add_exact(
        a_low: u64,
        a_high: i64,
        b_low: u64,
        b_high: i64,
        out_high: *mut i64,
    ) -> u64;
    fn sens_i96_sub_exact(
        a_low: u64,
        a_high: i64,
        b_low: u64,
        b_high: i64,
        out_high: *mut i64,
    ) -> u64;
    fn sens_u96_mul_exact(
        a_low: u64,
        a_high: u64,
        b_low: u64,
        b_high: u64,
        out_middle: *mut u64,
        out_high: *mut u64,
    ) -> u64;
    // Багатослівна арифметика: на відміну від двослівних D96, довільна довжина.
    fn sens_words_add_exact(left: *const u64, right: *const u64, output: *mut u64, words: usize);
    fn sens_words_sub_exact(left: *const u64, right: *const u64, output: *mut u64, words: usize);
    fn sens_words_mul_exact(left: *const u64, right: *const u64, output: *mut u64, words: usize);
    fn sens_words_divrem_u64(
        input: *const u64,
        output: *mut u64,
        words: usize,
        divisor: u64,
        remainder: *mut u64,
    );
}

/// Цілочисельний механізм для рівно двох НАЯВНИХ знакових слів D24.
///
/// Повертає математичний i64, але не обирає самовільно домен, не допускає
/// змішані D24/D48 і не представляє точної дробової семантики SENS.
/// Для D24 результат +, -, * завжди вкладається в знакові 48 бітів.
pub(crate) fn exact_i24_integer_op(operator: &str, left: i64, right: i64) -> Option<i64> {
    const MIN: i64 = -(1 << 23);
    const MAX: i64 = (1 << 23) - 1;
    if !(MIN..=MAX).contains(&left) || !(MIN..=MAX).contains(&right) {
        return None;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        // SAFETY: фіксований SysV ABI, параметри — числа у знаковій межі
        // D24. Навіть добуток крайніх D24 не перевищує знакові 48 бітів.
        // SIMD не потрібен: ADD/SUB/IMUL дозволені у звичайному x86-64.
        Some(unsafe {
            match operator {
                "+" => sens_i24_add_exact(left, right),
                "-" => sens_i24_sub_exact(left, right),
                "*" => sens_i24_mul_exact(left, right),
                _ => return None,
            }
        })
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    match operator {
        "+" => left.checked_add(right),
        "-" => left.checked_sub(right),
        "*" => left.checked_mul(right),
        _ => None,
    }
}

/// Точний D48 механізм. Доменний допуск/ріст D48->D96 виконує SENS.
/// 64-бітні ADD/SUB існуючого x86-ядра не усікають D48-суми;
/// IMUL використовує RDX:RAX та повертає 128 бітів через ABI-адаптер.
pub(crate) fn exact_i48_integer_op(op: &str, left: i64, right: i64) -> Option<i128> {
    const MIN: i64 = -(1_i64 << 47);
    const MAX: i64 = (1_i64 << 47) - 1;
    if !(MIN..=MAX).contains(&left) || !(MIN..=MAX).contains(&right) {
        return None;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        // SAFETY: D48 аргументи знакові, ABI System V, &mut high
        // зберігає старші 64 біти множення без втрати перенесення.
        Some(unsafe {
            match op {
                "+" => i128::from(sens_i24_add_exact(left, right)),
                "-" => i128::from(sens_i24_sub_exact(left, right)),
                "*" => {
                    let mut high = 0_i64;
                    let low = sens_i48_mul_exact(left, right, &mut high);
                    (i128::from(high) << 64) | i128::from(low as u64)
                }
                _ => return None,
            }
        })
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    match op {
        "+" => Some(i128::from(left) + i128::from(right)),
        "-" => Some(i128::from(left) - i128::from(right)),
        "*" => Some(i128::from(left) * i128::from(right)),
        _ => None,
    }
}

/// Точні знакові D96 +/−: 97-бітний результат без усічення й f64.
/// Результат i128 є лише носієм, вибір D96/D192 належить SENS.
pub(crate) fn exact_i96_add_sub(op: &str, left: i128, right: i128) -> Option<i128> {
    const MIN: i128 = -(1_i128 << 95);
    const MAX: i128 = (1_i128 << 95) - 1;
    if !(MIN..=MAX).contains(&left) || !(MIN..=MAX).contains(&right) {
        return None;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        let mut high = 0_i64;
        // SAFETY: обидва числа D96 знакові, System V ABI, &mut high
        // є чинним місцем для старшого машинного слова.
        let low = unsafe {
            match op {
                "+" => sens_i96_add_exact(
                    left as u64,
                    (left >> 64) as i64,
                    right as u64,
                    (right >> 64) as i64,
                    &mut high,
                ),
                "-" => sens_i96_sub_exact(
                    left as u64,
                    (left >> 64) as i64,
                    right as u64,
                    (right >> 64) as i64,
                    &mut high,
                ),
                _ => return None,
            }
        };
        Some((i128::from(high) << 64) | i128::from(low))
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    match op {
        "+" => left.checked_add(right),
        "-" => left.checked_sub(right),
        _ => None,
    }
}

/// Повні 192 біти множення двох БЕЗЗНАКОВИХ механічних модулів до 96 біт.
/// Підписи, ратифіковані домени й композиції НЕ вирішуються асемблером.
/// Результат: [молодші 64, середні 64, старші 64] без усічення.
pub(crate) fn exact_u96_multiply(a: u128, b: u128) -> Option<[u64; 3]> {
    if (a >> 96) != 0 || (b >> 96) != 0 {
        return None;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        let (mut middle, mut high) = (0_u64, 0_u64);
        // SAFETY: a,b мають не більше 96 бітів, SysV ABI,
        // обидва вихідні вказівники чинні й не перекриваються.
        let low = unsafe {
            sens_u96_mul_exact(
                a as u64,
                (a >> 64) as u64,
                b as u64,
                (b >> 64) as u64,
                &mut middle,
                &mut high,
            )
        };
        Some([low, middle, high])
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        let (a0, a1, b0, b1) = (a as u64 as u128, (a >> 64), b as u64 as u128, (b >> 64));
        let (p00, p01, p10, p11) = (a0 * b0, a0 * b1, a1 * b0, a1 * b1);
        let middle = (p00 >> 64) + u128::from(p01 as u64) + u128::from(p10 as u64);
        let high = (middle >> 64) + (p01 >> 64) + (p10 >> 64) + p11;
        Some([p00 as u64, middle as u64, high as u64])
    }
}

/// Точний багатослівний ADD/SUB з переносом, молодше слово перше.
///
/// Вхідні зрізи мусять мати однакову ненульову довжину. Це лише
/// механічне додавання/віднімання modulo 2^(64*N); верхній знаковий
/// резерв і ратифіковане розширення D192->D384 належать SENS.
pub(crate) fn exact_words_add_sub(operator: &str, left: &[u64], right: &[u64]) -> Option<Vec<u64>> {
    if left.is_empty() || left.len() != right.len() || !matches!(operator, "+" | "-") {
        return None;
    }
    let mut out = vec![0_u64; left.len()];
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    unsafe {
        // SAFETY: обидва входи та вихід містять рівно len чинних
        // елементів u64; вихідний буфер окремий; системний ABI x86-64.
        match operator {
            "+" => {
                sens_words_add_exact(left.as_ptr(), right.as_ptr(), out.as_mut_ptr(), left.len())
            }
            "-" => {
                sens_words_sub_exact(left.as_ptr(), right.as_ptr(), out.as_mut_ptr(), left.len())
            }
            _ => unreachable!(),
        }
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        let mut carry = 0_u64;
        for i in 0..left.len() {
            let (value, first) = if operator == "+" {
                left[i].overflowing_add(right[i])
            } else {
                left[i].overflowing_sub(right[i])
            };
            let (value, second) = if operator == "+" {
                value.overflowing_add(carry)
            } else {
                value.overflowing_sub(carry)
            };
            out[i] = value;
            carry = u64::from(first || second);
        }
    }
    Some(out)
}

/* Unsigned full-width product, 64*N × 64*N -> 128*N.
 * SENS alone admits exact Dn operands and selects Dn/D(2n).
 * Caller supplies equal nonempty little-endian limb arrays.
 * No rounding, truncation or float conversion. */
pub(crate) fn exact_words_mul_unsigned(left: &[u64], right: &[u64]) -> Option<Vec<u64>> {
    if left.is_empty() || left.len() != right.len() {
        return None;
    }
    let out_len = left.len().checked_mul(2)?;
    let mut output = vec![0_u64; out_len];
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    unsafe {
        // SAFETY: output is 2*n elements and never aliases inputs.
        // ASM preserves callee-saved registers under x86-64 System V ABI.
        sens_words_mul_exact(
            left.as_ptr(),
            right.as_ptr(),
            output.as_mut_ptr(),
            left.len(),
        );
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        for (i, &a) in left.iter().enumerate() {
            let mut carry = 0_u128;
            for (j, &b) in right.iter().enumerate() {
                let k = i + j;
                let part = u128::from(a) * u128::from(b) + u128::from(output[k]) + carry;
                output[k] = part as u64;
                carry = part >> 64;
            }
            output[i + left.len()] = carry as u64;
        }
    }
    Some(output)
}

/// Точна механічна частка та остача багатослівного БЕЗЗНАКОВОГО числа.
/// Молодше слово перше, довжина ненульова; рішення про Dn та RATIO — за SENS.
pub(crate) fn exact_words_div_rem_u64(input: &[u64], divisor: u64) -> Option<(Vec<u64>, u64)> {
    if input.is_empty() || divisor == 0 {
        return None;
    }
    let mut output = vec![0_u64; input.len()];
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        let mut remainder = 0_u64;
        // SAFETY: окремі буфери рівної довжини, дільник >0;
        // старша половина перед DIVQ завжди строго менша за дільник.
        unsafe {
            sens_words_divrem_u64(
                input.as_ptr(),
                output.as_mut_ptr(),
                input.len(),
                divisor,
                &mut remainder,
            );
        }
        Some((output, remainder))
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        let mut remainder = 0_u128;
        let d = u128::from(divisor);
        for i in (0..input.len()).rev() {
            let numerator = (remainder << 64) | u128::from(input[i]);
            output[i] = (numerator / d) as u64;
            remainder = numerator % d;
        }
        Some((output, remainder as u64))
    }
}

/// Точне беззнакове ділення довільної кількості 64-бітних слів.
/// Дані — little-endian; нульовий дільник і різні довжини заборонені.
/// Дільник в одному слові: раніше перевірений ASM DIVQ.
/// Ширший дільник: відновлювальне ділення з наявним ASM SBB.
/// Жодного фіксованого мовного Dn чи округлення цей механізм не створює.
pub(crate) fn exact_words_div_rem_unsigned(
    input: &[u64],
    divisor: &[u64],
) -> Option<(Vec<u64>, Vec<u64>)> {
    if input.is_empty() || input.len() != divisor.len() {
        return None;
    }
    let n = input.len();
    let highest = divisor.iter().rposition(|&word| word != 0)?;
    if highest == 0 {
        let (q, r) = exact_words_div_rem_u64(input, divisor[0])?;
        let mut remainder = vec![0_u64; n];
        remainder[0] = r;
        return Some((q, remainder));
    }

    let count = n.checked_mul(64)?;
    let mut quotient = vec![0_u64; n];
    let mut remainder = vec![0_u64; n.checked_add(1)?];
    let mut extended_divisor = divisor.to_vec();
    extended_divisor.push(0);

    // Після кожної ітерації remainder < divisor. Одне резервне
    // слово гарантує відсутність усічення при зсуві.
    for bit in (0..count).rev() {
        let mut carry = (input[bit / 64] >> (bit % 64)) & 1;
        for limb in &mut remainder {
            let next = *limb >> 63;
            *limb = (*limb << 1) | carry;
            carry = next;
        }
        if remainder.iter().rev().cmp(extended_divisor.iter().rev()) != std::cmp::Ordering::Less {
            remainder = exact_words_add_sub("-", &remainder, &extended_divisor)?;
            quotient[bit / 64] |= 1_u64 << (bit % 64);
        }
    }
    if remainder[n] != 0 {
        return None;
    }
    remainder.pop();
    Some((quotient, remainder))
}

/// Точна цілочисельна частка двох явно допущених знакових D24/D48.
/// Не зараховує ділення з остачею: воно йде до канонічного RATIO у SENS.
/// Навіть D48 minimum/-1 вміщується в i64, але домен виходу має розширитися.
pub(crate) fn exact_small_integer_quotient(width: usize, a: i64, b: i64) -> Option<i64> {
    if !matches!(width, 24 | 48) {
        return None;
    }
    let bound = 1_i64 << (width - 1);
    if !(-bound..=bound - 1).contains(&a) || !(-bound..=bound - 1).contains(&b) || b == 0 {
        return None;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        // SAFETY: b != 0, обидва операнди <= 48 знакових бітів,
        // тому IDIV не переповнить i64, &mut remainder придатний для запису.
        let mut remainder = 0_i64;
        let quotient = unsafe { sens_i64_divrem_exact(a, b, &mut remainder) };
        (remainder == 0).then_some(quotient)
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        let quotient = a.checked_div(b)?;
        (a % b == 0).then_some(quotient)
    }
}

/// Вибір механізму за ISA процесора, а не ратифікація мовної функції.
pub fn backend() -> Backend {
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    if std::is_x86_feature_detected!("avx2") && std::is_x86_feature_detected!("fma") {
        return Backend::Avx2Fma;
    }
    Backend::Scalar
}

fn scalar_dot(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b.iter()).fold(0.0, |sum, (x, y)| sum + x * y)
}

fn dot_same_length(a: &[f64], b: &[f64]) -> f64 {
    if a.is_empty() {
        return 0.0;
    }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    if backend() == Backend::Avx2Fma {
        // SAFETY: AVX2/FMA перевірено. Довжини рівні, усі елементи
        // доступні для читання, ASM зберігає x86-64 System V ABI.
        return unsafe { sens_dot_avx2(a.as_ptr(), b.as_ptr(), a.len()) };
    }
    scalar_dot(a, b)
}

/// Скалярний добуток наближених чисел; для різних довжин — явна помилка.
pub fn dot_f64(a: &[f64], b: &[f64]) -> Result<f64, MathError> {
    if a.len() != b.len() {
        return Err(MathError::LengthMismatch {
            left: a.len(),
            right: b.len(),
        });
    }
    Ok(dot_same_length(a, b))
}

/// Квадрат евклідової норми наближеного вектора.
pub fn squared_norm_f64(values: &[f64]) -> f64 {
    dot_same_length(values, values)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() <= 1e-10 * (expected.abs() + 1.0),
            "actual={actual:?}, expected={expected:?}, backend={:?}",
            backend()
        );
    }

    #[test]
    fn empty_signed_and_length_mismatch() {
        assert_eq!(dot_f64(&[], &[]), Ok(0.0));
        assert_eq!(squared_norm_f64(&[]), 0.0);
        assert_eq!(
            dot_f64(&[1.0, 2.0], &[3.0]),
            Err(MathError::LengthMismatch { left: 2, right: 1 })
        );
        close(dot_f64(&[2.0, -3.0], &[4.0, 5.0]).unwrap(), -7.0);
        close(squared_norm_f64(&[3.0, 4.0]), 25.0);
    }

    #[test]
    fn avx2_tails_and_unaligned_slices() {
        for n in [1, 2, 3, 7, 15, 16, 17, 31, 32, 33, 65, 257, 1024] {
            let left: Vec<f64> = (0..n + 1)
                .map(|i| ((i % 97) as f64 - 44.0) * 0.003)
                .collect();
            let right: Vec<f64> = (0..n + 1)
                .map(|i| ((i % 89) as f64 + 1.0) * 0.002)
                .collect();
            let a = &left[1..];
            let b = &right[..n];
            close(dot_f64(a, b).unwrap(), scalar_dot(a, b));
            close(squared_norm_f64(a), scalar_dot(a, a));
        }
    }

    #[test]
    fn backend_detected_before_invoking_avx2() {
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        assert_eq!(
            backend() == Backend::Avx2Fma,
            std::is_x86_feature_detected!("avx2") && std::is_x86_feature_detected!("fma")
        );
        #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
        assert_eq!(backend(), Backend::Scalar);
    }
    #[test]
    fn d24_assembly_exact_signed_boundaries_and_rejects_bad_inputs() {
        const MIN: i64 = -(1 << 23);
        const MAX: i64 = (1 << 23) - 1;
        for a in [MIN, MIN + 1, -1, 0, 1, MAX - 1, MAX] {
            for b in [MIN, MIN + 1, -1, 0, 1, MAX - 1, MAX] {
                assert_eq!(exact_i24_integer_op("+", a, b), Some(a + b), "sum {a} {b}");
                assert_eq!(
                    exact_i24_integer_op("-", a, b),
                    Some(a - b),
                    "difference {a} {b}"
                );
                assert_eq!(
                    exact_i24_integer_op("*", a, b),
                    Some(a * b),
                    "product {a} {b}"
                );
            }
        }
        assert_eq!(exact_i24_integer_op("+", MAX + 1, 0), None);
        assert_eq!(exact_i24_integer_op("*", MIN - 1, 1), None);
        assert_eq!(exact_i24_integer_op("/", 2, 2), None);
        assert_eq!(exact_i24_integer_op("=", 2, 2), None);
    }

    #[test]
    fn d24_assembly_matches_checked_scalar_across_seeded_samples() {
        let mut state = 0x9e37_79b9_u64;
        for _ in 0..4096 {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let a = ((state & 0xff_ffff) as i64) - (1 << 23);
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let b = ((state & 0xff_ffff) as i64) - (1 << 23);
            assert_eq!(exact_i24_integer_op("+", a, b), a.checked_add(b));
            assert_eq!(exact_i24_integer_op("-", a, b), a.checked_sub(b));
            assert_eq!(exact_i24_integer_op("*", a, b), a.checked_mul(b));
        }
    }

    #[test]
    fn d48_asm_exact_signed_boundaries_and_wide_product() {
        const MIN: i64 = -(1_i64 << 47);
        const MAX: i64 = (1_i64 << 47) - 1;
        for a in [MIN, MIN + 1, -1, 0, 1, MAX - 1, MAX] {
            for b in [MIN, -1, 0, 1, MAX] {
                assert_eq!(
                    exact_i48_integer_op("+", a, b),
                    Some(i128::from(a) + i128::from(b))
                );
                assert_eq!(
                    exact_i48_integer_op("-", a, b),
                    Some(i128::from(a) - i128::from(b))
                );
                assert_eq!(
                    exact_i48_integer_op("*", a, b),
                    Some(i128::from(a) * i128::from(b))
                );
            }
        }
        assert_eq!(exact_i48_integer_op("*", MIN, MIN), Some(1_i128 << 94));
        assert_eq!(exact_i48_integer_op("+", MAX + 1, 0), None);
        assert_eq!(exact_i48_integer_op("*", MIN - 1, 1), None);
        assert_eq!(exact_i48_integer_op("/", 2, 1), None);
    }

    #[test]
    fn d48_asm_matches_i128_oracle_in_4096_cases() {
        let mut seed = 0x9e37_79b9_82a1_c365_u64;
        for _ in 0..4096 {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let a = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let b = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            for (op, value) in [
                ("+", i128::from(a) + i128::from(b)),
                ("-", i128::from(a) - i128::from(b)),
                ("*", i128::from(a) * i128::from(b)),
            ] {
                assert_eq!(exact_i48_integer_op(op, a, b), Some(value));
            }
        }
    }
    #[test]
    fn d96_asm_signed_boundaries_and_carry_borrow() {
        const MIN: i128 = -(1_i128 << 95);
        const MAX: i128 = (1_i128 << 95) - 1;
        for a in [MIN, MIN + 1, -1, 0, 1, MAX - 1, MAX] {
            for b in [MIN, -1, 0, 1, MAX] {
                assert_eq!(exact_i96_add_sub("+", a, b), Some(a + b));
                assert_eq!(exact_i96_add_sub("-", a, b), Some(a - b));
            }
        }
        assert_eq!(exact_i96_add_sub("+", MAX, 1), Some(1_i128 << 95));
        assert_eq!(exact_i96_add_sub("-", MIN, 1), Some(MIN - 1));
        assert_eq!(exact_i96_add_sub("+", MAX + 1, 0), None);
        assert_eq!(exact_i96_add_sub("-", MIN - 1, 0), None);
        assert_eq!(exact_i96_add_sub("*", 2, 3), None);
    }

    #[test]
    fn d96_asm_matches_independent_i128_seeded_oracle() {
        let mut state = 0x63b9_8af5_1d0c_27e4_u64;
        let mut next = || {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state
        };
        for _ in 0..4096 {
            let left = (u128::from(next()) << 32) | u128::from(next() & 0xffff_ffff);
            let right = (u128::from(next()) << 32) | u128::from(next() & 0xffff_ffff);
            let a = ((left as i128) << 32) >> 32;
            let b = ((right as i128) << 32) >> 32;
            assert_eq!(exact_i96_add_sub("+", a, b), a.checked_add(b));
            assert_eq!(exact_i96_add_sub("-", a, b), a.checked_sub(b));
        }
    }
    #[test]
    fn d96_full_unsigned_product_retains_all_192_bits() {
        const MAX: u128 = (1_u128 << 96) - 1;
        assert_eq!(exact_u96_multiply(0, MAX), Some([0, 0, 0]));
        assert_eq!(
            exact_u96_multiply(1, MAX),
            Some([u64::MAX, u32::MAX as u64, 0])
        );
        assert_eq!(
            exact_u96_multiply(1_u128 << 95, 1_u128 << 95),
            Some([0, 0, 1_u64 << 62])
        );
        assert_eq!(
            exact_u96_multiply(MAX, MAX),
            Some([1, 0xffff_fffe_0000_0000, u64::MAX])
        );
        assert_eq!(exact_u96_multiply(1_u128 << 96, 1), None);
    }

    #[test]
    fn d96_multiply_exact_matches_independent_u128_oracle() {
        let mut state = 0x9e37_41c6_f02a_b8d5_u64;
        for _ in 0..4096 {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let a = u128::from(state & ((1_u64 << 60) - 1));
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let b = u128::from(state & ((1_u64 << 60) - 1));
            let result = a * b;
            let limbs = exact_u96_multiply(a, b).unwrap();
            assert_eq!(limbs, [result as u64, (result >> 64) as u64, 0]);
        }
    }

    #[test]
    fn wide_limb_asm_retains_carries_borrows_and_sign_extensions() {
        for len in [1, 2, 3, 4, 6, 12] {
            let mut a = vec![u64::MAX; len];
            let mut b = vec![0_u64; len];
            b[0] = 1;
            assert_eq!(exact_words_add_sub("+", &a, &b), Some(vec![0; len]));
            assert_eq!(
                exact_words_add_sub("-", &vec![0; len], &b),
                Some(vec![u64::MAX; len])
            );
            a[0] = 0;
            let diff = exact_words_add_sub("-", &a, &b).unwrap();
            assert_eq!(diff[0], u64::MAX);
            assert!(diff[1..]
                .iter()
                .all(|&x| x == u64::MAX - 1 || x == u64::MAX));
        }
        assert_eq!(exact_words_add_sub("+", &[], &[]), None);
        assert_eq!(exact_words_add_sub("-", &[1], &[1, 2]), None);
        assert_eq!(exact_words_add_sub("*", &[2], &[3]), None);
    }

    #[test]
    fn wide_limb_asm_matches_independent_u128_oracle() {
        let mut seed = 0x15be_0297_a486_cdf1_u64;
        for _ in 0..4096 {
            let mut next = || {
                seed ^= seed << 13;
                seed ^= seed >> 7;
                seed ^= seed << 17;
                seed
            };
            let (a0, a1, b0, b1) = (next(), next(), next(), next());
            let a = u128::from(a0) | (u128::from(a1) << 64);
            let b = u128::from(b0) | (u128::from(b1) << 64);
            let sum = exact_words_add_sub("+", &[a0, a1], &[b0, b1]).unwrap();
            let sub = exact_words_add_sub("-", &[a0, a1], &[b0, b1]).unwrap();
            let expect_sum = a.wrapping_add(b);
            let expect_sub = a.wrapping_sub(b);
            assert_eq!(sum, [expect_sum as u64, (expect_sum >> 64) as u64]);
            assert_eq!(sub, [expect_sub as u64, (expect_sub >> 64) as u64]);
        }
    }

    #[test]
    fn multiword_asm_multiplication_preserves_full_width() {
        for n in [1, 2, 3, 4, 6, 12] {
            let max = vec![u64::MAX; n];
            let zero = vec![0_u64; n];
            let one = [vec![1_u64], vec![0; n.saturating_sub(1)]].concat();
            assert_eq!(exact_words_mul_unsigned(&max, &zero), Some(vec![0; 2 * n]));
            assert_eq!(
                exact_words_mul_unsigned(&max, &one),
                Some([max.clone(), vec![0; n]].concat())
            );
            // Алгебраїчна тотожність (2^(64*n)-1)^2 = 2^(128*n)-2^(64*n+1)+1.
            // У молодшому слові 1, у слові n значення MAX-1,
            // у решті старших слів MAX. Для n=1 найстарше саме MAX-1.
            let mut expected = vec![0_u64; 2 * n];
            expected[0] = 1;
            expected[n] = u64::MAX - 1;
            expected[n + 1..].fill(u64::MAX);
            assert_eq!(
                exact_words_mul_unsigned(&max, &max),
                Some(expected),
                "повний квадрат (2^(64*{n})-1)"
            );
        }
        assert_eq!(exact_words_mul_unsigned(&[], &[]), None);
        assert_eq!(exact_words_mul_unsigned(&[1], &[1, 2]), None);
    }

    #[test]
    fn multiword_asm_matches_independent_schoolbook_oracle() {
        let mut seed = 0x9e37_79b9_82a1_c365_u64;
        for n in [1, 2, 3, 4, 6, 12] {
            for repeat in 0..4096 {
                let mut left = vec![0_u64; n];
                let mut right = vec![0_u64; n];
                for i in 0..n {
                    seed ^= seed << 13;
                    seed ^= seed >> 7;
                    seed ^= seed << 17;
                    left[i] = if repeat % 11 == 0 { u64::MAX } else { seed };
                    seed ^= seed << 13;
                    seed ^= seed >> 7;
                    seed ^= seed << 17;
                    right[i] = if repeat % 13 == 0 { u64::MAX } else { seed };
                }
                let mut oracle = vec![0_u64; 2 * n];
                for i in 0..n {
                    let mut carry = 0_u128;
                    for j in 0..n {
                        let k = i + j;
                        let value = u128::from(left[i]) * u128::from(right[j])
                            + u128::from(oracle[k])
                            + carry;
                        oracle[k] = value as u64;
                        carry = value >> 64;
                    }
                    oracle[i + n] = carry as u64;
                }
                assert_eq!(
                    exact_words_mul_unsigned(&left, &right),
                    Some(oracle),
                    "words={n} repetition={repeat}"
                );
            }
        }
    }
    #[test]
    fn exact_idiv_boundary_and_fraction_rejection() {
        for width in [24_usize, 48] {
            let bound = 1_i64 << (width - 1);
            let xs = [-bound, -bound + 1, -17, -3, -1, 0, 1, 3, 17, bound - 1];
            for a in xs {
                for b in xs {
                    let expected = if b == 0 || a % b != 0 {
                        None
                    } else {
                        Some(a / b)
                    };
                    assert_eq!(
                        exact_small_integer_quotient(width, a, b),
                        expected,
                        "D{width} {a}/{b}"
                    );
                }
            }
            assert_eq!(exact_small_integer_quotient(width, -bound, -1), Some(bound));
            assert_eq!(exact_small_integer_quotient(width, 0, 7), Some(0));
            assert_eq!(exact_small_integer_quotient(width, 1, 0), None);
            assert_eq!(exact_small_integer_quotient(width, bound, 1), None);
            assert_eq!(exact_small_integer_quotient(width, -bound - 1, 1), None);
        }
        assert_eq!(exact_small_integer_quotient(96, 10, 2), None);
    }

    #[test]
    fn exact_idiv_matches_independent_integer_oracle_4096_cases() {
        let mut seed = 0xd8a7_6f59_c213_4e0b_u64;
        for _ in 0..4096 {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let a = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let b = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            let expected = if b == 0 || a % b != 0 {
                None
            } else {
                Some(a / b)
            };
            assert_eq!(exact_small_integer_quotient(48, a, b), expected);
        }
    }
    #[test]
    fn full_width_division_keeps_all_bits_and_rejects_bad_inputs() {
        assert_eq!(exact_words_div_rem_unsigned(&[], &[]), None);
        assert_eq!(exact_words_div_rem_unsigned(&[1], &[1, 0]), None);
        assert_eq!(exact_words_div_rem_unsigned(&[1, 2], &[0, 0]), None);
        for n in [2_usize, 3, 6, 12] {
            let mut divisor = vec![0_u64; n];
            divisor[n - 1] = 1;
            divisor[0] = 3;
            let mut one = vec![0_u64; n];
            one[0] = 1;
            let zero = vec![0_u64; n];
            assert_eq!(
                exact_words_div_rem_unsigned(&divisor, &divisor),
                Some((one.clone(), zero.clone()))
            );
            assert_eq!(
                exact_words_div_rem_unsigned(&one, &divisor),
                Some((zero.clone(), one.clone()))
            );
            assert_eq!(
                exact_words_div_rem_unsigned(&zero, &divisor),
                Some((zero.clone(), zero))
            );
            let dividend = vec![u64::MAX; n];
            let (q, r) = exact_words_div_rem_unsigned(&dividend, &divisor).unwrap();
            assert_eq!(
                r.iter().rev().cmp(divisor.iter().rev()),
                std::cmp::Ordering::Less
            );
            // Алгебраїчна тотожність незалежно від конкретного алгоритму:
            // dividend = quotient * divisor + remainder.
            let product = exact_words_mul_unsigned(&q, &divisor).unwrap();
            let mut rem = vec![0_u64; 2 * n];
            rem[..n].copy_from_slice(&r);
            let reconstructed = exact_words_add_sub("+", &product, &rem).unwrap();
            assert_eq!(&reconstructed[..n], dividend.as_slice());
            assert!(reconstructed[n..].iter().all(|&word| word == 0));
        }
    }

    #[test]
    fn full_width_division_matches_independent_u128_oracle() {
        let mut seed = 0x4f79_1ab3_8052_dc6e_u64;
        for case in 0..4096 {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let a0 = seed;
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let a1 = seed;
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let d0 = seed;
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let d1 = seed | 1; // справжній широкий ненульовий дільник
            let numerator = (u128::from(a1) << 64) | u128::from(a0);
            let denominator = (u128::from(d1) << 64) | u128::from(d0);
            let (q, r) = exact_words_div_rem_unsigned(&[a0, a1], &[d0, d1]).unwrap();
            let expected_q = numerator / denominator;
            let expected_r = numerator % denominator;
            assert_eq!(
                q,
                vec![expected_q as u64, (expected_q >> 64) as u64],
                "case {case}"
            );
            assert_eq!(
                r,
                vec![expected_r as u64, (expected_r >> 64) as u64],
                "case {case}"
            );
        }
        assert_eq!(
            exact_words_div_rem_unsigned(&[u64::MAX, 1], &[3, 0]),
            exact_words_div_rem_u64(&[u64::MAX, 1], 3).map(|(q, r)| (q, vec![r, 0]))
        );
    }

    #[test]
    fn wide_divrem_reconstructs_every_bit_and_rejects_zero_divisor() {
        assert_eq!(exact_words_div_rem_u64(&[], 1), None);
        assert_eq!(exact_words_div_rem_u64(&[42], 0), None);
        for n in [1, 2, 3, 6, 12] {
            let max = vec![u64::MAX; n];
            for divisor in [1_u64, 2, 3, 17, u32::MAX as u64, u64::MAX] {
                let (quot, rem) = exact_words_div_rem_u64(&max, divisor).unwrap();
                assert!(rem < divisor);
                let mut carry = u128::from(rem);
                for i in 0..n {
                    let product = u128::from(quot[i]) * u128::from(divisor) + carry;
                    assert_eq!(product as u64, max[i]);
                    carry = product >> 64;
                }
                assert_eq!(carry, 0);
            }
        }
    }

    #[test]
    fn wide_divrem_matches_u128_oracle_in_seeded_cases() {
        let mut seed = 0x35cd_a871_4eb9_f206_u64;
        for n in [1, 2, 3, 6, 12] {
            for _ in 0..1024 {
                let mut input = Vec::new();
                for _ in 0..n {
                    seed ^= seed << 13;
                    seed ^= seed >> 7;
                    seed ^= seed << 17;
                    input.push(seed);
                }
                seed ^= seed << 13;
                seed ^= seed >> 7;
                seed ^= seed << 17;
                let divisor = seed | 1;
                let (quot, rem) = exact_words_div_rem_u64(&input, divisor).unwrap();
                assert!(rem < divisor);
                let mut carry = u128::from(rem);
                for i in 0..n {
                    let product = u128::from(quot[i]) * u128::from(divisor) + carry;
                    assert_eq!(product as u64, input[i], "n={n}, limb={i}");
                    carry = product >> 64;
                }
                assert_eq!(carry, 0);
                if n <= 2 {
                    let value = u128::from(input[0])
                        | if n == 2 {
                            u128::from(input[1]) << 64
                        } else {
                            0
                        };
                    let expect = value / u128::from(divisor);
                    assert_eq!(quot[0], expect as u64);
                    if n == 2 {
                        assert_eq!(quot[1], (expect >> 64) as u64);
                    }
                    assert_eq!(rem, (value % u128::from(divisor)) as u64);
                }
            }
        }
    }
}
