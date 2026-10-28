/* ENERGY-02 T08: immutable cons-list, C11, independent corpus implementation.
 * Frozen workload: n=500 (VERIFY) or n=20000 (MEASURE).
 * Each append allocates a fresh node that refers to the previous head.
 * The final head retains all earlier versions without mutating prior nodes.
 *
 * Output: SHA-256 of comma-separated lengths at i%1000==0 plus final length,
 * matching corpus/parity_check.py::ref_T08. This is not a SENS law or a
 * physical-energy measurement. No instrumentation/release gate changes.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Node {
    uint32_t value;
    const struct Node *previous;
} Node;

/* Escape the persistent head as an observable volatile pointer store.
 * Prevents the optimizer from treating all node allocation as unused work.
 * A future physical claim still needs compiler/assembly review.
 */
static const Node *volatile retained_head;

static const uint32_t SHA_K[64] = {
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
    0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
    0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
    0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
    0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
    0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};
static uint32_t rotr(uint32_t x, unsigned shift) {
    return (x >> shift) | (x << (32u - shift));
}
static void sha256(const unsigned char *in, size_t len, unsigned char out[32]) {
    uint32_t h[8] = {
        0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u
    };
    unsigned char buf[320] = {0};
    memcpy(buf, in, len);
    buf[len] = 0x80u;
    size_t blocks = (len + 9u + 63u) / 64u;
    uint64_t bits = (uint64_t)len * 8u;
    for (unsigned j=0; j<8; ++j) buf[blocks*64u-1u-j] = (unsigned char)(bits >> (j*8u));
    for (size_t b=0; b<blocks; ++b) {
        uint32_t w[64];
        for (unsigned i=0;i<16;++i) {
            size_t o=b*64u+i*4u;
            w[i]=((uint32_t)buf[o]<<24)|((uint32_t)buf[o+1]<<16)|
                 ((uint32_t)buf[o+2]<<8)|((uint32_t)buf[o+3]);
        }
        for (unsigned i=16;i<64;++i) {
            uint32_t s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3);
            uint32_t s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);
            w[i]=w[i-16]+s0+w[i-7]+s1;
        }
        uint32_t a=h[0],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],z=h[7];
        uint32_t bb=h[1];
        for (unsigned i=0;i<64;++i) {
            uint32_t s1=rotr(e,6)^rotr(e,11)^rotr(e,25);
            uint32_t ch=(e&f)^((~e)&g);
            uint32_t temp1=z+s1+ch+SHA_K[i]+w[i];
            uint32_t s0=rotr(a,2)^rotr(a,13)^rotr(a,22);
            uint32_t maj=(a&bb)^(a&c)^(bb&c);
            uint32_t temp2=s0+maj;
            z=g;g=f;f=e;e=d+temp1;d=c;c=bb;bb=a;a=temp1+temp2;
        }
        h[0]+=a;h[1]+=bb;h[2]+=c;h[3]+=d;
        h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=z;
    }
    for (unsigned i=0;i<8;++i) {
        out[i*4]=(unsigned char)(h[i]>>24);
        out[i*4+1]=(unsigned char)(h[i]>>16);
        out[i*4+2]=(unsigned char)(h[i]>>8);
        out[i*4+3]=(unsigned char)h[i];
    }
}
static int append_mark(char *buf, size_t capacity, size_t *used, unsigned n) {
    int wrote = snprintf(buf+*used, capacity-*used, "%s%u",
                         *used ? "," : "", n);
    if (wrote < 0 || (size_t)wrote >= capacity-*used) return 0;
    *used += (size_t)wrote;
    return 1;
}
static int reject(const char *detail) {
    fprintf(stderr, "T08_INVALID_INPUT: %s\n", detail);
    return 2;
}
static int parse_n(const char *raw, unsigned *n) {
    if (!raw || !*raw || raw[0]=='0') return 0;
    unsigned value=0;
    for (const char *p=raw; *p; ++p) {
        if (*p<'0'||*p>'9') return 0;
        value=value*10u+(unsigned)(*p-'0');
        if (value>20000u) return 0;
    }
    if (value!=500u && value!=20000u) return 0;
    *n=value;
    return 1;
}
int main(void) {
    const char *id=getenv("TASK_ID");
    if (!id || strcmp(id,"T08-persistent-structures")!=0)
        return reject("TASK_ID must match the frozen T08");
    unsigned n=0;
    if (!parse_n(getenv("TASK_N"), &n))
        return reject("TASK_N must be canonical 500 or 20000");
    const Node *head=NULL;
    size_t used=0;
    char marks[256]={0};
    for (unsigned i=0; i<n; ++i) {
        Node *item=malloc(sizeof(*item));
        if (!item) { fprintf(stderr,"T08_ALLOCATION_FAILURE\n"); return 3; }
        item->value=i;
        item->previous=head;
        head=item;
        if (i%1000u==0u && !append_mark(marks,sizeof marks,&used,i+1u))
            return reject("marker overflow");
    }
    retained_head=head;
    if (!append_mark(marks,sizeof marks,&used,n))
        return reject("marker overflow");
    unsigned char digest[32];
    sha256((const unsigned char *)marks,used,digest);
    for (unsigned i=0;i<32;++i) printf("%02x",(unsigned)digest[i]);
    if (putchar('\n')==EOF) return 3;
    return ferror(stdout) ? 3 : 0;
}
