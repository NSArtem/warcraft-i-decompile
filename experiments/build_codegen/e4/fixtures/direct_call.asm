; E4 controlled direct (unfixed) intra-TU call: A calls C over the neighbour B.
; NASM resolves the same-segment call to a plain rel32 displacement with no
; FIXUPP, so the extractor has to recover C's identity from the symbol table.
%include "wc1.inc"
CODE_SECTION
GLABEL E4_A
    push    ebp
    mov     ebp, esp
    call    E4_C
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
