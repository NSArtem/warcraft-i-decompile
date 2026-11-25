/* codegen-compiler: 10.0a */
/* Synthetic all-three-segment compiler control (not Warcraft source). */
static unsigned long counter = 7;
static unsigned long scratch;
extern void observe(const char *, unsigned long *, unsigned long *);
void Probe(void) { observe("E5 immutable literal", &counter, &scratch); }
