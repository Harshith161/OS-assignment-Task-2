# OS Synchronization Lab (Python)

A small Operating Systems project demonstrating two classic concurrency problems with two synchronization techniques each.

## Implementations

| Command | Problem | Technique |
|---|---|---|
| `rw-sem` | Readers–Writers | Semaphores; reader-preference |
| `rw-monitor` | Readers–Writers | `Condition` monitor; waiting writers block new readers |
| `dp-sem` | Dining Philosophers | One semaphore per fork plus a room semaphore |
| `dp-monitor` | Dining Philosophers | Monitor checks and claims both adjacent forks atomically |

Each run records thread events and writes a standalone HTML event player into `generated_html/`. The player has play, pause, previous/next, reset, speed, and seek controls.

## Requirements

- Python 3.10 or later recommended
- No third-party packages are required

## Run

```bash
python main.py
```

Run one demonstration only:

```bash
python main.py --problem rw-sem
python main.py --problem rw-monitor
python main.py --problem dp-sem
python main.py --problem dp-monitor
```

Then open the generated `.html` file in your browser.

## What to look for

- **Mutual exclusion:** a writer must be alone while writing; adjacent philosophers must not eat at the same time.
- **Concurrency:** several readers can read together.
- **Deadlock prevention:** the semaphore dining solution limits contenders to `N - 1`; the monitor solution claims a pair of forks in one protected decision.
- **Starvation:** the semaphore Readers–Writers solution is reader-preference and can starve writers under a continuous stream of readers. Writer priority reduces this risk in the monitor version, but does not provide a strict time-bound fairness guarantee.
- **Nondeterminism:** event order can change between runs because the OS schedules threads differently.

## Repository layout

```text
os-sync-lab/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
└── generated_html/
```

## Validation

Run the program several times and inspect all four HTML traces. Event ordering and event counts may differ from run to run; report the results you actually observe. The code includes end-state assertions for key shared-state invariants.

## Academic use

Use this as a learning scaffold: run it, inspect the synchronization logic, and be prepared to explain each lock/semaphore acquisition and release. Follow your course's rules for AI assistance and cite assistance where required. Do not report tests or results you have not personally run.
