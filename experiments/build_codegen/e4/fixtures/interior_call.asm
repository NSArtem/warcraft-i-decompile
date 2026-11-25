; E4 negative control N2: the only call targets the neighbour's interior.
%include "wc1.inc"
CODE_SECTION
GLABEL E4_A
    push    ebp
    mov     ebp, esp
    call    E4_Neighbor+1
    pop     ebp
    ret
    align 16
GLABEL E4_Neighbor
    mov     eax, [esp+4]
    add     eax, 7
    ret
    align 16
GLABEL E4_C
    mov     eax, [esp+4]
    lea     eax, [eax+eax*2]
    ret
DATA_SECTION
BSS_SECTION
STACK_SECTION
END_SECTIONS
