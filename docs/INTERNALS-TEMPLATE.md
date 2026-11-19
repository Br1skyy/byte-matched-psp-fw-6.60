# INTERNALS.md template for reconstructed modules

Copy this skeleton to modules/<name>/INTERNALS.md and fill it in. Keep only
the sections that apply to the module; mark skipped sections as "not
applicable" rather than deleting the numbering. The finished file is the
single topic-organized reference for the module; the per-batch reports live
in results/ARCHIVE.md and are the primary evidence.

## style rules

- Plain short sentences. No first person. No process noise (no iteration
  counts, no agent names, no match/blocked status talk unless the behavior
  itself matters).
- NO em dashes. Run `grep` for them before finishing.
- Tables for every offset map: `| offset | field | evidence |`.
- Cite retail virtual addresses as evidence, e.g. `@0x16DAC`.
- Every fact must trace to a batch report or the retail disassembly. Do not
  invent. When batches disagreed, state the corrected value inline and name
  what was wrong (e.g. "batch X first read this as Y; the raw word at
  @0xNNNN says Z").
- Define notation once at the top (base pointers, struct names) and use it
  consistently. Beware base confusion: "ctx+X" and "module+X" are different
  things; convert everything to one base and say which.

## skeleton

```
# <module> internals

One-paragraph notation block: base pointers, struct names, abbreviations,
where the evidence lives.

## contents
(numbered list mirroring the sections kept)

## 1. Overview
Module role, file size, text/data segment layout, export count, entry
points, from-scratch SHA1. One table, one short paragraph.

## 2. Boot sequence
module_start step by step: init calls in order, static construction,
tables registered, threads or objects created, mode detection. Give the
retail address of each step.

## 3. Module data block map
Every documented data offset with meaning and evidence, in one table per
region. State the real size of the data block. List text/rodata constant
addresses separately at the end. Fold in corrections from earlier notes.

## 4. <primary object> control block
The module's central per-object struct: full field table with offsets and
evidence addresses. Include calling-convention notes (hardware registers,
k1-style tricks) here or in their own section.

## 5. Handle/UID system (if the module has one)
Class tables with offsets, allocator and resolver entry points, record
layout, view mechanisms, uid encoding tricks, sentinels.

## 6. Scheduler / main loop (if any)
States, queues, the dispatch or processing loop, preemption or priority
rules, locks and their state values.

## 7. Blocking / wait machinery (if any)
Queue invariants, wait types or request kinds, wake paths, teardown
invariants.

## 8. Object families (one subsection each)
Per family: object struct table, attr bit meanings, semantics, waiter
ordering rules, priority questions answered explicitly (ceiling vs
inheritance vs neither).

## 9. Callbacks / deferred execution (if any)
Pump, invoke ABI, reentry path, nesting and guards.

## 10. Timers / interrupts (if any)
Deadline channel, hardware registers, shadow/seed values, expiry dispatch.

## 11. Teardown / exit paths
Exit cores, retarget mechanisms, dead-object lists, synchronous
operations.

## 12. Memory / stacks (if any)
Allocation owners, extension or recycling mechanics, marker values.

## 13. Error code catalog
Table: code -> meaning -> function(s). Complete for the module.

## 14. Log msgno catalog (if the module logs)
Table: msgno -> event -> a1 convention -> extras. Document every a1
variant; this is where batches disagree most.

## 15. Quirks and shipped bugs
State corruption, stranded waiters, wrong return values, stale-register
sites, TOCTOU windows, dead code, marker constants. Say which are
reproduced verbatim.
```
