#ifndef WSM_KERNEL_H
#define WSM_KERNEL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define WSM_KERNEL_ABI_VERSION 2u

typedef enum WsmKernelKind {
    WSM_KERNEL_COMMON_LISP = 1,
    WSM_KERNEL_PROLOG = 2,
    WSM_KERNEL_CLIPS = 3,
    WSM_KERNEL_DATALOG = 4
} WsmKernelKind;

typedef struct WsmByteSpan {
    const uint8_t *ptr;
    size_t len;
} WsmByteSpan;

typedef struct WsmMutableByteSpan {
    uint8_t *ptr;
    size_t len;
} WsmMutableByteSpan;

typedef struct WsmKernelRequest {
    uint8_t semantic_id;
    WsmByteSpan payload;
} WsmKernelRequest;

typedef enum WsmStatus {
    WSM_STATUS_OK = 0,
    WSM_STATUS_INVALID_ARGUMENT = 1,
    WSM_STATUS_NOT_RUNNING = 2,
    WSM_STATUS_BUFFER_TOO_SMALL = 3,
    WSM_STATUS_KERNEL_FAILURE = 4
} WsmStatus;

typedef WsmStatus (*WsmStartFn)(void *context);
typedef WsmStatus (*WsmStopFn)(void *context);
typedef WsmStatus (*WsmExchangeFn)(
    void *context,
    WsmKernelRequest request,
    WsmMutableByteSpan response,
    size_t *written
);
typedef WsmStatus (*WsmSnapshotFn)(
    void *context,
    WsmMutableByteSpan response,
    size_t *written
);

typedef struct WsmKernelVTable {
    uint32_t abi_version;
    WsmKernelKind kernel;
    void *context;
    WsmStartFn start;
    WsmExchangeFn exchange;
    WsmSnapshotFn snapshot;
    WsmStopFn stop;
} WsmKernelVTable;

uint32_t wsm_kernel_abi_version(void);
const char *wsm_kernel_kind_name(WsmKernelKind kind);

#ifdef __cplusplus
}
#endif

#endif
