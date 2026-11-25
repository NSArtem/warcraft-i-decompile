; E4 fixture data provider: one verified loadable data object plus the runtime.
%include "wc1.inc"
CODE_SECTION
..start:
    mov ax,0x4c00
    int 0x21
DATA_SECTION
GLABEL _e4_data
    db 1,2,3,4,5,6,7,8
BSS_SECTION
STACK_SECTION
    resb 4096
END_SECTIONS
