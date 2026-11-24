/*
 * Declarations for the two-player setup menu and the unit order dispatch
 * (analysis/symbols/mod_13f60.toml, docs/subsystems/mod_13f60.md).
 *
 * Only the fields the reconstructed functions touch are modelled; the offsets
 * come from the code (compile with -zp2, the module's packing).
 */
#ifndef MOD_13F60_H
#define MOD_13F60_H

#include <stdio.h>

/* a dialog control handed to the callbacks; +0x16 is the control's text/buffer
 * pointer (used by every edit control) and +6 a pointer to the integer a check
 * box edits (CheckBoxToggle 0x15498) */
typedef struct Control {
    char pad0[6];
    long *value;                        /* 0x06 (CheckBoxToggle) */
    char pad8[0x16 - 0x0a];
    char *text;                         /* 0x16 */
} Control;

/* The unit order dispatch (DISPATCH.C) handlers get the unit in eax; only the
 * fields they touch are modelled (see src/include/game_2c4e0.h for the full
 * record and docs/subsystems/game_2c4e0.md for the field meanings). */
typedef struct OrderUnit {
    char pad0[6];
    unsigned char anim_timer;           /* 0x06 */
    unsigned char frame;                /* 0x07 */
    unsigned char facing;               /* 0x08 */
    char pad9[0x10 - 9];
    unsigned short flags;               /* 0x10 */
    char pad12[0x16 - 0x12];
    unsigned short hp;                  /* 0x16 */
    char pad18[0x1a - 0x18];
    unsigned char energy;               /* 0x1a */
    unsigned char type;                 /* 0x1b */
    unsigned char type_copy;            /* 0x1c */
    char pad1d;
    unsigned char owner;                /* 0x1e */
    unsigned char order;                /* 0x1f */
    unsigned char order_next;           /* 0x20 */
    unsigned char order_next_arg;       /* 0x21 */
    char pad22[0x3a - 0x22];
    void *target;                       /* 0x3a: the attack target */
    char pad3e[0x46 - 0x3e];
    void *work;                         /* 0x46 */
    unsigned char b48;                  /* 0x48 */
    unsigned char b49;                  /* 0x49 */
    char pad4a[0x52 - 0x4a];
    void *dest;                         /* 0x52 */
} OrderUnit;

typedef struct ControlTitleBitmap {
    unsigned short width;              /* 0x00 */
    unsigned short height;             /* 0x02 */
    void *body;                        /* 0x04 */
} ControlTitleBitmap;

extern ControlTitleBitmap dat_51658;                /* 0x51658 */
extern OrderUnit *unit_array;

extern unsigned char death_sound_by_type[0x20];     /* 0x5156c */
extern short game_mode;                             /* 0x59616 */
extern short screen_mode;                           /* 0x593f6 */
extern unsigned short dat_516ae;              /* 0x516ae */
extern unsigned short own_campaign;                 /* 0x52584 */
extern short preview_rect[6];                       /* 0x5175c */
extern unsigned short game_start_mode;              /* 0x593d4 */
extern unsigned short save_slot;                    /* 0x593cc */
extern unsigned short slot_remote;                  /* 0x593d6 */
extern unsigned short edit_value;                   /* 0x593d2 */
extern void *edit_control;                          /* 0x593c8 */
extern void *slot_file;                             /* 0x59610 */
extern unsigned short net_node_number;              /* 0x52a7c (a word field) */
extern char phone_number[];                         /* 0x52a28 */
extern char modem_init1[];                          /* 0x52998 */
extern char modem_init2[];                          /* 0x529c8 */
extern char modem_hangup[];                         /* 0x529f8 */
extern char dat_59230[];                            /* 0x59230 (codegen_promo.toml) */
extern char edit_buffer1[];                         /* 0x59260 */
extern char edit_buffer2[];                         /* 0x59290 */
extern char exe_dir[];                              /* 0x59920 */
extern char str_remote_slot[];                      /* 0x516b4 */
extern char str_army_total_zero[];                  /* 0x516c2 */
extern char str_ext_net[];                          /* 0x56b1c ".net" */
extern char str_ext_sav[];                          /* 0x56b24 ".sav" */
extern char fmt_save_d[];                           /* 0x56b2c "save%d" */
extern char fmt_slot_number[];                      /* 0x56b34 "%d. %s" */
extern char str_read_binary[];                      /* 0x56b3c "rb" */
extern char fmt_decimal[];                          /* 0x56b4c "%d" */
extern char str_system_has_control[];               /* 0x56b70 */
extern char str_ctrl_esc_disconnect[];              /* 0x56b84 */
extern char tag_baud2idx[];                         /* 0x56ba0 */
extern char tag_idx2baud[];                         /* 0x56bac */
extern char tag_irq2idx[];                          /* 0x56bb8 */
extern char tag_idx2irq[];                          /* 0x56bc0 */
extern char tag_setirq[];                           /* 0x56bc8 */
extern char fmt_two_digits[];                       /* 0x56bd0 "%02d" */

void __cdecl FatalError(const char *msg, ...);      /* 0x30bf0, cdecl */
void UnitSetOrder(OrderUnit *u, unsigned char order);   /* 0x2ee50 */
void UnitSetNextOrders(OrderUnit *u, unsigned char o, unsigned char arg); /* 0x2eed4 */
short IsNumberChar(int c);                       /* 0x15c50 */
short IsPhoneChar(unsigned char c);               /* 0x15c70 */
void _makepath(char *path, const char *drive, const char *dir, const char *name, const char *ext); /* 0x31c24 */

#endif
