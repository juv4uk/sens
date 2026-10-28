/* Physical byte-copy; no interpretation of SENS source or laws. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    errno = 0;
    char *end = NULL;
    unsigned long long copies = strtoull(argv[2], &end, 10);
    if (errno || !end || *end != '\0' || copies < 1 || copies > 5000000ULL) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file) return 2;
    if (fseek(file, 0, SEEK_END) != 0) return 2;
    long length = ftell(file);
    if (length <= 0 || length > 64L * 1024L * 1024L) return 2;
    if (fseek(file, 0, SEEK_SET) != 0) return 2;
    size_t size = (size_t) length;
    unsigned char *source = malloc(size), *dest = malloc(size);
    if (!source || !dest) return 2;
    if (fread(source, 1, size, file) != size) return 2;
    fclose(file);
    volatile unsigned char *observed_bytes = dest;
    unsigned long long observed = 0;
    for (unsigned long long i = 0; i < copies; i++) {
        memcpy(dest, source, size);
        observed += observed_bytes[i % size];
    }
    if (memcmp(source, dest, size) != 0) {
        fputs("PHYSICAL_COPY_FAIL byte-parity\n", stderr);
        return 1;
    }
    printf("PHYSICAL_COPY\tbytes=%zu\tcopies=%llu\tobserved=%llu\n", size, copies, observed);
    free(dest);
    free(source);
    return 0;
}
