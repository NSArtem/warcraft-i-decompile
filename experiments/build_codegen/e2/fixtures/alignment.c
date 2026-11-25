/* Exact short bodies isolate alignment policy from C instruction selection.
 * Aux routines are inlined byte emitters, with an empty register clobber set.
 * The enclosing exported C functions still get compiler-chosen alignment. */
void Bytes4(void);
#pragma aux Bytes4 = 0x90 0x90 0x90 0x90 modify exact [];
void Bytes10(void);
#pragma aux Bytes10 = 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 modify exact [];
void Bytes16(void);
#pragma aux Bytes16 = 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 modify exact [];
void Bytes22(void);
#pragma aux Bytes22 = 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 0x90 modify exact [];
void Body5(void) { Bytes4(); }
void Body11(void) { Bytes10(); }
void Body17(void) { Bytes16(); }
void Body23(void) { Bytes22(); }
/* Natural C controls: no byte emitters. */
unsigned Add(unsigned x) { return x + 17; }
unsigned Multiply(unsigned x) { return x * 17 + 0x12345; }
unsigned Branch(unsigned x) { if (x & 8) return x * 33; return x / 7; }
unsigned Walk(volatile unsigned *p, unsigned n)
{
    unsigned sum = 0;
    while (n--) sum += *p++;
    return sum;
}
