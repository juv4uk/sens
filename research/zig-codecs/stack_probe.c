#define _GNU_SOURCE
// Hosted Linux diagnostic for the freestanding physical Zig ABI.
// A painted pthread stack reports *touched* bytes, not a provable maximum.
// Never use this result as the ESP32-S3/Xtensa stack budget or a SENS oracle.
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define F3C_SCRATCH_BYTES 8192u
#define PROBE_STACK_BYTES (256u * 1024u)
#define PAINT_BYTE 0xa5u

typedef int32_t (*f3c_codec)(const uint8_t *, uint32_t, uint8_t *, uint32_t,
                             uint8_t *, uint32_t);

typedef struct {
    const char *name;
    const uint8_t *raw;
    uint32_t raw_len;
    const uint8_t *carrier;
    uint32_t carrier_len;
} Sample;

typedef struct {
    const Sample *sample;
    f3c_codec pack;
    f3c_codec unpack;
    int status;
} Task;

static const uint8_t quote_raw[] = {0x63, 0x89, 0x06, 0xa1};
static const uint8_t quote_carrier[] = {0xf3, 0x40, 0x60};
static const uint8_t nested_raw[] = {0x66, 0x38, 0x67, 0x89, 0x89, 0x3b, 0x35};
static const uint8_t nested_carrier[] = {0xf3, 0x36, 0x5f, 0x1b, 0xd0, 0xc9};
static const Sample samples[] = {
    {.name = "baseline", .raw = NULL, .raw_len = 0, .carrier = NULL, .carrier_len = 0},
    {.name = "quote", .raw = quote_raw, .raw_len = sizeof(quote_raw),
     .carrier = quote_carrier, .carrier_len = sizeof(quote_carrier)},
    {.name = "nested_car_cons", .raw = nested_raw, .raw_len = sizeof(nested_raw),
     .carrier = nested_carrier, .carrier_len = sizeof(nested_carrier)},
};

static void *worker(void *arg) {
    Task *task = (Task *)arg;
    uint8_t scratch[F3C_SCRATCH_BYTES];
    uint8_t bytes[64];
    // Touch all caller-owned scratch, so this reserved space contributes
    // even if a particular input uses only a fraction of the work area.
    memset(scratch, PAINT_BYTE, sizeof(scratch));
    memset(bytes, 0, sizeof(bytes));
    task->status = 1;
    if (task->sample->raw == NULL) {
        task->status = (scratch[0] == PAINT_BYTE &&
                        scratch[F3C_SCRATCH_BYTES - 1] == PAINT_BYTE) ? 0 : 2;
        return NULL;
    }
    const Sample *s = task->sample;
    memcpy(bytes, s->raw, s->raw_len);
    const int32_t enc = task->pack(bytes, s->raw_len, bytes, sizeof(bytes),
                                   scratch, sizeof(scratch));
    if (enc != (int32_t)s->carrier_len ||
        memcmp(bytes, s->carrier, s->carrier_len) != 0) {
        fprintf(stderr, "F3C_STACK_FAIL case=%s phase=pack actual=%d expected=%u\n",
                s->name, enc, s->carrier_len);
        task->status = 3;
        return NULL;
    }
    const int32_t dec = task->unpack(bytes, s->carrier_len, bytes, sizeof(bytes),
                                     scratch, sizeof(scratch));
    if (dec != (int32_t)s->raw_len || memcmp(bytes, s->raw, s->raw_len) != 0) {
        fprintf(stderr, "F3C_STACK_FAIL case=%s phase=unpack actual=%d expected=%u\n",
                s->name, dec, s->raw_len);
        task->status = 4;
        return NULL;
    }
    task->status = 0;
    return NULL;
}

static int run_thread(const Sample *sample, f3c_codec pack, f3c_codec unpack,
                      size_t *touched) {
    const long page = sysconf(_SC_PAGESIZE);
    if (page <= 0 || PROBE_STACK_BYTES % (size_t)page != 0) {
        fprintf(stderr, "F3C_STACK_FAIL phase=host_page_size\n");
        return 1;
    }
    const size_t total = (size_t)page + PROBE_STACK_BYTES;
    void *region = mmap(NULL, total, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    uint8_t *stack = (uint8_t *)region + page;
    memset(stack, PAINT_BYTE, PROBE_STACK_BYTES);
    if (mprotect(region, (size_t)page, PROT_NONE) != 0) {
        perror("mprotect");
        munmap(region, total);
        return 1;
    }
    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0) {
        fprintf(stderr, "F3C_STACK_FAIL phase=attr_init\n");
        munmap(region, total);
        return 1;
    }
    const int attr_status = pthread_attr_setstack(&attr, stack, PROBE_STACK_BYTES);
    if (attr_status != 0) {
        fprintf(stderr, "F3C_STACK_FAIL phase=attr_setstack errno=%d\n", attr_status);
        pthread_attr_destroy(&attr);
        munmap(region, total);
        return 1;
    }
    Task task = {.sample = sample, .pack = pack, .unpack = unpack, .status = 99};
    pthread_t thread;
    const int created = pthread_create(&thread, &attr, worker, &task);
    pthread_attr_destroy(&attr);
    if (created != 0) {
        fprintf(stderr, "F3C_STACK_FAIL phase=pthread_create errno=%d\n", created);
        munmap(region, total);
        return 1;
    }
    const int joined = pthread_join(thread, NULL);
    if (joined != 0 || task.status != 0) {
        fprintf(stderr, "F3C_STACK_FAIL case=%s phase=join_or_codec join=%d status=%d\n",
                sample->name, joined, task.status);
        munmap(region, total);
        return 1;
    }
    // Linux x86-64 pthread stacks grow downward. The lowermost overwritten
    // canary gives touched high-water, a lower bound on peak reserved stack.
    // pthread startup/teardown is also included in this figure.
    size_t low_watermark = PROBE_STACK_BYTES;
    for (size_t i = 0; i < PROBE_STACK_BYTES; ++i) {
        if (stack[i] != PAINT_BYTE) {
            low_watermark = i;
            break;
        }
    }
    *touched = PROBE_STACK_BYTES - low_watermark;
    printf("F3C_STACK_SAMPLE host=linux_x86_64 case=%s stack_capacity=%u "
           "touched_bytes=%zu scratch_caller_bytes=%u measurement=CANARY_LOWER_BOUND\n",
           sample->name, PROBE_STACK_BYTES, *touched, F3C_SCRATCH_BYTES);
    munmap(region, total);
    return (*touched > 0 && *touched < PROBE_STACK_BYTES) ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s path-to-freestanding-shared-lib\n", argv[0]);
        return 2;
    }
    void *lib = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (lib == NULL) {
        fprintf(stderr, "F3C_STACK_FAIL phase=dlopen detail=%s\n", dlerror());
        return 1;
    }
    f3c_codec pack = (f3c_codec)dlsym(lib, "sens_zig_free_f3c_pack");
    f3c_codec unpack = (f3c_codec)dlsym(lib, "sens_zig_free_f3c_unpack");
    if (pack == NULL || unpack == NULL) {
        fprintf(stderr, "F3C_STACK_FAIL phase=dlsym\n");
        dlclose(lib);
        return 1;
    }
    size_t touched[sizeof(samples) / sizeof(samples[0])] = {0};
    for (size_t i = 0; i < sizeof(samples) / sizeof(samples[0]); ++i) {
        if (run_thread(&samples[i], pack, unpack, &touched[i]) != 0) {
            dlclose(lib);
            return 1;
        }
    }
    for (size_t i = 1; i < sizeof(samples) / sizeof(samples[0]); ++i) {
        const long delta = (long)touched[i] - (long)touched[0];
        printf("F3C_STACK_DELTA case=%s touched_delta_from_baseline=%ld\n",
               samples[i].name, delta);
    }
    puts("F3C_STACK_HOST_GOLDEN_PASS measured=TOUCHED_ONLY worst_case_stack=NOT_PROVED esp32_s3=NOT_TESTED semantic_authority=SENS");
    dlclose(lib);
    return 0;
}
