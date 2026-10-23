# Owned active-process incident: console hosts and an additive resolution

The preserved actual attempt02 stopped at0.375 seconds with active-process accounting above2, total job processes3, a zero-byte worker log and no produced background files. The kernel memory/process settings were unchanged. This operational failure is not biological evidence.

We reproduced the launch chain using invented/source-only children: import the frozen worker module without invoking it, read one committed source file with explicit direct Git, then prepend the direct Git directory and run20 rapid original-style `git show HEAD:file` calls. No original worker admission, producer/replay function, cohort input, sequence table, feature matrix or outcome was invoked/read. Parent class3 job queries enumerate only owned PIDs; images are queried only after exact job-membership verification. Child NULL-handle job queries first verify the exact immediate-job caps.

| Launch configuration | Native observation |
|---|---|
| Original `CREATE_SUSPENDED|CREATE_NO_WINDOW` Python; default Git | Python plus a live `conhost.exe` already occupied2 before the first Git call. Git became a third live owned process. Stop at0.125s. |
| `CREATE_SUSPENDED|DETACHED_PROCESS` Python; default Git | Python alone initially; Git plus its new `conhost.exe` yielded3 live processes. Stop at0.140s. |
| Detached Python; `CREATE_NO_WINDOW` Git | Git still introduced `conhost.exe`;3 live processes. Stop at0.140s. |
| Detached Python; `DETACHED_PROCESS` Git |21 identical5344-byte source responses, exit0, max active2, no console host in454 observed snapshots; historical total22=Python+21 sequential Git helpers.0.781s. |
| Exact production-ready `headless.Job` + `GitFacade` |Same21 byte-identical source responses, exit0, max active2, no console host in508 snapshots; final active0, total22, peak job47,435,776 bytes.0.937s. |

The offending snapshots show actual live Python, direct Git and `C:/Windows/System32/conhost.exe`, all nonsignaled. This is stronger than an accounting-lag conjecture for this reproduced failure. It does not establish that all possible future accounting transitions are synchronous. No caps were raised and no observed excess was ignored.

## Additive helper API

`src/generalization_pum_process_probe_20261021/headless.py` exports `memory`, `process_memory`, `Job`, `GitFacade`, `scoped_git`, and `native_origins`. It preserves the old WinJob source SHA and inherits all memory limits, active2, suspended creation/assignment/membership checks, terminate/close behavior and global memory counters. Its own Job instance wraps only the native creation call: replace `CREATE_NO_WINDOW` by `DETACHED_PROCESS`, retain `CREATE_SUSPENDED`, and change no other arguments. It does not mutate the old module or global API bindings.

`GitFacade(module)` verifies the pinned direct Git executable. Its `check_output` accepts only three-argument `git show HEAD:file` calls, routes the executable to that same direct binary and supplies `creationflags=DETACHED_PROCESS`. Other kwargs and returned bytes remain unchanged. It rejects shell/text conversion and other creation flags. `scoped_git(target_module)` changes only that module's `subprocess` binding and restores its exact old object in `finally`; it never mutates the shared `subprocess` module. Install the facade **before every operational Git call**, including the worker's admission call and the original producer/replay module's manifest check. Root owns the new controller/worker fork and its separate freeze, and may not silently edit the old frozen modules.

Keep process768 MiB, job896 MiB, active2, kill-on-close,512 MiB startup physical,1.875 GiB startup system commit,1 GiB commit reserve,256 MiB physical stop and all other existing checks unchanged. Root must preserve startup/final/deadline checks and transparent resource-disclosure receipts. A detached console application has no console window; its existing explicit file logs and capture pipes are retained. This is resource routing, not a new numerical or data protocol.

Four invented tests verify flag-only changes, exact argument/kwarg/byte forwarding, module-local restoration after exception, and rejection of other commands/flags. The exact production helper was also exercised in the final native source-only case. The original code/math/IDs/modes/tolerances and every predecessor incident/result remain preserved. Full PUM cohort resource admission and independent numerical replay are still pending root execution; these checks are not a production-memory safety guarantee.

## Native provenance and primary API references

The final native case verified that the loaded `kernel32.dll` and `psapi.dll` module handles resolve under the actual `GetSystemDirectoryW` directory, with paths and SHA256 recorded in its receipt. This records current system module identity; it is not a reproducible-build or universal host certificate. The direct Git SHA is `51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7`. Original WinJob SHA is `3a2b470f116e87ff6233cdc8710b2703cf33b908dae68ece7fb4592227b5f741`.

[Microsoft process-creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags) distinguishes detached console processes, console-window suppression and suspended startup. [QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject) specifies immediate-job selection for a NULL handle in a nested job. The owned PID roster follows [JOBOBJECT_BASIC_PROCESS_ID_LIST](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list); image identification follows [QueryFullProcessImageNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew).
