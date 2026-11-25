; E4 fixture runtime: DOS exit entry, one stack, no loadable data bytes.
%include "wc1.inc"
CODE_SECTION
..start:
    mov ax,0x4c00
    int 0x21
DATA_SECTION
BSS_SECTION
STACK_SECTION
    resb 4096
END_SECTIONS
