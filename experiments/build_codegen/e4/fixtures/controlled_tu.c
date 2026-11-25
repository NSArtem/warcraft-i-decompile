/* codegen-compiler: 10.0a */
/* E4 controlled multi-function TU: A (extracted) calls C across the
 * non-extracted neighbour B and reads one anonymous CONST literal.
 * Compiled with the original Watcom 10.0a; the oracle executable is this TU
 * linked intact, then recreated from the extracted A plus a provider of the
 * remaining bytes. */
extern int E4_C(int x);

int E4_A(int x)
{
    return E4_C(x) + "e4 const literal"[0];
}

int E4_B(int x)
{
    return x + 7;
}

int E4_C(int x)
{
    return x * 3;
}
