; Same early-ret sibling; an indirect call exercises the independent hook.
BITS 32
segment _TEXT public align=16 class=CODE use32
global IntroFrame_, IntroLoadCreditLines_
extern _line_timer
IntroFrame_:
    mov eax, IntroLoadCreditLines_ + 1
    call eax
    call IntroLoadCreditLines_
    ret
align 16
IntroLoadCreditLines_:
    ret
    mov word [_line_timer], 7
    ret
