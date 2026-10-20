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
}
