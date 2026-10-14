// Host-only physical F3C stack-touch probe. Zig remains freestanding.
// libc/pthreads exist only in this measurement executable, not in Zig.
#define _GNU_SOURCE
#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

extern int32_t sens_zig_free_f3c_pack(
    const uint8_t *, uint32_t, uint8_t *, uint32_t, uint8_t *, uint32_t);
extern int32_t sens_zig_free_f3c_unpack(
    const uint8_t *, uint32_t, uint8_t *, uint32_t, uint8_t *, uint32_t);

#define SCRATCH_BYTES 8192u
#define STACK_BYTES (512u * 1024u)
#define STACK_CANARY 0xA5u

static const uint8_t quote_t5[] = {0x63, 0x89, 0x06, 0xa1};
static const uint8_t quote_f3[] = {0xf3, 0x40, 0x60};
static const uint8_t nested_t5[] = {0x66, 0x38, 0x67, 0x89, 0x89, 0x3b, 0x35};
static const uint8_t nested_f3[] = {0xf3, 0x36, 0x5f, 0x1b, 0xd0, 0xc9};

struct sample {
    const char *name;
    int unpack;
    const uint8_t *input;
    uint32_t input_length;
    const uint8_t *expected;
    uint32_t expected_length;
    int32_t actual_length;
    int ok;
};

// Volatile writes ensure that caller-owned scratch is counted as touched.
// The observed stack region includes C + pthread setup and the Zig call chain,
// NOT a proven worst-case Zig frame, stack-pointer bound or ESP32-S3 SRAM use.
__attribute__((noinline)) static void *exercise(void *opaque) {
    struct sample *sample = (struct sample *)opaque;
    volatile uint8_t scratch[SCRATCH_BYTES];
    uint8_t buffer[32];
    for (size_t i = 0; i < sizeof scratch; i++) scratch[i] = (uint8_t)i;
    memset(buffer, STACK_CANARY, sizeof buffer);
    memcpy(buffer, sample->input, sample->input_length);

    const int32_t actual = sample->unpack
        ? sens_zig_free_f3c_unpack(
              buffer, sample->input_length, buffer, sizeof buffer,
              (uint8_t *)scratch, sizeof scratch)
        : sens_zig_free_f3c_pack(
              buffer, sample->input_length, buffer, sizeof buffer,
              (uint8_t *)scratch, sizeof scratch);

    sample->actual_length = actual;
    sample->ok = actual == (int32_t)sample->expected_length &&
                 memcmp(buffer, sample->expected, sample->expected_length) == 0;
    return NULL;
}

static int measure(struct sample *sample) {
    const long page_long = sysconf(_SC_PAGESIZE);
    if (page_long <= 0) {
        fputs("ZIG_F3C_STACK_SAMPLE_FAIL phase=page_size\n", stderr);
        return 2;
    }
    const size_t page = (size_t)page_long;
    const size_t stack_size = STACK_BYTES;
    const size_t allocation = stack_size + 2 * page;
    void *mapping = mmap(NULL, allocation, PROT_NONE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) {
        perror("mmap");
        return 2;
    }
    uint8_t *stack = (uint8_t *)mapping + page;
    if (mprotect(stack, stack_size, PROT_READ | PROT_WRITE) != 0) {
        perror("mprotect");
        munmap(mapping, allocation);
        return 2;
    }

    memset(stack, STACK_CANARY, stack_size);
    pthread_attr_t attr;
    int code = pthread_attr_init(&attr);
    if (code != 0) {
        fprintf(stderr, "pthread_attr_init error=%d\n", code);
        munmap(mapping, allocation);
        return 2;
    }
    code = pthread_attr_setguardsize(&attr, 0); // Explicit mmap guard pages.
    if (code == 0) code = pthread_attr_setstack(&attr, stack, stack_size);
    pthread_t thread;
    if (code == 0) code = pthread_create(&thread, &attr, exercise, sample);
    pthread_attr_destroy(&attr);
    if (code != 0) {
        fprintf(stderr, "pthread_stack_setup error=%d\n", code);
        munmap(mapping, allocation);
        return 2;
    }
    code = pthread_join(thread, NULL);
    if (code != 0) {
        fprintf(stderr, "pthread_join error=%d\n", code);
        munmap(mapping, allocation);
        return 2;
    }

    size_t first_changed = 0;
    while (first_changed < stack_size &&
           stack[first_changed] == STACK_CANARY) first_changed++;
    const size_t touched = stack_size - first_changed;
    // Leave at least 64 KiB sentinel margin: avoid a silent stack overflow.
    const int passed = sample->ok && touched > 0 &&
                       touched < stack_size - (64u * 1024u);
    printf("ZIG_F3C_STACK_SAMPLE_%s case=%s abi_length=%" PRId32
           " observed_touched_stack_bytes=%zu host_pthread_stack_bytes=%zu"
           " caller_scratch_bytes=%u target=x86_64-linux reason=%s\n",
           passed ? "PASS" : "FAIL", sample->name, sample->actual_length,
           touched, stack_size, SCRATCH_BYTES,
           passed ? "golden_bytes_match" : "golden_or_guard_margin_failure");
    fflush(stdout);
    munmap(mapping, allocation);
    return passed ? 0 : 1;
}

int main(void) {
    struct sample samples[] = {
        {"pack_quote", 0, quote_t5, sizeof quote_t5,
         quote_f3, sizeof quote_f3, -99, 0},
        {"unpack_quote", 1, quote_f3, sizeof quote_f3,
         quote_t5, sizeof quote_t5, -99, 0},
        {"pack_nested", 0, nested_t5, sizeof nested_t5,
         nested_f3, sizeof nested_f3, -99, 0},
        {"unpack_nested", 1, nested_f3, sizeof nested_f3,
         nested_t5, sizeof nested_t5, -99, 0},
    };
    for (size_t i = 0; i < sizeof samples / sizeof samples[0]; i++) {
        if (measure(&samples[i]) != 0) return 1;
    }
    puts("ZIG_F3C_STACK_HOST_SAMPLES_PASS cases=4"
         " worst_case_stack_bound=NOT_PROVEN esp32_s3=NOT_TESTED");
    return 0;
}
