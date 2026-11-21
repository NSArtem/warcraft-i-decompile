#ifndef MOD_13E60_H
#define MOD_13E60_H

/* Demo / attract-mode sequencer (0x13e60..0x13f60). */

typedef struct DemoStep {
    int (*fn)(void);        /* step function, 0x51534 + 6*i (NULL ends table) */
    short scenario;         /* scenario number, 0x51538 + 6*i (interior of demo_steps) */
} DemoStep;

extern short demo_idle_timer;          /* 0x51530 */
extern unsigned short demo_step_index; /* 0x51532 */
extern DemoStep demo_steps[];          /* 0x51534; 0x51538 is demo_steps[0].scenario */

extern unsigned short demo_mode;       /* 0x5152c */
extern unsigned short dialog_modal;    /* 0x5152e */

int  DemoIdleTick(void);        /* 0x13e60 */
void DemoIdleTimerReset(void);  /* 0x13e94 */
int  DemoStepStartScenario(void); /* 0x13ea0 */
int  DemoStepMainMenu(void);    /* 0x13ef8 */
void DemoRun(void);             /* 0x13f0c */

#endif
