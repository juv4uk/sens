#include "sens_embed.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    if (sens_embed_abi_version() != SENS_EMBED_ABI_VERSION) {
        return 10;
    }

    SensEmbedSession *session = sens_embed_session_new();
    if (session == NULL) {
        return 11;
    }

    char *defined = sens_embed_eval(session, "(визначити portable-proof 42)");
    if (defined == NULL) {
        sens_embed_session_free(session);
        return 12;
    }
    sens_embed_free_string(defined);

    char *read_back = sens_embed_eval(session, "portable-proof");
    if (read_back == NULL || strcmp(read_back, "42") != 0) {
        if (read_back != NULL) {
            fprintf(stderr, "unexpected readback: %s\n", read_back);
            sens_embed_free_string(read_back);
        }
        sens_embed_session_free(session);
        return 13;
    }

    sens_embed_free_string(read_back);
    sens_embed_session_free(session);
    puts("static sens-embed C consumer OK");
    return 0;
}
