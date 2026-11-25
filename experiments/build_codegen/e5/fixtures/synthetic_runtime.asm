%include "wc1.inc"
CODE_SECTION
global observe_
observe_:
    ret
..start:
    mov ax,0x4c00
    int 0x21
DATA_SECTION
BSS_SECTION
STACK_SECTION
    resb 4096
END_SECTIONS
