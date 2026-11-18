/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module res_init (0x34040..0x34060), resource layer, "DBG" style. */
/* The codec descriptor (src/resources/codec.c, RegisterCodec).  A complete
 * type: Watcom 10.0a rejects an extern object of incomplete struct type
 * (E1044), and only its address is used here. */
typedef struct CodecDesc {
    unsigned char id;
    void (*alloc)(void);
    void (*begin)(void);
    void (*decode)(void);
    void (*free)(void);
} CodecDesc;

extern CodecDesc lzss_codec_desc;
extern void OpenArchive(void);
extern void RegisterCodec(CodecDesc *d);

/* @0x34040 */
void InitResources(void)
{
    OpenArchive();
    RegisterCodec(&lzss_codec_desc);
}
