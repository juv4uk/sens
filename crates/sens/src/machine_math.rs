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
    // sens_dot_scalar експортований у machine_math_skylake.S (.globl), але
    // досі не був оголошений тут — тому скалярний шлях ішов чистим Rust-фолдом,
    // а написаний вручну SSE2-асемблер просто не виконувався.
    fn sens_dot_scalar(a: *const f64, b: *const f64, n: usize) -> f64;
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

/// Скалярний добуток. На x86_64/linux іде через написаний вручну SSE2-асемблер
/// `sens_dot_scalar` — саме для нього він і був написаний. Rust-фолд лишається
/// запасним шляхом для інших цілей.
fn scalar_dot(a: &[f64], b: &[f64]) -> f64 {
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        if a.is_empty() {
            return 0.0;
        }
        // SAFETY: довжини рівні, елементи доступні для читання,
        // ASM зберігає x86-64 System V ABI.
        return unsafe { sens_dot_scalar(a.as_ptr(), b.as_ptr(), a.len()) };
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    {
        a.iter().zip(b.iter()).fold(0.0, |sum, (x, y)| sum + x * y)
    }
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

