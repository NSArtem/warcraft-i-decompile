; NASM OMF fixture: a cross-function branch bypasses the sibling entry.
BITS 32
segment _TEXT public align=16 class=CODE use32
global IntroFrame_, IntroLoadCreditLines_
IntroFrame_:
    jmp IntroLoadCreditLines_ + 1
    ret
align 16
IntroLoadCreditLines_:
    nop
    xor eax, eax
    ret
