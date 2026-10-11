// #1989 research-only carrier benchmark.
// No SENS runtime semantics live here. This measures mechanism carriers only.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BITS 129
#define MAX_BYTES ((MAX_BITS + 7) / 8)

static uint64_t g_alloc_calls = 0, g_alloc_bytes = 0;

static void *bm_malloc(size_t n) {
    void *p = malloc(n ? n : 1);
    if (!p) { perror("malloc"); exit(2); }
    g_alloc_calls++;
    g_alloc_bytes += n;
    return p;
}
static void bm_free(void *p) { free(p); }

typedef struct { uint16_t width; uint64_t bits; } Inline64;
typedef struct { uint16_t width; uint16_t nbytes; uint8_t *p; } BitBytes;
typedef struct {
    uint16_t width;
    uint8_t spilled;
    union { uint64_t bits; struct { uint16_t nbytes; uint8_t *p; } heap; } u;
} SmallSpill;

static uint16_t nbytes_for(uint16_t width) { return (uint16_t)((width + 7u)/8u); }

static void fill_bits(uint8_t *dst, uint16_t width, uint32_t salt) {
    uint16_t n = nbytes_for(width);
    memset(dst, 0, MAX_BYTES);
    for (uint16_t i=0;i<n;i++) dst[i] = (uint8_t)(0xA5u ^ (uint8_t)(i*37u) ^ (uint8_t)salt);
    unsigned unused = (unsigned)n*8u - width;
    if (unused) dst[0] &= (uint8_t)(0xFFu >> unused);
    // Force a leading zero when width > 1: exact width must preserve it.
    if (width > 1) {
        unsigned first_used = 7u - unused;
        dst[0] &= (uint8_t)~(1u << first_used);
    }
}

static uint64_t bytes_to_u64(const uint8_t *p, uint16_t n) {
    uint64_t v=0;
    for (uint16_t i=0;i<n;i++) v=(v<<8)|p[i];
    return v;
}
static int inline_make(Inline64 *o, const uint8_t *src, uint16_t width) {
    if (width<1 || width>64) return 0;
    o->width=width; o->bits=bytes_to_u64(src,nbytes_for(width)); return 1;
}
static int inline_eq(const Inline64 *a,const Inline64 *b){return a->width==b->width&&a->bits==b->bits;}
static int inline_append(const Inline64 *a,int bit,Inline64 *o){
    if(a->width>=64) return 0;
    o->width=a->width+1;
    o->bits=(a->bits<<1)|(uint64_t)bit;
    return 1;
}
static int inline_parent(const Inline64 *a,Inline64 *o){
    if(a->width<=1) return 0;
    o->width=a->width-1;
    o->bits=a->bits>>1;
    return 1;
}
static int inline_prefix(const Inline64 *a,const Inline64 *b){
    return a->width<=b->width && a->bits==(b->bits>>(b->width-a->width));
}
static uint64_t inline_hash(const Inline64 *a){return (a->bits*0x9E3779B185EBCA87ull)^a->width;}
static int inline_bit(const Inline64 *a,uint16_t i){ if(i>=a->width)return -1; return (int)((a->bits>>(a->width-1-i))&1u); }

static int bitbytes_make(BitBytes *o,const uint8_t *src,uint16_t width){
    if(width<1) return 0;
    o->width=width;
    o->nbytes=nbytes_for(width);
    o->p=bm_malloc(o->nbytes);
    memcpy(o->p,src,o->nbytes);
    return 1;
}
static void bitbytes_drop(BitBytes *o){ if(o->p)bm_free(o->p);o->p=NULL; }
static int bitbytes_eq(const BitBytes*a,const BitBytes*b){return a->width==b->width&&a->nbytes==b->nbytes&&!memcmp(a->p,b->p,a->nbytes);}
static int bitbytes_bit(const BitBytes*a,uint16_t i){
    if(i>=a->width) return -1;
    unsigned unused=(unsigned)a->nbytes*8u-a->width;
    unsigned pos=unused+i;
    return (a->p[pos/8]>>(7-(pos%8)))&1u;
}
static uint64_t bitbytes_hash(const BitBytes*a){
    uint64_t h=1469598103934665603ull ^ a->width;
    for(uint16_t i=0;i<a->nbytes;i++){h^=a->p[i];h*=1099511628211ull;}return h;
}
static int bitbytes_append(const BitBytes*a,int bit,BitBytes*o){
    uint16_t nw=a->width+1, nn=nbytes_for(nw); uint8_t tmp[MAX_BYTES]={0};
    // Bitwise copy avoids text and preserves exact leading zero/width.
    for(uint16_t i=0;i<a->width;i++){
        int b=bitbytes_bit(a,i); unsigned unused=(unsigned)nn*8u-nw; unsigned pos=unused+i;
        tmp[pos/8]|=(uint8_t)(b<<(7-(pos%8)));
    }
    unsigned unused=(unsigned)nn*8u-nw; unsigned pos=unused+a->width;
    tmp[pos/8]|=(uint8_t)(bit<<(7-(pos%8)));
    return bitbytes_make(o,tmp,nw);
}
static int bitbytes_parent(const BitBytes*a,BitBytes*o){
    if(a->width<=1) return 0;
    uint16_t nw=a->width-1, nn=nbytes_for(nw);
    uint8_t tmp[MAX_BYTES]={0};
    for(uint16_t i=0;i<nw;i++){int b=bitbytes_bit(a,i);unsigned unused=(unsigned)nn*8u-nw;unsigned pos=unused+i;tmp[pos/8]|=(uint8_t)(b<<(7-(pos%8)));}
    return bitbytes_make(o,tmp,nw);
}
static int bitbytes_prefix(const BitBytes*a,const BitBytes*b){
    if(a->width>b->width) return 0;
    for(uint16_t i=0;i<a->width;i++) {
        if(bitbytes_bit(a,i)!=bitbytes_bit(b,i)) return 0;
    }
    return 1;
}

static int spill_make(SmallSpill *o,const uint8_t*src,uint16_t width){
    if(width<1) return 0;
    o->width=width;
    if(width<=64){o->spilled=0;o->u.bits=bytes_to_u64(src,nbytes_for(width));}
    else{o->spilled=1;o->u.heap.nbytes=nbytes_for(width);o->u.heap.p=bm_malloc(o->u.heap.nbytes);memcpy(o->u.heap.p,src,o->u.heap.nbytes);}
    return 1;
}
static void spill_drop(SmallSpill*o){if(o->spilled&&o->u.heap.p)bm_free(o->u.heap.p);o->spilled=0;}
static int spill_bit(const SmallSpill*a,uint16_t i){
    if(i>=a->width)return -1;
    if(!a->spilled)return (int)((a->u.bits>>(a->width-1-i))&1u);
    unsigned unused=(unsigned)a->u.heap.nbytes*8u-a->width;unsigned pos=unused+i;
    return (a->u.heap.p[pos/8]>>(7-(pos%8)))&1u;
}
static int spill_eq(const SmallSpill*a,const SmallSpill*b){
    if(a->width!=b->width) return 0;
    if(!a->spilled) return a->u.bits==b->u.bits;
    return a->u.heap.nbytes==b->u.heap.nbytes &&
           memcmp(a->u.heap.p,b->u.heap.p,a->u.heap.nbytes)==0;
}
static uint64_t spill_hash(const SmallSpill*a){
    if(!a->spilled) return (a->u.bits*0x9E3779B185EBCA87ull)^a->width;
    uint64_t h=1469598103934665603ull^a->width;
    for(uint16_t i=0;i<a->u.heap.nbytes;i++){h^=a->u.heap.p[i];h*=1099511628211ull;}
    return h;
}
static int spill_append(const SmallSpill*a,int bit,SmallSpill*o){
    uint16_t nw=a->width+1;uint8_t tmp[MAX_BYTES]={0};uint16_t nn=nbytes_for(nw);
    for(uint16_t i=0;i<a->width;i++){int b=spill_bit(a,i);unsigned unused=(unsigned)nn*8u-nw;unsigned pos=unused+i;tmp[pos/8]|=(uint8_t)(b<<(7-(pos%8)));}
    unsigned unused=(unsigned)nn*8u-nw;unsigned pos=unused+a->width;tmp[pos/8]|=(uint8_t)(bit<<(7-(pos%8)));
    return spill_make(o,tmp,nw);
}
static int spill_parent(const SmallSpill*a,SmallSpill*o){
    if(a->width<=1) return 0;
    uint16_t nw=a->width-1,nn=nbytes_for(nw);
    uint8_t tmp[MAX_BYTES]={0};
    for(uint16_t i=0;i<nw;i++){int b=spill_bit(a,i);unsigned unused=(unsigned)nn*8u-nw;unsigned pos=unused+i;tmp[pos/8]|=(uint8_t)(b<<(7-(pos%8)));}
    return spill_make(o,tmp,nw);
}
static int spill_prefix(const SmallSpill*a,const SmallSpill*b){
    if(a->width>b->width) return 0;
    for(uint16_t i=0;i<a->width;i++) {
        if(spill_bit(a,i)!=spill_bit(b,i)) return 0;
    }
    return 1;
}

static int sens8_make(uint8_t *o,const uint8_t*src,uint16_t width){if(width!=8)return 0;*o=src[0];return 1;}
static uint64_t hash8(uint8_t v){return (uint64_t)v*0x9E3779B185EBCA87ull;}

static void usage(void){
    fprintf(stderr,"usage: carrier_bench CANDIDATE OP WIDTH ITERS MODE\n");
    fprintf(stderr,"candidate: sens8|inline64|bitbytes|spill; op: construct|eq|hash|bit|append|parent|prefix|project|clone; mode: prepare|full\n");
}

int main(int argc,char**argv){
    if(argc!=6){usage();return 2;}
    const char*cand=argv[1],*op=argv[2],*mode=argv[5];
    int width=atoi(argv[3]),iters=atoi(argv[4]),full=!strcmp(mode,"full");
    if(width<1||width>128||iters<1||(!full&&strcmp(mode,"prepare"))){usage();return 2;}
    uint8_t src[MAX_BYTES]={0},src2[MAX_BYTES]={0};fill_bits(src,(uint16_t)width,1);fill_bits(src2,(uint16_t)width,1);
    volatile uint64_t sink=0; uint64_t alloc0=0,bytes0=0;
    int supported=1;

    Inline64 ia={0},ib={0}; BitBytes ba={0},bb={0}; SmallSpill sa={0},sb={0}; uint8_t u8a=0,u8b=0;
    // Preparation is deliberately outside allocation accounting.
    if(!strcmp(cand,"sens8")) supported=sens8_make(&u8a,src,width)&&sens8_make(&u8b,src2,width);
    else if(!strcmp(cand,"inline64")) supported=inline_make(&ia,src,width)&&inline_make(&ib,src2,width);
    else if(!strcmp(cand,"bitbytes")) supported=bitbytes_make(&ba,src,width)&&bitbytes_make(&bb,src2,width);
    else if(!strcmp(cand,"spill")) supported=spill_make(&sa,src,width)&&spill_make(&sb,src2,width);
    else {usage();return 2;}
    if(!supported){
        printf("supported=0 candidate=%s op=%s width=%d\n",cand,op,width);
        return 0;
    }

    g_alloc_calls=0;g_alloc_bytes=0; alloc0=g_alloc_calls;bytes0=g_alloc_bytes;
    for(int k=0;k<iters;k++){
        if(!full){sink^=(uint64_t)(k&1);continue;}
        if(!strcmp(cand,"sens8")){
            if(!strcmp(op,"construct")){uint8_t x=0;supported=sens8_make(&x,src,width);if(supported)sink^=x;}
            else if(!strcmp(op,"eq"))sink^=(uint64_t)(u8a==u8b);
            else if(!strcmp(op,"hash"))sink^=hash8(u8a);
            else if(!strcmp(op,"bit"))sink^=(u8a>>(7-(k&7)))&1u;
            else if(!strcmp(op,"project"))sink^=u8a;
            else if(!strcmp(op,"clone")){uint8_t x=u8a;sink^=x;}
            else supported=0;
        } else if(!strcmp(cand,"inline64")){
            if(!strcmp(op,"construct")){Inline64 x={0};supported=inline_make(&x,src,width);if(supported)sink^=x.bits;}
            else if(!strcmp(op,"eq"))sink^=inline_eq(&ia,&ib);
            else if(!strcmp(op,"hash"))sink^=inline_hash(&ia);
            else if(!strcmp(op,"bit"))sink^=(uint64_t)inline_bit(&ia,(uint16_t)(k%width));
            else if(!strcmp(op,"append")){Inline64 x;supported=inline_append(&ia,k&1,&x);if(supported)sink^=x.bits;}
            else if(!strcmp(op,"parent")){Inline64 x;supported=inline_parent(&ia,&x);if(supported)sink^=x.bits;}
            else if(!strcmp(op,"prefix"))sink^=inline_prefix(&ia,&ib);
            else if(!strcmp(op,"project"))sink^=(width==8?ia.bits:0x55u);
            else if(!strcmp(op,"clone")){Inline64 x=ia;sink^=x.bits;}
            else supported=0;
        } else if(!strcmp(cand,"bitbytes")){
            if(!strcmp(op,"construct")){BitBytes x={0};bitbytes_make(&x,src,width);sink^=x.p[x.nbytes-1];bitbytes_drop(&x);}
            else if(!strcmp(op,"eq"))sink^=bitbytes_eq(&ba,&bb);
            else if(!strcmp(op,"hash"))sink^=bitbytes_hash(&ba);
            else if(!strcmp(op,"bit"))sink^=(uint64_t)bitbytes_bit(&ba,(uint16_t)(k%width));
            else if(!strcmp(op,"append")){BitBytes x={0};bitbytes_append(&ba,k&1,&x);sink^=x.p[x.nbytes-1];bitbytes_drop(&x);}
            else if(!strcmp(op,"parent")){BitBytes x={0};supported=bitbytes_parent(&ba,&x);if(supported){sink^=x.p[x.nbytes-1];bitbytes_drop(&x);}}
            else if(!strcmp(op,"prefix"))sink^=bitbytes_prefix(&ba,&bb);
            else if(!strcmp(op,"project"))sink^=(width==8?ba.p[0]:0x55u);
            else if(!strcmp(op,"clone")){BitBytes x={0};bitbytes_make(&x,ba.p,ba.width);sink^=x.p[x.nbytes-1];bitbytes_drop(&x);}
            else supported=0;
        } else {
            if(!strcmp(op,"construct")){SmallSpill x={0};spill_make(&x,src,width);sink^=(uint64_t)spill_bit(&x,width-1);spill_drop(&x);}
            else if(!strcmp(op,"eq"))sink^=spill_eq(&sa,&sb);
            else if(!strcmp(op,"hash"))sink^=spill_hash(&sa);
            else if(!strcmp(op,"bit"))sink^=(uint64_t)spill_bit(&sa,(uint16_t)(k%width));
            else if(!strcmp(op,"append")){SmallSpill x={0};spill_append(&sa,k&1,&x);sink^=(uint64_t)spill_bit(&x,x.width-1);spill_drop(&x);}
            else if(!strcmp(op,"parent")){SmallSpill x={0};supported=spill_parent(&sa,&x);if(supported){sink^=(uint64_t)spill_bit(&x,x.width-1);spill_drop(&x);}}
            else if(!strcmp(op,"prefix"))sink^=spill_prefix(&sa,&sb);
            else if(!strcmp(op,"project"))sink^=(width==8?(uint64_t)sa.u.bits:0x55u);
            else if(!strcmp(op,"clone")){SmallSpill x={0};spill_make(&x,src,width);sink^=(uint64_t)spill_bit(&x,width-1);spill_drop(&x);}
            else supported=0;
        }
        if(!supported)break;
    }
    uint64_t ac=g_alloc_calls-alloc0, ab=g_alloc_bytes-bytes0;

    size_t object_bytes=0, payload_bytes=nbytes_for((uint16_t)width);
    if(!strcmp(cand,"sens8"))object_bytes=sizeof(uint8_t);
    else if(!strcmp(cand,"inline64"))object_bytes=sizeof(Inline64);
    else if(!strcmp(cand,"bitbytes"))object_bytes=sizeof(BitBytes);
    else object_bytes=sizeof(SmallSpill);

    printf("supported=%d candidate=%s op=%s width=%d mode=%s iters=%d sink=%llu allocations=%llu allocated_bytes=%llu object_bytes=%zu payload_bytes=%zu spilled=%d\n",
        supported,cand,op,width,mode,iters,(unsigned long long)sink,(unsigned long long)ac,
        (unsigned long long)ab,object_bytes,payload_bytes,
        !strcmp(cand,"spill") && width>64 ? 1:0);

    if(!strcmp(cand,"bitbytes")){bitbytes_drop(&ba);bitbytes_drop(&bb);}
    if(!strcmp(cand,"spill")){spill_drop(&sa);spill_drop(&sb);}
    return 0;
}
