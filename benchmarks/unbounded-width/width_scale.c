// #2000 research-only benchmark: width scaling without a semantic ceiling.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint64_t g_alloc_calls=0,g_alloc_bytes=0;
static void *bm_malloc(size_t n){void*p=malloc(n?n:1);if(!p){perror("malloc");exit(2);}g_alloc_calls++;g_alloc_bytes+=n;return p;}
static void bm_free(void*p){free(p);}
static size_t nb(uint32_t w){return (w+7u)/8u;}

static uint8_t *pattern(uint32_t w,uint32_t salt){
 size_t n=nb(w);uint8_t*p=bm_malloc(n);memset(p,0,n);
 for(size_t i=0;i<n;i++)p[i]=(uint8_t)(0xA5u^(uint8_t)(i*37u)^(uint8_t)salt);
 unsigned unused=(unsigned)(n*8u-w);if(unused)p[0]&=(uint8_t)(0xFFu>>unused);
 if(w>1){unsigned first=7u-unused;p[0]&=(uint8_t)~(1u<<first);}return p;
}
static int raw_bit(const uint8_t*p,uint32_t w,uint32_t i){
 size_t n=nb(w);unsigned unused=(unsigned)(n*8u-w),pos=unused+i;
 return (p[pos/8]>>(7u-(pos%8u)))&1u;
}
static void raw_set(uint8_t*p,uint32_t w,uint32_t i,int bit){
 size_t n=nb(w);unsigned unused=(unsigned)(n*8u-w),pos=unused+i;uint8_t m=(uint8_t)(1u<<(7u-(pos%8u)));
 if(bit)p[pos/8]|=m;else p[pos/8]&=(uint8_t)~m;
}

typedef struct{uint32_t width;size_t nbytes;uint8_t*p;}HeapWord;
typedef struct{uint32_t width;uint8_t spilled;union{uint64_t bits;struct{size_t nbytes;uint8_t*p;}heap;}u;}SpillWord;

static int hm(HeapWord*o,const uint8_t*s,uint32_t w){if(!w)return 0;o->width=w;o->nbytes=nb(w);o->p=bm_malloc(o->nbytes);memcpy(o->p,s,o->nbytes);return 1;}
static void hd(HeapWord*o){if(o->p)bm_free(o->p);o->p=NULL;}
static int hb(const HeapWord*a,uint32_t i){return i<a->width?raw_bit(a->p,a->width,i):-1;}
static int he(const HeapWord*a,const HeapWord*b){return a->width==b->width&&a->nbytes==b->nbytes&&!memcmp(a->p,b->p,a->nbytes);}
static uint64_t hh(const HeapWord*a){uint64_t h=1469598103934665603ull^a->width;for(size_t i=0;i<a->nbytes;i++){h^=a->p[i];h*=1099511628211ull;}return h;}
static int hpfx(const HeapWord*a,const HeapWord*b){if(a->width>b->width)return 0;for(uint32_t i=0;i<a->width;i++)if(hb(a,i)!=hb(b,i))return 0;return 1;}
static int happ(const HeapWord*a,int bit,HeapWord*o){
 uint32_t w=a->width+1u;size_t n=nb(w);uint8_t*t=calloc(n,1);if(!t){perror("calloc");exit(2);}
 for(uint32_t i=0;i<a->width;i++) raw_set(t,w,i,hb(a,i));
 raw_set(t,w,a->width,bit);
 int ok=hm(o,t,w);
 free(t);
 return ok;
}
static int hpar(const HeapWord*a,HeapWord*o){
 if(a->width<=1) return 0;
 uint32_t w=a->width-1u;
 size_t n=nb(w);
 uint8_t*t=calloc(n,1);
 if(!t){perror("calloc");exit(2);}
 for(uint32_t i=0;i<w;i++) raw_set(t,w,i,hb(a,i));
 int ok=hm(o,t,w);
 free(t);
 return ok;
}

static uint64_t to64(const uint8_t*p,size_t n){uint64_t v=0;for(size_t i=0;i<n;i++)v=(v<<8)|p[i];return v;}
static int sm(SpillWord*o,const uint8_t*s,uint32_t w){
 if(!w) return 0;
 o->width=w;
 if(w<=64){o->spilled=0;o->u.bits=to64(s,nb(w));}
 else{o->spilled=1;o->u.heap.nbytes=nb(w);o->u.heap.p=bm_malloc(o->u.heap.nbytes);memcpy(o->u.heap.p,s,o->u.heap.nbytes);}return 1;
}
static void sd(SpillWord*o){if(o->spilled&&o->u.heap.p)bm_free(o->u.heap.p);o->spilled=0;}
static int sb(const SpillWord*a,uint32_t i){if(i>=a->width)return -1;if(!a->spilled)return (int)((a->u.bits>>(a->width-1u-i))&1u);return raw_bit(a->u.heap.p,a->width,i);}
static int se(const SpillWord*a,const SpillWord*b){
 if(a->width!=b->width) return 0;
 if(!a->spilled&&!b->spilled) return a->u.bits==b->u.bits;
 if(a->spilled!=b->spilled) return 0;
 return a->u.heap.nbytes==b->u.heap.nbytes&&!memcmp(a->u.heap.p,b->u.heap.p,a->u.heap.nbytes);
}
static uint64_t sh(const SpillWord*a){
 if(!a->spilled)return (a->u.bits*0x9E3779B185EBCA87ull)^a->width;
 uint64_t h=1469598103934665603ull^a->width;for(size_t i=0;i<a->u.heap.nbytes;i++){h^=a->u.heap.p[i];h*=1099511628211ull;}return h;
}
static int spfx(const SpillWord*a,const SpillWord*b){if(a->width>b->width)return 0;for(uint32_t i=0;i<a->width;i++)if(sb(a,i)!=sb(b,i))return 0;return 1;}
static int sapp(const SpillWord*a,int bit,SpillWord*o){
 if(!a->spilled&&a->width<64){o->width=a->width+1u;o->spilled=0;o->u.bits=(a->u.bits<<1)|(uint64_t)bit;return 1;}
 uint32_t w=a->width+1u;size_t n=nb(w);uint8_t*t=calloc(n,1);if(!t){perror("calloc");exit(2);}
 for(uint32_t i=0;i<a->width;i++) raw_set(t,w,i,sb(a,i));
 raw_set(t,w,a->width,bit);
 int ok=sm(o,t,w);
 free(t);
 return ok;
}
static int spar(const SpillWord*a,SpillWord*o){
 if(a->width<=1) return 0;
 if(!a->spilled){o->width=a->width-1u;o->spilled=0;o->u.bits=a->u.bits>>1;return 1;}
 uint32_t w=a->width-1u;
 size_t n=nb(w);
 uint8_t*t=calloc(n,1);
 if(!t){perror("calloc");exit(2);}
 for(uint32_t i=0;i<w;i++) raw_set(t,w,i,sb(a,i));
 int ok=sm(o,t,w);
 free(t);
 return ok;
}

static void verify(uint32_t w){
 uint8_t*s=pattern(w,7);HeapWord h={0},h2={0},ha={0},hp={0};SpillWord x={0},x2={0},xa={0},xp={0};
 hm(&h,s,w);hm(&h2,s,w);sm(&x,s,w);sm(&x2,s,w);if(!he(&h,&h2)||!se(&x,&x2))abort();
 happ(&h,1,&ha);sapp(&x,1,&xa);if(!hpfx(&h,&ha)||!spfx(&x,&xa))abort();hpar(&ha,&hp);spar(&xa,&xp);if(!he(&h,&hp)||!se(&x,&xp))abort();
 if(w>1){uint8_t*z0=calloc(nb(w),1),*z1=calloc(nb(w-1u),1);HeapWord a={0},b={0};SpillWord c={0},d={0};hm(&a,z0,w);hm(&b,z1,w-1u);sm(&c,z0,w);sm(&d,z1,w-1u);if(he(&a,&b)||se(&c,&d))abort();hd(&a);hd(&b);sd(&c);sd(&d);free(z0);free(z1);}
 hd(&h);hd(&h2);hd(&ha);hd(&hp);sd(&x);sd(&x2);sd(&xa);sd(&xp);bm_free(s);
}

int main(int argc,char**argv){
 if(argc!=6) return 2;
 const char*c=argv[1],*op=argv[2],*mode=argv[5];
 uint32_t w=(uint32_t)strtoul(argv[3],NULL,10);
 int it=atoi(argv[4]);
 int full=!strcmp(mode,"full");
 if(!w||it<1||(!full&&strcmp(mode,"prepare"))) return 2;
 verify(w);
 uint8_t*s=pattern(w,11);HeapWord h={0},h2={0};SpillWord x={0},x2={0};
 if(!strcmp(c,"heap")){hm(&h,s,w);hm(&h2,s,w);}else if(!strcmp(c,"spill")){sm(&x,s,w);sm(&x2,s,w);}else return 2;
 g_alloc_calls=g_alloc_bytes=0;volatile uint64_t sink=0;
 for(int k=0;k<it;k++){if(!full){sink^=(uint64_t)(k&1);continue;}
  if(!strcmp(c,"heap")){
   if(!strcmp(op,"eq"))sink^=he(&h,&h2);else if(!strcmp(op,"hash"))sink^=hh(&h);else if(!strcmp(op,"bit"))sink^=(uint64_t)hb(&h,(uint32_t)k%w);
   else if(!strcmp(op,"prefix"))sink^=hpfx(&h,&h2);else if(!strcmp(op,"append")){HeapWord q={0};happ(&h,k&1,&q);sink^=(uint64_t)hb(&q,q.width-1u);hd(&q);}
   else if(!strcmp(op,"parent")){if(w>1){HeapWord q={0};hpar(&h,&q);sink^=(uint64_t)hb(&q,q.width-1u);hd(&q);}}
   else if(!strcmp(op,"clone")){HeapWord q={0};hm(&q,h.p,h.width);sink^=he(&q,&h);hd(&q);}else return 2;
  }else{
   if(!strcmp(op,"eq"))sink^=se(&x,&x2);else if(!strcmp(op,"hash"))sink^=sh(&x);else if(!strcmp(op,"bit"))sink^=(uint64_t)sb(&x,(uint32_t)k%w);
   else if(!strcmp(op,"prefix"))sink^=spfx(&x,&x2);else if(!strcmp(op,"append")){SpillWord q={0};sapp(&x,k&1,&q);sink^=(uint64_t)sb(&q,q.width-1u);sd(&q);}
   else if(!strcmp(op,"parent")){if(w>1){SpillWord q={0};spar(&x,&q);sink^=(uint64_t)sb(&q,q.width-1u);sd(&q);}}
   else if(!strcmp(op,"clone")){SpillWord q={0};if(x.spilled)sm(&q,x.u.heap.p,x.width);else{uint8_t*t=calloc(nb(w),1);if(!t)exit(2);for(uint32_t i=0;i<w;i++)raw_set(t,w,i,sb(&x,i));sm(&q,t,w);free(t);}sink^=se(&q,&x);sd(&q);}else return 2;
  }
 }
 printf("candidate=%s op=%s width=%u mode=%s iters=%d sink=%llu allocations=%llu allocated_bytes=%llu object_bytes=%zu payload_bytes=%zu spilled=%d\n",c,op,w,mode,it,(unsigned long long)sink,(unsigned long long)g_alloc_calls,(unsigned long long)g_alloc_bytes,!strcmp(c,"heap")?sizeof(HeapWord):sizeof(SpillWord),nb(w),!strcmp(c,"spill")&&w>64);
 if(!strcmp(c,"heap")){hd(&h);hd(&h2);}else{sd(&x);sd(&x2);}bm_free(s);return 0;
}
