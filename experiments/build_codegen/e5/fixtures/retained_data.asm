; Synthetic retained DATA -> emptied CONST fixup control.
%include "wc1.inc"
CODE_SECTION
GLABEL Probe_
    mov eax, pointer
    ret
DATA_SECTION
pointer:
    dd literal
segment CONST public align=1 class=DATA use32 flat
literal:
    db 'ABCD'
BSS_SECTION
STACK_SECTION
END_SECTIONS
