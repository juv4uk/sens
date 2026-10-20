/* Скалярний добуток для порівняння реалізацій: С, Fortran, Rust.
 * Вхідний масив змінюється перед кожним добутком, щоб не вилучити роботу. */
#include <stdio.h>
#include <stdlib.h>

enum { N = 65536, ROUNDS = 2048 };

int main(void) {
    double *a = malloc(sizeof(double) * N);
    double *b = malloc(sizeof(double) * N);
    if (!a || !b) {
        free(a);
        free(b);
        return 2;
    }
    for (int i = 0; i < N; i++) {
        a[i] = (double)(i % 97 + 1) * 0.001;
        b[i] = (double)(i % 89 + 1) * 0.002;
    }
    double total = 0.0;
    for (int round = 0; round < ROUNDS; round++) {
        a[round % N] += 1.0e-9;
        double dot = 0.0;
        for (int i = 0; i < N; i++) {
            dot += a[i] * b[i];
        }
        total += dot;
    }
    printf("%.16e\n", total);
    free(a);
    free(b);
    return 0;
}
