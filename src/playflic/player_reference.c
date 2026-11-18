/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 *
 * REFERENCE C (not built): the 20 functions of the object that are not
 * byte-identical yet.  They are kept here, complete and semantically
 * documented, so the remaining codegen differences are isolated to one file
 * per function.  See docs/subsystems/playflic.md section 6 for the exact
 * first difference of each one.
 */
#include "playflic.h"

/* ---------------- intro_load_credit_lines ---------------- */
/* @0x22d40  Scrolling loader of the credit text: advances the credit table
 * when the line timer reaches 1, and loops while the new delay is 0. */
void IntroLoadCreditLines(void)
{
    unsigned short count = line_count;
    unsigned short idx = line_index;
    unsigned short timer = line_timer;

    if (--timer == 0) {
        do {
            const CreditLine *c;

            idx++;
            line_index = idx;
            c = &credit_lines[idx];
            timer = c->delay;
            line_timer = timer;
            if (!*c->text) {
                count = 0;
                credit_line[0] = 0;
                credit_line[1] = 0;
                credit_line[2] = 0;
                line_count = count;
                memset(frame_image + flic_height * 0x140, 0, 0xfa00 - flic_height * 0x140);
            } else {
                credit_line[count] = c->text;
                line_count = count;
                credit_line_x[count] = (0x140 - TextWidth(cur_font, c->text)) / 2;
                count++;
            }
        } while (timer == 0);
        if (timer == 0xffff)
            credits_on = 0;
    }
    line_count = count;
    line_index = idx;
    line_timer = timer;
}

/* ---------------- intro_fade_step ---------------- */
/* @0x22eac */
void IntroFadeStep(void)
{
    unsigned char *d = fade_delta;
    unsigned char *p = palette;
    int i;

    for (i = 0; i < 0x2d0; i++, d++, p++) {
        if (*d > *p)
            *p = 0;
        else
            *p = *p - *d;
    }
    PaletteSet(0, 0x100, palette);
}

/* ---------------- intro_fade_frames ---------------- */
/* @0x22eec  Play `frames` animation frames while the palette fades from
 * palette_base to palette_target; returns 1 if the movie was aborted. */
short IntroFadeFrames(unsigned short frames)
{
    short i;

    for (i = 0; i < (short)frames; i++) {
        while (!frame_ready)
            IntroTick();
        frame_ready = 0;
        if (intro_abort)
            return 1;
        PaletteLerp(1, 0xef, i, frames);
    }
    return 0;
}

/* ---------------- intro_begin_flic ---------------- */
/* @0x22f48  Open the selected movie and set up the blit; p is the opcode
 * that follows (the return value). */
unsigned short *IntroBeginFlic(unsigned short *p)
{
    fade_frames = 0xffff;
    if (!FlicOpen(flic_files[flic_sel], frame_chunk, frame_image, 1, 0xef))
        return 0;
    flic_open = 1;
    if (skip_next_flic) {
        skip_next_flic = 0;
        return p;
    }
    intro_dest = (unsigned char *)0xa0000 + (0xc8 - flic_height) / 2 * 0x140;
    frame_size = flic_width * flic_height;
    return p;
}

/* ---------------- intro_op_play_frames ---------------- */
/* @0x23070  op 0x05: play the given number of frames, looping the movie. */
unsigned short *IntroOpPlayFrames(unsigned short *p)
{
    int n = *p;
    unsigned short *next = p + 1;
    int i;

    for (i = 0; i < n; i++) {
        IntroTick();
        if (intro_abort)
            break;
        if (frame == flic_frames + 1) {
            if (!IntroShowFirstFrame(next))
                return 0;
        } else if (!IntroNextFrame()) {
            return 0;
        }
    }
    return next;
}

/* ---------------- intro_op_play_to_end ---------------- */
/* @0x230e8  op 0x06: play to the end of the movie, fading out over the last
 * fade_frames frames. */
unsigned short *IntroOpPlayToEnd(unsigned short *p)
{
    unsigned f = fade_frames;

    while (frame < flic_frames) {
        IntroTick();
        if (intro_abort)
            break;
        if (!IntroNextFrame())
            return 0;
        if (f != 0xffff && flic_frames - frame <= f)
            IntroFadeStep();
    }
    return p;
}

/* ---------------- intro_op_wait_sound ---------------- */
/* @0x231cc  op 0x09: tick until the sound finishes. */
unsigned short *IntroOpWaitSound(unsigned short *p)
{
    while (SndActiveCount()) {
        if (intro_abort)
            break;
        IntroTick();
    }
    return p;
}

/* ---------------- intro_op_wait_frames ---------------- */
/* @0x231ec  op 0x0a: tick the given number of frames. */
unsigned short *IntroOpWaitFrames(unsigned short *p)
{
    unsigned short n = *p;
    unsigned short *next = p + 1;

    while (n) {
        if (intro_abort)
            break;
        IntroTick();
        if (frame_ready) {
            frame_ready = 0;
            n--;
        }
    }
    return next;
}

/* ---------------- intro_op_slide_layer ---------------- */
/* @0x23238  op 0x0c: slide layer 13 up one pixel per two frames until its
 * bottom edge reaches scroll_target. */
unsigned short *IntroOpSlideLayer(unsigned short *p)
{
    while (I16(&layers[13].y) + I16(&layers[13].h) - 1 != scroll_target) {
        while (!frame_ready)
            IntroTick();
        frame_ready = 0;
        do
            IntroTick();
        while (!frame_ready);
        frame_ready = 0;
        if (sound_timer && intro_tick_count > 0x14) {
            sound_timer = 0;
            SndPlay(0);
        }
        LayerInvalidate(0xd);
        layers[13].y--;
        LayerInvalidate(0xd);
        ScreenUpdate();
        return p - 1;
    }
    return p;
}

/* ---------------- intro_op_wait_anim ---------------- */
/* @0x232ec  op 0x0f: wait for the given number of animation frames. */
unsigned short *IntroOpWaitAnim(unsigned short *p)
{
    int n = *p;
    unsigned short *next = p + 1;

    frame_ready = 0;
    for (;;) {
        IntroTick();
        if (intro_abort)
            break;
        if (frame_ready) {
            if (--n == 0)
                break;
            frame_ready = 0;
        }
    }
    return next;
}

/* ---------------- intro_op_setup_fade ---------------- */
/* @0x23330  op 0x10: prepare a fade-out over the given number of frames. */
unsigned short *IntroOpSetupFade(unsigned short *p)
{
    unsigned short steps = *p;
    unsigned short *next = p + 1;
    int i;

    memcpy(fade_delta, palette, 0x2d0);
    fade_frames = steps;
    for (i = 0; i < 0x2d0; i++)
        fade_delta[i] = fade_delta[i] / fade_frames + 1;
    return next;
}

/* ---------------- intro_op_fade_in ---------------- */
/* @0x23410  op 0x14: fade from black to the loaded palette over N frames. */
unsigned short *IntroOpFadeIn(unsigned short *p)
{
    unsigned short n = *p;
    unsigned short *next = p + 1;

    memset(palette_base, 0, 0x300);
    memcpy(palette_target, palette, 0x300);
    if (IntroFadeFrames(n))
        next = 0;
    return next;
}

/* ---------------- intro_op_fade_out ---------------- */
/* @0x23458  op 0x15: fade from the loaded palette to black over N frames. */
unsigned short *IntroOpFadeOut(unsigned short *p)
{
    unsigned short n = *p;
    unsigned short *next = p + 1;

    memcpy(palette_base, palette, 0x300);
    memset(palette_target, 0, 0x300);
    if (IntroFadeFrames(n))
        next = 0;
    return next;
}

/* ---------------- intro_op_credit_area ---------------- */
/* @0x234d8  op 0x17: set up the three-line credit area. */
unsigned short *IntroOpCreditArea(unsigned short *p)
{
    unsigned short lh;

    line_index = 0xffff;
    lh = cur_font->rows + 2;
    line_height = lh;
    intro_dest -= lh * 640;
    frame_size += (lh * 3 + 2) * 0x140;
    return p;
}

/* ---------------- intro_op_start_credits ---------------- */
/* @0x23530  op 0x18: load the next three credit lines and show them. */
unsigned short *IntroOpStartCredits(unsigned short *p)
{
    int i;

    credits_on = 1;
    for (i = 0;; i++) {
        line_index++;
        line_timer = credit_lines[line_index].delay;
        credit_line[i] = credit_lines[line_index].text;
        credit_line_x[i] = (0x140 - TextWidth(cur_font, credit_lines[line_index].text)) / 2;
        if (line_timer)
            break;
    }
    line_count = i + 1;
    for (; i < 3; i++)
        credit_line[i] = 0;
    return p;
}

/* ---------------- intro_run_script ---------------- */
/* @0x23668  Run one intro script: install the input and frame callbacks,
 * allocate the two 64000-byte buffers, dispatch the opcodes until one returns
 * 0 or the movie is skipped, then tear everything down.  Returns intro_abort. */
unsigned short IntroRunScript(const unsigned short *script, int blank_on_abort)
{
    const unsigned short *p = script;
    unsigned short *next;

    intro_abort = 0;
    frame_ready = 1;
    abort_request = 0;
    UiInputInit();
    EvtPump();
    event_handlers[0] = IntroCheckSkip;
    event_handlers[5] = IntroCheckSkip;
    event_handlers[7] = IntroCheckSkip;
    event_handlers[8] = (void (*)(Event *))IntroFrame;
    intro_tick_count = 0;
    frame_chunk = GdsAlloc(0xfa00);
    frame_image = GdsAlloc(0xfa00);
    memset(frame_image, 0, 0xfa00);
    credits_on = 0;
    intro_bitmap.data = frame_image;
    cur_bitmap = &intro_bitmap;
    cur_font = (Font *)0x59220;
    TextSetColorBase(0xf3);
    skip_next_flic = 0;
    for (;;) {
        next = script_ops[*(unsigned char *)p](p + 1);
        p = next;
        IntroTick();
        if (!next || intro_abort)
            break;
    }
    if (flic_open) {
        flic_open = 0;
        FlicClose();
    }
    GdsFree(frame_chunk);
    GdsFree(frame_image);
    if (intro_abort && blank_on_abort)
        memset((void *)0xa0000, 0, 0xfa00);
    return intro_abort;
}

/* ---------------- credits_tick_a ---------------- */
/* @0x237a0  First credits animation variant: one GRP frame per intro frame
 * on layer 14, and every second frame the layer-15 and layer-16 sequences. */
void CreditsTickA(void)
{
    if (intro_tick_count == 0) {
        credit_tick = 0;
        credit_step_b = 0;
        credit_step_c = 1;
        credit_frame_c = credit_steps1[0];
        credit_step_d = 1;
        credit_frame_d = credit_steps2[0];
    }
    if (intro_tick_count == credit_tick)
        return;
    credit_tick = intro_tick_count;
    CreditDrawA(credit_step_b);
    credit_step_b++;
    if (credit_step_b == 0x1f)
        credit_step_b = 0;
    if (intro_tick_count & 1)
        return;
    CreditDrawB(credit_frames1[credit_frame_c]);
    credit_frame_c++;
    if (credit_frame_c % 10 == 0) {
        credit_step_c++;
        if (credit_step_c == 0x14)
            credit_step_c = 0;
        credit_frame_c = credit_steps1[credit_step_c];
    }
    CreditDrawC(credit_frames2[credit_frame_d]);
    credit_frame_d++;
    if (credit_frame_d % 10 == 0) {
        credit_step_d++;
        if (credit_step_d == 0x14)
            credit_step_d = 0;
        credit_frame_d = credit_steps2[credit_step_d];
    }
}

/* ---------------- credits_tick_b ---------------- */
/* @0x2393c  Second credits animation variant: layers 14 and 15 share one
 * frame number, layers 16 and 17 have their own sequences. */
void CreditsTickB(void)
{
    if (intro_tick_count == 0) {
        credit_tick = 0;
        credit_step_b = 0;
        credit_step_c = 1;
        credit_frame_c = credit_steps3[0];
        credit_step_d = 1;
        credit_frame_d = credit_steps4[0];
    }
    if (intro_tick_count == credit_tick)
        return;
    credit_tick = intro_tick_count;
    CreditDrawA(credit_step_b);
    CreditDrawB(credit_step_b);
    credit_step_b++;
    if (credit_step_b == 0x15)
        credit_step_b = 0;
    if (intro_tick_count & 1)
        return;
    CreditDrawC(credit_frames3[credit_frame_c]);
    credit_frame_c++;
    if (credit_frame_c % 10 == 0) {
        credit_step_c++;
        if (credit_step_c == 0x14)
            credit_step_c = 0;
        credit_frame_c = credit_steps3[credit_step_c];
    }
    CreditDrawD(credit_frames4[credit_frame_d]);
    credit_frame_d++;
    if (credit_frame_d % 10 == 0) {
        credit_step_d++;
        if (credit_step_d == 0x14)
            credit_step_d = 0;
        credit_frame_d = credit_steps4[credit_step_d];
    }
}

/* ---------------- intro_play ---------------- */
/* @0x23ae0  Top level: play the epilogue script, then either fade out or run
 * the extra sequence (a bitmap layer fades in from resource 0x108 to 0x106). */
void IntroPlay(void)
{
    Bitmap bm;
    unsigned short done;

    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].active = 0;
    ScreenUpdate();
    ResourceBegin(0x106, 0);
    ResourceRead(palette, 0);
    SndLoadTable(intro_sounds);
    MusicStart(0xe);
    ResourceBegin(0x107, 0);
    ResourceReadHeaderBody(&bm, 0);
    intro_tick = 0;
    done = IntroRunScript(cfg_dig_driver == 0xffff ? script_no_dig : script_epilogue, 0);
    if (!abort_request)
        done = 1;
    if (!done) {
        layers[2].active = 0;
        layers[14].x = 0;
        layers[14].y = 0;
        layers[14].w = 0x140;
        layers[14].h = 0xc8;
        layers[14].data = &bm;
        layers[14].draw = BitmapBlit;
        layers[14].active = 1;
        LayerInvalidate(0xe);
        ScreenUpdate();
        ResourceBegin(0x108, 0);
        ResourceRead(palette_base, 0);
        ResourceBegin(0x106, 0);
        ResourceRead(palette_target, 0);
        IntroFadeFrames(0x1b);
    }
    if (done) {
        PaletteFadeOut(1);
    } else {
        intro_music_started = 1;
        palette_faded = 0;
    }
    layers[14].active = 0;
    ResourceFreeBody(&bm);
    SndReleaseAll();
    if (!intro_music_started)
        MusicClear();
    SndLoadTable(0);
}

/* ---------------- flic_overrun ---------------- */
/* @0x23cf4  Unreachable stub: the 'flic overrun' fatal error. */
void FlicOverrun(void)
{
    FatalError("flic overrun");
}
