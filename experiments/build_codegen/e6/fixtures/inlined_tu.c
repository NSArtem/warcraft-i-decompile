/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Watcom C inline helper, using the compiler's pragma-aux inline facility.
 * The caller contains the body; the retained sibling entry is unreachable. */
static int IntroLoadCreditLines(void) { return 7; }
#pragma aux IntroLoadCreditLines = "mov eax,7" value [eax] modify [eax];
int IntroFrame(void) { return IntroLoadCreditLines() + 3; }
