! Скалярний добуток: ті самі дані та кількість операцій, що у С і Rust.
! DOT_PRODUCT — звичний для Fortran математичний інструмент.
program language_fit_dot
  use, intrinsic :: iso_fortran_env, only: real64
  implicit none
  integer, parameter :: n = 65536, rounds = 2048
  real(real64), allocatable :: a(:), b(:)
  real(real64) :: total
  integer :: i, round

  allocate(a(n), b(n))
  do i = 1, n
    a(i) = real(mod(i - 1, 97) + 1, real64) * 0.001_real64
    b(i) = real(mod(i - 1, 89) + 1, real64) * 0.002_real64
  end do

  total = 0.0_real64
  do round = 0, rounds - 1
    a(mod(round, n) + 1) = a(mod(round, n) + 1) + 1.0e-9_real64
    total = total + dot_product(a, b)
  end do
  write(*, '(ES24.16E3)') total
end program language_fit_dot
