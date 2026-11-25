; Exact review reproducer: entry reachability stops before executable bytes.
BITS 32
segment _TEXT public align=16 class=CODE use32
global IntroFrame_, IntroLoadCreditLines_
extern _line_timer
IntroFrame_:
    jmp IntroLoadCreditLines_ + 1
    ret
align 16
IntroLoadCreditLines_:
    ret
    mov word [_line_timer], 7
    ret
