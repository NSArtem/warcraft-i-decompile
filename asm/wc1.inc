; Section/label macros shared by the generated and hand-maintained asm.
; WC1_FORMAT_BIN: flat binary at the original addresses (round-trip proof).
; otherwise:      OMF segments for wlink (DOS/4GW LE).

%ifdef WC1_FORMAT_BIN
  bits 32
  %macro CODE_SECTION 0
    section .text vstart=0x10000 align=1
  %endmacro
  %macro DATA_SECTION 0
    section .data vstart=0x50000 follows=.text align=1
  %endmacro
  %macro BSS_SECTION 0
    section .bss nobits vfollows=.data
  %endmacro
  %macro STACK_SECTION 0
  %endmacro
  %macro GLABEL 1
    %1:
  %endmacro
  %macro ENTRY_POINT 0
  %endmacro
  %macro EXTERN_FN 1
    %error "the bin round-trip cannot contain C-replaced functions"
  %endmacro
  %macro END_SECTIONS 0
  %endmacro
%else
  %macro CODE_SECTION 0
    segment _TEXT public align=1 class=CODE use32 flat
  %endmacro
  %macro DATA_SECTION 0
    segment _DATA public align=1 class=DATA use32 flat
  %endmacro
  %macro BSS_SECTION 0
    segment _BSS public align=1 class=BSS use32 flat
  %endmacro
  %macro STACK_SECTION 0
    segment STACK stack align=1 class=STACK use32 flat
  %endmacro
  %macro GLABEL 1
    global %1
    %1:
  %endmacro
  %macro ENTRY_POINT 0
    ..start:
  %endmacro
  %macro EXTERN_FN 1
    extern %1
  %endmacro
  %macro END_SECTIONS 0
    group DGROUP _DATA _BSS STACK
  %endmacro
%endif
