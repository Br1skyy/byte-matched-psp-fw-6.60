# progress

clockgen is done. build_prx_cg.py --no-retail builds all 2836 bytes from
source derived material and the sha1 matches retail. details per function
below.

## functions (17/17, 437 words, 0 diffs)

| Addr | Size | Function | Status |
|---|---|---|---|
| 0x00000 | 62w | `sceClockgenSetup` | ✅ (transcribed; both I2C read paths) |
| 0x000F8 | 111w | `sceClockgenSetSpectrumSpreading` | ✅ (transcribed; ins word) |
| 0x002B4 | 27w | `module_start` | ✅ (pure C at link; 3 veneer jal + string lo16 are reloc words) |
| 0x00320 | 30w | `module_reboot_before` | ✅ (transcribed; ins word, inlines End) |
| 0x00398 | 21w | `sceClockgenInit` | ✅ (pure C at link; same reloc shape) |
| 0x003EC | 19w | `sceClockgenEnd` | ✅ (pure C at link; 2 veneer jal) |
| 0x00438 | 4w | `sceClockgenSetProtocol` | ✅ (pure C) |
| 0x00448 | 3w | `sceClockgenGetRevision` | ✅ (pure C) |
| 0x00454 | 10w | `sceClockgenGetRegValue` | ✅ (pure C) |
| 0x0047C | 16w | `sceClockgenAudioClkSetFreq` | ✅ (transcribed; branchy form) |
| 0x004BC | 8w | `sceClockgenAudioClkEnable` | ✅ (transcribed wrapper) |
| 0x004DC | 8w | `sceClockgenAudioClkDisable` | ✅ (transcribed wrapper) |
| 0x004FC | 8w | `sceClockgenLeptonClkEnable` | ✅ (transcribed wrapper) |
| 0x0051C | 8w | `sceClockgenLeptonClkDisable` | ✅ (transcribed wrapper) |
| 0x0053C | 40w | `_sceClockgenSysEventHandler` | ✅ (internal, transcribed; ins word) |
| 0x005DC | 41w | `_sceClockgenSetControl1` | ✅ (internal, transcribed) |
| 0x00680 | 21w | `_cy27040_write_register` | ✅ (internal, transcribed; daddu word) |

## link

```
56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199  clockgen-linked.prx (generated)
56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199  retail kd/clockgen.prx
```

every region generated and identical: text, 10 import veneers, export
entries and NID tables, import entries, strings, SceModuleInfo, sdk word,
the 80 byte RW image (from the C initializers) and the 308 byte load
relocation stream (re-encoded with a codec calibrated on the retail
stream, byte verified).
