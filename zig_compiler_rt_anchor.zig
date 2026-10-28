// Окремий compilation unit для compiler-rt: тут немає libc-імпортів.
// Zig 0.16 окремо архівує runtime і native C transport без втрати stack probes.
pub const sens_compiler_rt_anchor = true;
