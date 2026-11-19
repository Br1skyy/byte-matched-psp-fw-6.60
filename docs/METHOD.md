# Method - how a function gets matched

1. **Locate**: `tools/prx.py` maps every export NID to a retail address
   (`orig/threadman-map.json`, 300 functions).
2. **Read**: `grep -A<n> ' addr:' orig/threadman.dis` - the full retail
   disassembly, vaddr-aligned with the map.
3. **Reverse**: write the C that *produces* that codegen. Known shapes:
   - tail-returns (`return f(...)`) leave v0 alone across the call
   - 8-byte struct / u64 returns land in v0/v1 with no frame
   - branch-likely delay slots hold the "taken" side effects
   - `lui aX,0 / lw aX,off(aX)` = module-relative global; the LO16 offset
     is the retail data-block offset
4. **Compare**: `tools/match.py match/threadman/tm.c`
   - `*** MATCH ***` - done
   - `match (reloc)` - only relocation-covered fields differ; goes exact
     at module link when the data layout is reproduced
   - `DIFF n` - word-level dump; fix source shape and repeat
5. **Record**: globals discovered -> pad the statics block at the right
   offsets; function -> PROGRESS.md.

## Kernel-PRX export table layout (empirically decoded)

- `SceModuleInfo`: `attr(2) ver(2) name[28] gp(4) ent_top/ent_end/
  stub_top/stub_end` as **u32 absolute module vaddrs**; `p_paddr` in the
  program header is a packer constant (0x800189DC everywhere), NOT the
  modinfo address - locate the struct by scanning for the name string.
- Export entry (16 bytes): `name u32, flags u32, ver u16, fcount u8, x u8,
  table u32`. Table = `[NID ...][ADDR ...]`; the NID block can run one
  longer than fcount, so scan for the boundary (first word < 0x10000).
- Observed: syslib fcount covers 4 NIDs / 2 addrs; ThreadManForUser
  151 NIDs/151 addrs; ThreadManForKernel 150 NIDs/149 addrs.
