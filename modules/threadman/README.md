# threadman

the scheduler. 331 functions / 24982 words matched, from scratch build
equals retail sha1 32e4457c8018af2f168bb931c07ab01b88b836af.

match/ holds the source split by subsystem (sema.c evf.c mutex.c
thread.c dispatch.c timer.c etc, shared types in threadman.h).
PROGRESS.md is the scoreboard.

INTERNALS.md is the topic-organized reference: module data map, tcb
layout, k1 convention, uid classes, dispatcher, wait queues, ipc
families, callback reentry, boot sequence, timers, error and log
catalogs. results/ARCHIVE.md holds the unedited batch reports it
distills.
