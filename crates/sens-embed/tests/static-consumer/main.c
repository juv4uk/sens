#include "my_lisp_embed.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    if (my_lisp_embed_abi_version() != MY_LISP_EMBED_ABI_VERSION) {
        return 10;
    }

    MyLispEmbedSession *session = my_lisp_embed_session_new();
    if (session == NULL) {
        return 11;
    }

    char *defined = my_lisp_embed_eval(session, "(визначити portable-proof 42)");
    if (defined == NULL) {
        my_lisp_embed_session_free(session);
        return 12;
    }
    my_lisp_embed_free_string(defined);

    char *read_back = my_lisp_embed_eval(session, "portable-proof");
    if (read_back == NULL || strcmp(read_back, "42") != 0) {
        if (read_back != NULL) {
            fprintf(stderr, "unexpected readback: %s\n", read_back);
            my_lisp_embed_free_string(read_back);
        }
        my_lisp_embed_session_free(session);
        return 13;
    }

    my_lisp_embed_free_string(read_back);
    my_lisp_embed_session_free(session);
    puts("static my-lisp-embed C consumer OK");
    return 0;
}
