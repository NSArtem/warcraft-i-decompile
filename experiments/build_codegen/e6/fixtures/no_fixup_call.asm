; Supplemental zero-FIXUPP intra-segment call, assembled rather than patched.
BITS 32
segment _TEXT public align=16 class=CODE use32
global IntroFrame_, IntroLoadCreditLines_
extern _frame_ready, _intro_tick_count, _credits_on
IntroLoadCreditLines_:
    ret
align 16
IntroFrame_:
    mov word [_frame_ready], 1
    inc word [_intro_tick_count]
    cmp word [_credits_on], 0
    je .done
    call IntroLoadCreditLines_
.done:
    ret
