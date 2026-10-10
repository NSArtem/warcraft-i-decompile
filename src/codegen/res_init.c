/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module res_init (0x34040..0x34060), resource layer, "DBG" style. */
struct codec_desc;
extern struct codec_desc lzss_codec_desc;
extern void OpenArchive(void);
extern void RegisterCodec(const struct codec_desc *d);

/* @0x34040 */
void InitResources(void)
{
    OpenArchive();
    RegisterCodec(&lzss_codec_desc);
}
