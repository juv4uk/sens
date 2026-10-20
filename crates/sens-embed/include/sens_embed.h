#ifndef SENS_EMBED_H
#define SENS_EMBED_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SENS_EMBED_ABI_VERSION 6u

typedef struct SensEmbedSession SensEmbedSession;
typedef int32_t (*SensEmbedNullaryFn)(void *context, uint32_t *out_result);
typedef int32_t (*SensEmbedUnaryFn)(void *context, uint64_t token, uint32_t *out_result);

enum {
    SENS_EMBED_NIL = 0u,
    SENS_EMBED_TRUE = 1u,
};

uint32_t sens_embed_abi_version(void);
SensEmbedSession *sens_embed_session_new(void);
int32_t sens_embed_bind_host_handle(
    SensEmbedSession *session,
    const char *utf8_surface,
    const char *utf8_kind,
    uint64_t token);
int32_t sens_embed_register_nullary(
    SensEmbedSession *session,
    const char *utf8_surface,
    SensEmbedNullaryFn callback,
    void *context);
int32_t sens_embed_register_unary(
    SensEmbedSession *session,
    const char *utf8_surface,
    const char *utf8_kind,
    SensEmbedUnaryFn callback,
    void *context);
char *sens_embed_eval(SensEmbedSession *session, const char *utf8_source);
/* Densely packed result bits: 8 bits per byte, MSB-first, no padding.
   *out_bit_len is the meaningful bit count; never infer a domain from *out_len. */
int32_t sens_embed_eval_binary(
    SensEmbedSession *session,
    const char *utf8_source,
    uint8_t **out_bytes,
    size_t *out_len,
    size_t *out_bit_len,
    char **out_error);
void sens_embed_free_bits(uint8_t *bytes, size_t len);
void sens_embed_free_string(char *value);
void sens_embed_session_free(SensEmbedSession *session);

#ifdef __cplusplus
}
#endif

#endif
