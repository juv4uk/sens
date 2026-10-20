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
core::arch::global_asm!(
    include_str!("machine_math_skylake.S"),
    options(att_syntax)
);

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
        return Some(unsafe {
            match operator {
                "+" => sens_i24_add_exact(left, right),
                "-" => sens_i24_sub_exact(left, right),
                "*" => sens_i24_mul_exact(left, right),
                _ => return None,
            }
        });
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
    if !(MIN..=MAX).contains(&left) || !(MIN..=MAX).contains(&right) { return None; }
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    {
        // SAFETY: D48 аргументи знакові, ABI System V, &mut high
        // зберігає старші 64 біти множення без втрати перенесення.
        return Some(unsafe {
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
        });
    }
    #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
    match op {
        "+" => Some(i128::from(left) + i128::from(right)),
        "-" => Some(i128::from(left) - i128::from(right)),
        "*" => Some(i128::from(left) * i128::from(right)),
        _ => None,
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
        return Err(MathError::LengthMismatch { left: a.len(), right: b.len() });
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
        assert!((actual - expected).abs() <= 1e-10 * (expected.abs() + 1.0),
            "actual={actual:?}, expected={expected:?}, backend={:?}", backend());
    }

    #[test]
    fn empty_signed_and_length_mismatch() {
        assert_eq!(dot_f64(&[], &[]), Ok(0.0));
        assert_eq!(squared_norm_f64(&[]), 0.0);
        assert_eq!(dot_f64(&[1.0, 2.0], &[3.0]),
                   Err(MathError::LengthMismatch { left: 2, right: 1 }));
        close(dot_f64(&[2.0, -3.0], &[4.0, 5.0]).unwrap(), -7.0);
        close(squared_norm_f64(&[3.0, 4.0]), 25.0);
    }

    #[test]
    fn avx2_tails_and_unaligned_slices() {
        for n in [1, 2, 3, 7, 15, 16, 17, 31, 32, 33, 65, 257, 1024] {
            let left: Vec<f64> = (0..n + 1).map(|i| ((i % 97) as f64 - 44.0) * 0.003).collect();
            let right: Vec<f64> = (0..n + 1).map(|i| ((i % 89) as f64 + 1.0) * 0.002).collect();
            let a = &left[1..];
            let b = &right[..n];
            close(dot_f64(a, b).unwrap(), scalar_dot(a, b));
            close(squared_norm_f64(a), scalar_dot(a, a));
        }
    }

    #[test]
    fn backend_detected_before_invoking_avx2() {
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        assert_eq!(backend() == Backend::Avx2Fma,
                   std::is_x86_feature_detected!("avx2") && std::is_x86_feature_detected!("fma"));
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
                assert_eq!(exact_i24_integer_op("-", a, b), Some(a - b), "difference {a} {b}");
                assert_eq!(exact_i24_integer_op("*", a, b), Some(a * b), "product {a} {b}");
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
                assert_eq!(exact_i48_integer_op("+", a, b), Some(i128::from(a) + i128::from(b)));
                assert_eq!(exact_i48_integer_op("-", a, b), Some(i128::from(a) - i128::from(b)));
                assert_eq!(exact_i48_integer_op("*", a, b), Some(i128::from(a) * i128::from(b)));
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
            seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17;
            let a = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17;
            let b = ((seed & ((1_u64 << 48) - 1)) as i64) - (1_i64 << 47);
            for (op, value) in [("+", i128::from(a) + i128::from(b)),
                                ("-", i128::from(a) - i128::from(b)),
                                ("*", i128::from(a) * i128::from(b))] {
                assert_eq!(exact_i48_integer_op(op, a, b), Some(value));
            }
        }
    }
}
