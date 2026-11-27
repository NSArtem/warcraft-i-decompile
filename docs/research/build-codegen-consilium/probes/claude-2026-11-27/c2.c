extern void use(const char *a, const char *b);
void f(int x) { use(x ? ".net" : ".sav", "save%d"); }
