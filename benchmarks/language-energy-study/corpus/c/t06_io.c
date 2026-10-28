/* T06-io — C implementation for ENERGY-02 corpus (#6287).
 *
 * Functional unit matches parity_check.ref_T06:
 *   payload = concat("line-%06d\n" for i in 0..lines-1)
 *   output  = "{utf8_byte_len}:{line_count}"
 *
 * Input via environment: TASK_ID=T06-io, TASK_LINES=<positive int>.
 * Exactly one stdout line on success; exit 2 on bad input.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

int main(void) {
    const char *id = getenv("TASK_ID");
    const char *lines_env = getenv("TASK_LINES");
    char *end = NULL;
    long lines;
    long long byte_len = 0;
    long i;

    if (!id || strcmp(id, "T06-io") != 0) {
        fprintf(stderr, "TASK_ID must be T06-io\n");
        return 2;
    }
    if (!lines_env || !*lines_env) {
        fprintf(stderr, "TASK_LINES required\n");
        return 2;
    }
    errno = 0;
    lines = strtol(lines_env, &end, 10);
    if (errno || end == lines_env || *end != '\0' || lines < 1 || lines > 10000000L) {
        fprintf(stderr, "TASK_LINES invalid\n");
        return 2;
    }

    /* Each line is exactly "line-" + 6 digits + "\n" = 12 bytes (ASCII). */
    for (i = 0; i < lines; i++) {
        char buf[32];
        int n = snprintf(buf, sizeof buf, "line-%06ld\n", i);
        if (n < 0 || (size_t)n >= sizeof buf) {
            fprintf(stderr, "format failed\n");
            return 2;
        }
        byte_len += n;
    }

    printf("%lld:%ld\n", byte_len, lines);
    return 0;
}
