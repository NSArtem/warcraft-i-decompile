; Entirely synthetic data verification control, with an off32 pointer field.
%include "wc1.inc"
extern good_target:wrt FLAT
CODE_SECTION
GLABEL Probe_
    mov eax, pointer
    ret
DATA_SECTION
pointer:
    dd good_target
    db 'ABCD'
BSS_SECTION
STACK_SECTION
END_SECTIONS
