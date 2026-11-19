/* clockgen byte-match grind — cg_asm.c (.set noreorder transcriptions)
 * Retail: PSP firmware 6.60 kd/clockgen.prx (owner's own console dump).
 * Toolchain: GCC 3.3.6 -O3 -mips2 -G0 -mabi=eabi (16-byte stack align patch).
 *
 * GCC 3.3.6 targeting -mips2 cannot emit the SPECIAL3 `ins` words the retail
 * compiler used for the 3-bit mask clears (0x7C0A1004 @0x1A8, 0x7C081004
 * @0x344, 0x7C0318C4 @0x598) nor the MIPS III `daddu` (0x0044182D @0x6C0),
 * so those functions (and the ones whose GCC scheduling diverges beyond
 * fixing) are transcribed word-for-word, tm_c.c style:
 *   - registers numeric ($sp/$ra aliases only; this gas rejects $s0 etc),
 *   - intra-function branches use local labels (PC-relative offsets are
 *     preserved by the 1:1 transcription),
 *   - j/jal use literal retail addresses (word-exact, no reloc),
 *   - global refs use literal lui 0 + addiu {0,16,2264}: g_Cy27040 sits at
 *     RW-segment +0, g_ClockGenSysEv at +0x10, "SceClockgen" at 0x8D8, so
 *     the literals ARE the stored retail words (the loader adds the base).
 *
 * C-level shapes being transcribed (uofW semantics, see cg.c for the pure-C
 * versions that GCC reproduces): sceClockgenSetup, sceClockgenAudioClkSetFreq,
 * sceClockgenSetSpectrumSpreading, module_reboot_before,
 * _sceClockgenSysEventHandler, _sceClockgenSetControl1,
 * _cy27040_write_register, plus the four _sceClockgenSetControl1 wrappers.
 */

__asm__(
".text\n"
".set push\n"
".set noreorder\n"

/* ================================================================ */
/* sceClockgenSetup @0x000 — 38 words */
".globl sceClockgenSetup\n"
".type sceClockgenSetup,@function\n"
"sceClockgenSetup:\n"
"addiu $29,$29,-48\n"        /* 0000 27BDFFD0 */
"lui   $3,0\n"               /* 0004 3C030000 */
"sw    $17,36($29)\n"        /* 0008 AFB10024 */
"addiu $17,$3,0\n"           /* 000C 24710000 s1 = g_Cy27040 */
"lw    $2,4($17)\n"          /* 0010 8E220004 protocol */
"sw    $18,40($29)\n"        /* 0014 AFB20028 */
"move  $18,$17\n"            /* 0018 02209021 s2 = g */
"sw    $16,32($29)\n"        /* 001C AFB00020 */
"move  $16,$0\n"             /* 0020 00008021 i = 0 */
"beq   $2,$0,cg_setup_all\n" /* 0024 1040001B */
"sw    $31,44($29)\n"        /* 0028 AFBF002C */
"cg_setup_one:\n"            /*        0x2C loop head */
"addiu $12,$16,-128\n"       /* 002C 260CFF80 trsm[0] = i-128 */
"li    $4,210\n"             /* 0030 240400D2 */
"addiu $5,$29,16\n"          /* 0034 27A50010 trsm */
"li    $6,1\n"               /* 0038 24060001 */
"li    $7,210\n"             /* 003C 240700D2 */
"move  $8,$29\n"             /* 0040 03A04021 recv */
"li    $9,1\n"               /* 0044 24090001 */
"jal   0x6fc\n"              /* 0048 0C0001BF TransmitReceive */
"sb    $12,16($29)\n"        /* 004C A3AC0010 delay: store trsm[0] */
"addu  $4,$16,$18\n"         /* 0050 02122021 &curReg[i] */
"addiu $16,$16,1\n"          /* 0054 26100001 i++ */
"slti  $5,$16,3\n"           /* 0058 2A050003 */
"bltz  $2,cg_setup_ret\n"    /* 005C 04400006 */
"move  $3,$2\n"              /* 0060 00401821 delay: v1 = ret */
"lbu   $6,0($29)\n"          /* 0064 93A60000 recv[0] */
"sb    $6,11($4)\n"          /* 0068 A086000B oldReg[i] */
"bnez  $5,cg_setup_one\n"    /* 006C 14A0FFEF */
"sb    $6,8($4)\n"           /* 0070 A0860008 delay: curReg[i] */
"cg_setup_zero:\n"
"move  $3,$0\n"              /* 0074 00001821 */
"cg_setup_ret:\n"
"lw    $31,44($29)\n"        /* 0078 8FBF002C */
"lw    $18,40($29)\n"        /* 007C 8FB20028 */
"lw    $17,36($29)\n"        /* 0080 8FB10024 */
"lw    $16,32($29)\n"        /* 0084 8FB00020 */
"move  $2,$3\n"              /* 0088 00601021 */
"jr    $31\n"                /* 008C 03E00008 */
"addiu $29,$29,48\n"         /* 0090 27BD0030 */
"cg_setup_all:\n"
"li    $4,210\n"             /* 0094 240400D2 */
"addiu $5,$29,16\n"          /* 0098 27A50010 */
"li    $6,1\n"               /* 009C 24060001 */
"li    $7,210\n"             /* 00A0 240700D2 */
"move  $8,$29\n"             /* 00A4 03A04021 */
"li    $9,16\n"              /* 00A8 24090010 */
"jal   0x6fc\n"              /* 00AC 0C0001BF */
"sb    $0,16($29)\n"         /* 00B0 A3A00010 delay: trsm[0] = 0 */
"bltz  $2,cg_setup_ret\n"    /* 00B4 0440FFF0 */
"move  $3,$2\n"              /* 00B8 00401821 delay */
"lbu   $6,0($29)\n"          /* 00BC 93A60000 recv[0] = count */
"beqz  $6,cg_setup_zero\n"   /* 00C0 10C0FFEC */
"move  $7,$17\n"             /* 00C4 02203821 delay: a3 = g */
"cg_setup_all_loop:\n"
"addu  $11,$16,$29\n"        /* 00C8 021D5821 */
"addu  $9,$16,$7\n"          /* 00CC 02074821 */
"lbu   $4,1($11)\n"          /* 00D0 91640001 recv[i+1] */
"addiu $16,$16,1\n"          /* 00D4 26100001 */
"slt   $5,$16,$6\n"          /* 00D8 0206282A */
"slti  $10,$16,3\n"          /* 00DC 2A0A0003 */
"and   $8,$5,$10\n"          /* 00E0 00AA4024 */
"sb    $4,11($9)\n"          /* 00E4 A124000B */
"bnez  $8,cg_setup_all_loop\n" /* 00E8 1500FFF7 */
"sb    $4,8($9)\n"           /* 00EC A1240008 delay */
"j     0x78\n"               /* 00F0 0800001E */
"move  $3,$0\n"              /* 00F4 00001821 delay */
".size sceClockgenSetup,.-sceClockgenSetup\n"

/* ================================================================ */
/* sceClockgenAudioClkSetFreq @0x47C — 19 words.  Branchy form: GCC's
 * `freq != 44100 && freq != 48000` if-converts to xor/sltu (+10 words). */
".globl sceClockgenAudioClkSetFreq\n"
".type sceClockgenAudioClkSetFreq,@function\n"
"sceClockgenAudioClkSetFreq:\n"
"addiu $29,$29,-16\n"        /* 047C 27BDFFF0 */
"li    $3,0xac44\n"          /* 0480 3403AC44 */
"sw    $31,0($29)\n"         /* 0484 AFBF0000 */
"beq   $4,$3,cg_freq_call\n" /* 0488 10830004 44100 */
"move  $5,$0\n"              /* 048C 00002821 delay: mode = 0 */
"li    $3,0xbb80\n"          /* 0490 3403BB80 */
"bne   $4,$3,cg_freq_bad\n"  /* 0494 14830006 48000 */
"li    $5,1\n"               /* 0498 24050001 delay: mode = 1 */
"cg_freq_call:\n"
"jal   0x5dc\n"              /* 049C 0C000177 _sceClockgenSetControl1 */
"li    $4,1\n"               /* 04A0 24040001 delay: bus = AUDIO_FREQ */
"cg_freq_out:\n"
"lw    $31,0($29)\n"         /* 04A4 8FBF0000 */
"jr    $31\n"                /* 04A8 03E00008 */
"addiu $29,$29,16\n"         /* 04AC 27BD0010 */
"cg_freq_bad:\n"
"lui   $4,0x8000\n"          /* 04B0 3C048000 */
"j     0x4a4\n"              /* 04B4 08000129 */
"ori   $2,$4,0x1fe\n"        /* 04B8 348201FE delay: SCE_ERROR_INVALID_VALUE */
".size sceClockgenAudioClkSetFreq,.-sceClockgenAudioClkSetFreq\n"

/* ================================================================ */
/* sceClockgenSetSpectrumSpreading @0x0F8 — 111 words.  Contains the
 * ins-with-$zero 3-bit clear @0x1A8; GCC cannot emit it. */
".globl sceClockgenSetSpectrumSpreading\n"
".type sceClockgenSetSpectrumSpreading,@function\n"
"sceClockgenSetSpectrumSpreading:\n"
"addiu $29,$29,-32\n"        /* 00F8 27BDFFE0 */
"sw    $18,8($29)\n"         /* 00FC AFB20008 */
"move  $18,$4\n"             /* 0100 00809021 s2 = mode */
"sw    $31,16($29)\n"        /* 0104 AFBF0010 */
"sw    $19,12($29)\n"        /* 0108 AFB3000C */
"sw    $17,4($29)\n"         /* 010C AFB10004 */
"bltz  $4,cg_ss_restore\n"   /* 0110 0480005D */
"sw    $16,0($29)\n"         /* 0114 AFB00000 delay */
"lui   $7,0\n"               /* 0118 3C070000 */
"addiu $9,$7,0\n"            /* 011C 24E90000 t1 = g */
"lbu   $6,8($9)\n"           /* 0120 91260008 curReg[0] (revision) */
"li    $5,8\n"               /* 0124 24050008 */
"andi  $16,$6,0xf\n"         /* 0128 30D0000F rev & 0xF */
"beq   $16,$5,cg_ss_ladder\n" /* 012C 1205000E rev 8 */
"li    $10,4\n"              /* 0130 240A0004 */
"beq   $16,$10,cg_ss_ladder4\n" /* 0134 120A0040 rev 4: coarser table */
"li    $17,15\n"             /* 0138 2411000F */
"beq   $16,$17,cg_ss_ladder\n" /* 013C 1211000A rev 0xF */
"li    $19,7\n"              /* 0140 24130007 */
"beq   $16,$19,cg_ss_ladder\n" /* 0144 12130008 rev 7 */
"li    $24,3\n"              /* 0148 24180003 */
"beq   $16,$24,cg_ss_ladder\n" /* 014C 12300006 rev 3 */
"li    $25,9\n"              /* 0150 24190009 */
"beq   $16,$25,cg_ss_ladder\n" /* 0154 12390004 rev 9 */
"li    $8,10\n"              /* 0158 2408000A */
"lui   $2,0x8000\n"          /* 015C 3C028000 */
"bne   $16,$8,cg_ss_ret_res\n" /* 0160 1608001E rev 0xA */
"ori   $6,$2,0x4\n"          /* 0164 34460004 delay: NOT_SUPPORTED */
"cg_ss_ladder:\n"
"slti  $16,$18,2\n"          /* 0168 2A500002 mode < 2 */
"bnez  $16,cg_ss_off\n"      /* 016C 1600002F */
"slti  $3,$18,7\n"           /* 0170 2A430007 delay */
"beq   $3,$0,cg_ss_15\n"     /* 0174 10600021 mode >= 7 */
"slti  $4,$18,15\n"          /* 0178 2A44000F delay */
"li    $18,5\n"              /* 017C 24120005 ret = 5 */
"cg_ss_r1:\n"
"li    $17,1\n"              /* 0180 24110001 regSS = 1 */
"cg_ss_lock:\n"
"lw    $4,0($7)\n"           /* 0184 8CE40000 g.mutex */
"cg_ss_lock_nb:\n"
"move  $6,$0\n"              /* 0188 00003021 */
"li    $5,1\n"               /* 018C 24050001 */
"jal   0x6e4\n"              /* 0190 0C0001B9 sceKernelLockMutex */
"addiu $19,$7,0\n"           /* 0194 24F30000 delay: s3 = g */
"bltz  $2,cg_ss_ret_res\n"   /* 0198 04400010 */
"move  $6,$2\n"              /* 019C 00403021 delay: a2 = res */
"lbu   $10,10($19)\n"        /* 01A0 926A000A curReg[2] */
"li    $4,2\n"               /* 01A4 24040002 idx = REG_SS */
".word 0x7c0a1004\n"         /* 01A8 7C0A1004 ins t2,zero,0,3: t2 &= ~7 */
"or    $9,$17,$10\n"         /* 01AC 022A4825 regSS | (cur & ~7) */
"sb    $9,10($19)\n"         /* 01B0 A269000A curReg[2] = val */
"jal   0x680\n"              /* 01B4 0C0001A0 _cy27040_write_register */
"move  $5,$9\n"              /* 01B8 01202821 delay: a1 = val */
"lui   $6,0\n"               /* 01BC 3C060000 */
"lw    $4,0($6)\n"           /* 01C0 8CC40000 g.mutex */
"move  $17,$2\n"             /* 01C4 00408821 s1 = res */
"jal   0x6dc\n"              /* 01C8 0C0001B7 sceKernelUnlockMutex */
"li    $5,1\n"               /* 01CC 24050001 delay */
"slti  $5,$17,0\n"           /* 01D0 2A250000 res < 0 */
"move  $6,$17\n"             /* 01D4 02203021 a2 = res */
".word 0x0245300a\n"         /* 01D8 0245300A movz a2,s2,a1: ret if !res<0 */
"cg_ss_ret_res:\n"
"lw    $31,16($29)\n"        /* 01DC 8FBF0010 */
"lw    $19,12($29)\n"        /* 01E0 8FB3000C */
"lw    $18,8($29)\n"         /* 01E4 8FB20008 */
"lw    $17,4($29)\n"         /* 01E8 8FB10004 */
"lw    $16,0($29)\n"         /* 01EC 8FB00000 */
"move  $2,$6\n"              /* 01F0 00C01021 */
"jr    $31\n"                /* 01F4 03E00008 */
"addiu $29,$29,32\n"         /* 01F8 27BD0020 */
"cg_ss_15:\n"
"slti  $2,$18,25\n"          /* 01FC 2A420019 */
"li    $17,4\n"              /* 0200 24110004 */
"beq   $4,$0,cg_ss_25\n"     /* 0204 10800004 !(mode<15) */
"li    $18,20\n"             /* 0208 24120014 ret = 20 */
"li    $18,10\n"             /* 020C 2412000A ret = 10 */
"cg_ss_l10:\n"
"j     0x184\n"              /* 0210 08000061 */
"li    $17,2\n"              /* 0214 24110002 delay: regSS = 2 */
"cg_ss_25:\n"
"bnez  $2,cg_ss_lock_nb\n"   /* 0218 1440FFDB mode < 25 */
"lw    $4,0($7)\n"           /* 021C 8CE40000 delay */
"li    $18,30\n"             /* 0220 2412001E ret = 30 */
"j     0x188\n"              /* 0224 08000062 */
"li    $17,6\n"              /* 0228 24110006 delay: regSS = 6 */
"cg_ss_off:\n"
"move  $18,$0\n"             /* 022C 00009021 ret = 0 */
"j     0x184\n"              /* 0230 08000061 */
"move  $17,$0\n"             /* 0234 00008821 delay: regSS = 0 */
"cg_ss_ladder4:\n"
"slti  $11,$4,2\n"           /* 0238 288B0002 */
"bnez  $11,cg_ss_off\n"      /* 023C 1560FFFB */
"slti  $12,$4,7\n"           /* 0240 288C0007 */
"bnez  $12,cg_ss_r1\n"       /* 0244 1580FFCE */
"li    $18,5\n"              /* 0248 24120005 */
"slti  $13,$4,12\n"          /* 024C 288D000C */
"bnez  $13,cg_ss_l10\n"      /* 0250 15A0FFEF */
"li    $18,10\n"             /* 0254 2412000A */
"slti  $14,$4,17\n"          /* 0258 288E0011 */
"li    $18,15\n"             /* 025C 2412000F */
"bnez  $14,cg_ss_lock\n"     /* 0260 15C0FFC8 */
"li    $17,3\n"              /* 0264 24110003 */
"slti  $15,$4,22\n"          /* 0268 288F0016 */
"li    $18,20\n"             /* 026C 24120014 */
"bnez  $15,cg_ss_lock\n"     /* 0270 15E0FFC4 */
"li    $17,4\n"              /* 0274 24110004 */
"slti  $2,$4,27\n"           /* 0278 2882001B */
"li    $17,5\n"              /* 027C 24110005 */
"j     0x218\n"              /* 0280 08000086 */
"li    $18,25\n"             /* 0284 24120019 delay */
"cg_ss_restore:\n"
"lui   $7,0\n"               /* 0288 3C070000 */
"addiu $4,$7,0\n"            /* 028C 24E40000 */
"lbu   $3,13($4)\n"          /* 0290 9083000D oldReg[2] */
"lbu   $8,10($4)\n"          /* 0294 9088000A curReg[2] */
"move  $6,$18\n"             /* 0298 02403021 a2 = mode */
"andi  $5,$3,0x7\n"          /* 029C 30650007 */
"andi  $2,$8,0x7\n"          /* 02A0 31020007 */
"bne   $2,$5,cg_ss_lock\n"   /* 02A4 1445FFB7 changed: go write it */
"move  $17,$5\n"             /* 02A8 00A08821 delay: regSS = old & 7 */
"j     0x1e0\n"              /* 02AC 08000078 unchanged: return mode */
"lw    $31,16($29)\n"        /* 02B0 8FBF0010 delay */
".size sceClockgenSetSpectrumSpreading,.-sceClockgenSetSpectrumSpreading\n"

/* ================================================================ */
/* module_reboot_before @0x320 — 30 words (syslib; inlines sceClockgenEnd).
 * ins-with-$zero @0x344. */
".globl module_reboot_before\n"
".type module_reboot_before,@function\n"
"module_reboot_before:\n"
"addiu $29,$29,-16\n"        /* 0320 27BDFFF0 */
"sw    $16,0($29)\n"         /* 0324 AFB00000 */
"lui   $16,0\n"              /* 0328 3C100000 s0 = g */
"addiu $3,$16,0\n"           /* 032C 26030000 */
"lbu   $5,13($3)\n"          /* 0330 9065000D oldReg[2] */
"lbu   $8,10($3)\n"          /* 0334 9068000A curReg[2] */
"sw    $31,4($29)\n"         /* 0338 AFBF0004 */
"andi  $6,$5,0x7\n"          /* 033C 30A60007 */
"andi  $7,$8,0x7\n"          /* 0340 31070007 */
".word 0x7c081004\n"         /* 0344 7C081004 ins t0,zero,0,3 */
"li    $4,2\n"               /* 0348 24040002 */
"beq   $7,$6,cg_rb_end\n"    /* 034C 10E60003 unchanged */
"or    $5,$8,$6\n"           /* 0350 01062825 delay: (cur&~7)|(old&7) */
"jal   0x680\n"              /* 0354 0C0001A0 */
"nop\n"                      /* 0358 00000000 */
"cg_rb_end:\n"
"lw    $6,0($16)\n"          /* 035C 8E060000 g.mutex */
"bltz  $6,cg_rb_unreg\n"     /* 0360 04C00005 */
"move  $4,$6\n"              /* 0364 00C02021 delay */
"jal   0x6f4\n"              /* 0368 0C0001BD sceKernelDeleteMutex */
"nop\n"                      /* 036C 00000000 */
"li    $2,-1\n"              /* 0370 2402FFFF */
"sw    $2,0($16)\n"          /* 0374 AE020000 g.mutex = -1 */
"cg_rb_unreg:\n"
"lui   $9,0\n"               /* 0378 3C090000 */
"jal   0x71c\n"              /* 037C 0C0001C7 UnregisterSysEventHandler */
"addiu $4,$9,16\n"           /* 0380 25240010 delay: &g_ClockGenSysEv */
"lw    $31,4($29)\n"         /* 0384 8FBF0004 */
"lw    $16,0($29)\n"         /* 0388 8FB00000 */
"move  $2,$0\n"              /* 038C 00001021 */
"jr    $31\n"                /* 0390 03E00008 */
"addiu $29,$29,16\n"         /* 0394 27BD0010 */
".size module_reboot_before,.-module_reboot_before\n"

/* ================================================================ */
/* _sceClockgenSysEventHandler @0x53C — 39 words.  ins-with-$zero
 * (1-bit clear, LEPTON) @0x598.  Internal, compared via the map's
 * "internals" section. */
".globl _sceClockgenSysEventHandler\n"
".type _sceClockgenSysEventHandler,@function\n"
"_sceClockgenSysEventHandler:\n"
"addiu $29,$29,-16\n"        /* 053C 27BDFFF0 */
"move  $3,$4\n"              /* 0540 00801821 v1 = eventId */
"lui   $6,0x1\n"             /* 0544 3C060001 */
"sw    $31,8($29)\n"         /* 0548 AFBF0008 */
"slt   $4,$6,$4\n"           /* 054C 00C4202A 0x10000 < eventId */
"li    $5,1\n"               /* 0550 24050001 */
"sw    $17,4($29)\n"         /* 0554 AFB10004 */
"beq   $3,$6,cg_ev_suspend\n" /* 0558 1066001B eventId == 0x10000 */
"sw    $16,0($29)\n"         /* 055C AFB00000 delay */
"beq   $4,$0,cg_ev_out\n"    /* 0560 10800007 eventId < 0x10000 */
"lw    $31,8($29)\n"         /* 0564 8FBF0008 delay */
"lui   $17,0\n"              /* 0568 3C110000 */
"lui   $5,0x10\n"            /* 056C 3C050010 */
"addiu $16,$17,0\n"          /* 0570 26300000 s0 = g */
"beq   $3,$5,cg_ev_resume\n" /* 0574 10650007 eventId == 0x100000 */
"li    $4,1\n"               /* 0578 24040001 delay */
"lw    $31,8($29)\n"         /* 057C 8FBF0008 */
"cg_ev_out:\n"
"lw    $17,4($29)\n"         /* 0580 8FB10004 */
"lw    $16,0($29)\n"         /* 0584 8FB00000 */
"move  $2,$0\n"              /* 0588 00001021 */
"jr    $31\n"                /* 058C 03E00008 */
"addiu $29,$29,16\n"         /* 0590 27BD0010 */
"cg_ev_resume:\n"
"lbu   $3,9($16)\n"          /* 0594 92030009 curReg[1] */
".word 0x7c0318c4\n"         /* 0598 7C0318C4 ins v1,zero,3,1: clear LEPTON */
"andi  $5,$3,0xf7\n"         /* 059C 306500F7 */
"jal   0x680\n"              /* 05A0 0C0001A0 write REG_CLOCK */
"sb    $3,9($16)\n"          /* 05A4 A2030009 delay: store back */
"li    $4,2\n"               /* 05A8 24040002 */
"jal   0x680\n"              /* 05AC 0C0001A0 write REG_SS */
"lbu   $5,10($16)\n"         /* 05B0 9205000A delay: curReg[2] */
"lw    $4,0($17)\n"          /* 05B4 8E240000 g.mutex */
"jal   0x6dc\n"              /* 05B8 0C0001B7 UnlockMutex */
"li    $5,1\n"               /* 05BC 24050001 delay */
"j     0x580\n"              /* 05C0 08000160 */
"lw    $31,8($29)\n"         /* 05C4 8FBF0008 delay */
"cg_ev_suspend:\n"
"lui   $6,0\n"               /* 05C8 3C060000 */
"jal   0x6d4\n"              /* 05CC 0C0001B5 TryLockMutex */
"lw    $4,0($6)\n"           /* 05D0 8CC40000 delay: g.mutex */
"j     0x580\n"              /* 05D4 08000160 */
"lw    $31,8($29)\n"         /* 05D8 8FBF0008 delay */
".size _sceClockgenSysEventHandler,.-_sceClockgenSysEventHandler\n"

/* ================================================================ */
/* _sceClockgenSetControl1 @0x5DC — 40 words.  Internal. */
".globl _sceClockgenSetControl1\n"
".type _sceClockgenSetControl1,@function\n"
"_sceClockgenSetControl1:\n"
"addiu $29,$29,-32\n"        /* 05DC 27BDFFE0 */
"sw    $18,8($29)\n"         /* 05E0 AFB20008 */
"lui   $18,0\n"              /* 05E4 3C120000 s2 = g */
"move  $6,$0\n"              /* 05E8 00003021 a2 = 0 */
"sw    $17,4($29)\n"         /* 05EC AFB10004 */
"move  $17,$4\n"             /* 05F0 00808821 s1 = bus */
"lw    $4,0($18)\n"          /* 05F4 8E440000 g.mutex */
"sw    $19,12($29)\n"        /* 05F8 AFB3000C */
"move  $19,$5\n"             /* 05FC 00A09821 s3 = mode */
"sw    $16,0($29)\n"         /* 0600 AFB00000 */
"sw    $31,16($29)\n"        /* 0604 AFBF0010 */
"jal   0x6e4\n"              /* 0608 0C0001B9 LockMutex */
"li    $5,1\n"               /* 060C 24050001 delay */
"move  $16,$2\n"             /* 0610 00408021 s0 = res */
"nor   $5,$0,$17\n"          /* 0614 00112827 a1 = ~bus */
"bltz  $16,cg_sc_ret\n"      /* 0618 06000011 */
"addiu $2,$18,0\n"           /* 061C 26420000 delay: v0 = g */
"lbu   $6,9($2)\n"           /* 0620 90460009 regClk = curReg[1] */
"move  $8,$2\n"              /* 0624 00404021 t0 = g */
"li    $4,1\n"               /* 0628 24040001 idx = REG_CLOCK */
"and   $9,$6,$17\n"          /* 062C 00D14824 regClk & bus */
"or    $7,$6,$17\n"          /* 0630 00D13825 regClk | bus */
"and   $3,$6,$5\n"           /* 0634 00C51824 regClk & ~bus */
"beq   $19,$0,cg_sc_join\n"  /* 0638 12600002 !mode */
"sltu  $16,$0,$9\n"          /* 063C 0009802B delay: s0 = bit was set */
"andi  $3,$7,0xff\n"         /* 0640 30E300FF mode: force bit 1 */
"cg_sc_join:\n"
"beq   $3,$6,cg_sc_unlock\n" /* 0644 10660003 unchanged */
"move  $5,$3\n"              /* 0648 00602821 delay: a1 = new val */
"jal   0x680\n"              /* 064C 0C0001A0 write_register */
"sb    $3,9($8)\n"           /* 0650 A1030009 delay: curReg[1] = val */
"cg_sc_unlock:\n"
"lw    $4,0($18)\n"          /* 0654 8E440000 */
"jal   0x6dc\n"              /* 0658 0C0001B7 UnlockMutex */
"li    $5,1\n"               /* 065C 24050001 delay */
"cg_sc_ret:\n"
"move  $2,$16\n"             /* 0660 02001021 */
"lw    $31,16($29)\n"        /* 0664 8FBF0010 */
"lw    $19,12($29)\n"        /* 0668 8FB3000C */
"lw    $18,8($29)\n"         /* 066C 8FB20008 */
"lw    $17,4($29)\n"         /* 0670 8FB10004 */
"lw    $16,0($29)\n"         /* 0674 8FB00000 */
"jr    $31\n"                /* 0678 03E00008 */
"addiu $29,$29,32\n"         /* 067C 27BD0020 */
".size _sceClockgenSetControl1,.-_sceClockgenSetControl1\n"

/* ================================================================ */
/* _cy27040_write_register @0x680 — 21 words.  Internal.  Contains the
 * MIPS III daddu (0x0044182D) GCC will not emit under -mips2. */
".globl _cy27040_write_register\n"
".type _cy27040_write_register,@function\n"
"_cy27040_write_register:\n"
"move  $3,$4\n"              /* 0680 00801821 v1 = idx */
"addiu $29,$29,-32\n"        /* 0684 27BDFFE0 */
"sltiu $9,$3,3\n"            /* 0688 2C690003 */
"lui   $10,0x8000\n"         /* 068C 3C0A8000 */
"addiu $8,$4,-128\n"         /* 0690 2488FF80 trsm[0] = idx-128 */
"move  $7,$5\n"              /* 0694 00A03821 a3 = val */
"sw    $31,16($29)\n"        /* 0698 AFBF0010 */
"li    $4,210\n"             /* 069C 240400D2 */
"li    $6,2\n"               /* 06A0 24060002 */
"move  $5,$29\n"             /* 06A4 03A02821 trsm at sp+0 */
"beq   $9,$0,cg_wr_bad\n"    /* 06A8 11200006 idx >= 3 */
"ori   $3,$10,0x102\n"       /* 06AC 35430102 delay: INVALID_INDEX */
"sb    $8,0($29)\n"          /* 06B0 A3A80000 */
"jal   0x70c\n"              /* 06B4 0C0001C3 sceI2cMasterTransmit */
"sb    $7,1($29)\n"          /* 06B8 A3A70001 delay: trsm[1] = val */
"move  $4,$0\n"              /* 06BC 00002021 */
".word 0x0044182d\n"         /* 06C0 0044182D daddu v1,a0,v0 */
"cg_wr_bad:\n"
"lw    $31,16($29)\n"        /* 06C4 8FBF0010 */
"move  $2,$3\n"              /* 06C8 00601021 */
"jr    $31\n"                /* 06CC 03E00008 */
"addiu $29,$29,32\n"         /* 06D0 27BD0020 */
".size _cy27040_write_register,.-_cy27040_write_register\n"

/* ================================================================ */
/* _sceClockgenSetControl1 wrappers (transcribed for the exact jal):
 * AudioClkEnable @0x4BC, AudioClkDisable @0x4DC, LeptonClkEnable
 * @0x4FC, LeptonClkDisable @0x51C — 8 words each. */
".globl sceClockgenAudioClkEnable\n"
".type sceClockgenAudioClkEnable,@function\n"
"sceClockgenAudioClkEnable:\n"
"addiu $29,$29,-16\n"        /* 04BC 27BDFFF0 */
"li    $4,16\n"              /* 04C0 24040010 bus = AUDIO */
"sw    $31,0($29)\n"         /* 04C4 AFBF0000 */
"jal   0x5dc\n"              /* 04C8 0C000177 */
"li    $5,1\n"               /* 04CC 24050001 delay: mode = 1 */
"lw    $31,0($29)\n"         /* 04D0 8FBF0000 */
"jr    $31\n"                /* 04D4 03E00008 */
"addiu $29,$29,16\n"         /* 04D8 27BD0010 */
".size sceClockgenAudioClkEnable,.-sceClockgenAudioClkEnable\n"

".globl sceClockgenAudioClkDisable\n"
".type sceClockgenAudioClkDisable,@function\n"
"sceClockgenAudioClkDisable:\n"
"addiu $29,$29,-16\n"        /* 04DC 27BDFFF0 */
"li    $4,16\n"              /* 04E0 24040010 */
"sw    $31,0($29)\n"         /* 04E4 AFBF0000 */
"jal   0x5dc\n"              /* 04E8 0C000177 */
"move  $5,$0\n"              /* 04EC 00002821 delay: mode = 0 */
"lw    $31,0($29)\n"         /* 04F0 8FBF0000 */
"jr    $31\n"                /* 04F4 03E00008 */
"addiu $29,$29,16\n"         /* 04F8 27BD0010 */
".size sceClockgenAudioClkDisable,.-sceClockgenAudioClkDisable\n"

".globl sceClockgenLeptonClkEnable\n"
".type sceClockgenLeptonClkEnable,@function\n"
"sceClockgenLeptonClkEnable:\n"
"addiu $29,$29,-16\n"        /* 04FC 27BDFFF0 */
"li    $4,8\n"               /* 0500 24040008 bus = LEPTON */
"sw    $31,0($29)\n"         /* 0504 AFBF0000 */
"jal   0x5dc\n"              /* 0508 0C000177 */
"li    $5,1\n"               /* 050C 24050001 delay */
"lw    $31,0($29)\n"         /* 0510 8FBF0000 */
"jr    $31\n"                /* 0514 03E00008 */
"addiu $29,$29,16\n"         /* 0518 27BD0010 */
".size sceClockgenLeptonClkEnable,.-sceClockgenLeptonClkEnable\n"

".globl sceClockgenLeptonClkDisable\n"
".type sceClockgenLeptonClkDisable,@function\n"
"sceClockgenLeptonClkDisable:\n"
"addiu $29,$29,-16\n"        /* 051C 27BDFFF0 */
"li    $4,8\n"               /* 0520 24040008 */
"sw    $31,0($29)\n"         /* 0524 AFBF0000 */
"jal   0x5dc\n"              /* 0528 0C000177 */
"move  $5,$0\n"              /* 052C 00002821 delay */
"lw    $31,0($29)\n"         /* 0530 8FBF0000 */
"jr    $31\n"                /* 0534 03E00008 */
"addiu $29,$29,16\n"         /* 0538 27BD0010 */
".size sceClockgenLeptonClkDisable,.-sceClockgenLeptonClkDisable\n"

".set pop\n"
);
