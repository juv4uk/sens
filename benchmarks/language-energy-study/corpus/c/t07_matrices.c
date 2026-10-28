/* ENERGY-02 T07: independent C11 matrix multiplication parity witness.
 * No SENS-semantic oracle and no energy/time measurement.
 * Exact unit: form A[i,j] = ((i+j)%7 == 0 ? 0.5 : 1.0), compute A*A
 * using (i,j,k) traversal, and print the sum of all product entries.
 */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TASK_NAME "T07-matrices"
#define MAX_DIMENSION 256u

static int reject(const char *reason) {
    fprintf(stderr, "T07_INVALID_INPUT: %s\n", reason);
    return 2;
}

static int read_dimension(const char *text, size_t *result) {
    if (text == NULL || *text == '\0') return 0;
    /* strtoull accepts leading whitespace and a sign; TASK_N does not. */
    for (const unsigned char *p = (const unsigned char *)text; *p; ++p) {
        if (*p < '0' || *p > '9') return 0;
    }
    errno = 0;
    char *end = NULL;
    unsigned long long value = strtoull(text, &end, 10);
    if (errno == ERANGE || *end != '\0' || value == 0 ||
        value > MAX_DIMENSION) return 0;
    *result = (size_t)value;
    return 1;
}

int main(void) {
    const char *task = getenv("TASK_ID");
    if (task == NULL || strcmp(task, TASK_NAME) != 0)
        return reject("TASK_ID must be T07-matrices");

    size_t n = 0;
    if (!read_dimension(getenv("TASK_N"), &n))
        return reject("TASK_N must be a decimal integer in 1..256");

    if (n > SIZE_MAX / n || n * n > SIZE_MAX / sizeof(double))
        return reject("matrix allocation exceeds size_t");
    size_t elements = n * n;
    double *matrix = malloc(elements * sizeof(*matrix));
    if (matrix == NULL) return reject("cannot allocate matrix");

    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            matrix[i * n + j] = ((i + j) % 7u == 0u) ? 0.5 : 1.0;
        }
    }

    double total = 0.0;
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            double cell = 0.0;
            for (size_t k = 0; k < n; ++k) {
                cell += matrix[i * n + k] * matrix[k * n + j];
            }
            total += cell;
        }
    }
    free(matrix);
    if (printf("%.12f\n", total) < 0) return reject("stdout write failed");
    return 0;
}
