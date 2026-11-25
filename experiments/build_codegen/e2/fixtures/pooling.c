/* Literal pointer equality and per-literal spacing are measured from FIXUPP. */
const char *PoolA(void) { return "E2-identical"; }
const char *PoolB(void) { return "E2-identical"; }
const char *StringA(void) { return "a"; }
const char *StringB(void) { return "bc"; }
const char *StringC(void) { return "defg"; }
static unsigned shared = 7;
unsigned StaticA(unsigned x) { static unsigned local = 11; local += x; return local + shared; }
unsigned StaticB(unsigned x) { shared += x; return shared; }
