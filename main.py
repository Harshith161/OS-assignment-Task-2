"""OS Synchronization Lab: Readers-Writers and Dining Philosophers.

Run `python main.py` to execute all four demonstrations and create HTML traces.
Uses only Python's standard library.
"""
from __future__ import annotations

import argparse
import html
import json
import threading
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "generated_html"


class EventLog:
    """Thread-safe event recorder shared by the worker threads."""
    def __init__(self, problem: str, method: str):
        self.problem = problem
        self.method = method
        self.events = []
        self._lock = threading.Lock()
        self._sequence = 0

    def add(self, actor: str, state: str, detail: str = ""):
        with self._lock:
            self._sequence += 1
            self.events.append({
                "step": self._sequence,
                "time": round(time.monotonic(), 4),
                "actor": actor,
                "state": state,
                "detail": detail,
            })

    def snapshot(self):
        with self._lock:
            return list(self.events)


def write_trace(log: EventLog, filename: str):
    """Write a self-contained HTML page with a step-by-step event player."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = json.dumps(log.snapshot())
    page = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#172033;background:#f4f7fb}
body{max-width:1000px;margin:32px auto;padding:0 18px}
header,.panel{background:white;border:1px solid #dce3ef;border-radius:14px;padding:20px;margin-bottom:16px}
h1{margin:0 0 6px;font-size:1.6rem} .muted{color:#5b667a}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
button{border:0;border-radius:8px;padding:10px 14px;background:#234f9b;color:white;cursor:pointer}
button.secondary{background:#e5ebf5;color:#172033}
input{width:100%}
#current{font-size:1.15rem;padding:18px;background:#eef4ff;border-radius:10px;margin:12px 0}
table{width:100%;border-collapse:collapse;background:white}
th,td{text-align:left;padding:10px;border-bottom:1px solid #e6eaf1}
th{background:#f0f3f9} .pill{display:inline-block;padding:3px 8px;border-radius:20px;background:#e5ebf5}
</style></head>
<body>
<header><h1>__TITLE__</h1><div class="muted">Execution trace captured from the Python thread run.</div></header>
<section class="panel">
<div><b id="counter">Step 0 of 0</b></div>
<input id="seek" type="range" min="0" max="0" value="0">
<div id="current">Press Play to inspect the trace.</div>
<div class="controls">
<button id="play">Play</button><button class="secondary" id="pause">Pause</button>
<button class="secondary" id="back">Previous</button><button class="secondary" id="next">Next</button>
<button class="secondary" id="reset">Reset</button>
<label>Speed <select id="speed"><option value="1200">Slow</option><option value="650" selected>Normal</option><option value="250">Fast</option></select></label>
</div>
</section>
<section class="panel"><h2>All recorded events</h2>
<table><thead><tr><th>#</th><th>Actor</th><th>State</th><th>Details</th></tr></thead><tbody id="rows"></tbody></table>
</section>
<script>
const events = __EVENTS__;
let index = -1, timer = null;
const seek = document.getElementById('seek');
const current = document.getElementById('current');
const counter = document.getElementById('counter');
function show(i){
 if(!events.length){current.textContent='No events were recorded.';return;}
 index=Math.max(0,Math.min(i,events.length-1)); seek.value=index;
 const e=events[index]; counter.textContent=`Step ${index+1} of ${events.length}`;
 current.innerHTML=`<b>${escapeText(e.actor)}</b> — <span class="pill">${escapeText(e.state)}</span><p>${escapeText(e.detail||'No extra detail')}</p>`;
 document.querySelectorAll('#rows tr').forEach((r,j)=>r.style.background=j===index?'#eef4ff':'white');
}
function escapeText(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function stop(){if(timer!==null){clearInterval(timer);timer=null;}}
function play(){stop();timer=setInterval(()=>{if(index>=events.length-1){stop();return;}show(index+1);},Number(document.getElementById('speed').value));}
document.getElementById('play').onclick=play;
document.getElementById('pause').onclick=stop;
document.getElementById('next').onclick=()=>{stop();show(index+1)};
document.getElementById('back').onclick=()=>{stop();show(index-1)};
document.getElementById('reset').onclick=()=>{stop();show(0)};
seek.oninput=()=>{stop();show(Number(seek.value))};
document.getElementById('speed').onchange=()=>{if(timer!==null)play()};
seek.max=Math.max(0,events.length-1);
document.getElementById('rows').innerHTML=events.map((e,i)=>`<tr><td>${e.step}</td><td>${escapeText(e.actor)}</td><td>${escapeText(e.state)}</td><td>${escapeText(e.detail)}</td></tr>`).join('');
if(events.length)show(0);
</script></body></html>"""
    page = page.replace("__TITLE__", html.escape(f"{log.problem} — {log.method}"))
    page = page.replace("__EVENTS__", data)
    (OUTPUT_DIR / filename).write_text(page, encoding="utf-8")
    print(f"HTML trace: {OUTPUT_DIR / filename} ({len(log.snapshot())} events)")


def run_threads(workers):
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()


# 1. Readers-Writers with semaphores (reader-preference variant).
def readers_writers_semaphore(readers=3, writers=2):
    log = EventLog("Readers-Writers", "Semaphore")
    count_lock = threading.Semaphore(1)
    room_empty = threading.Semaphore(1)
    read_count = 0

    def reader(number):
        nonlocal read_count
        name = f"Reader {number}"
        log.add(name, "waiting", "Waiting to begin reading")
        with count_lock:
            read_count += 1
            if read_count == 1:
                room_empty.acquire()
        log.add(name, "reading", f"Active readers: {read_count}")
        time.sleep(0.08)
        with count_lock:
            read_count -= 1
            remaining = read_count
            if read_count == 0:
                room_empty.release()
        log.add(name, "finished", f"Readers still active: {remaining}")

    def writer(number):
        name = f"Writer {number}"
        log.add(name, "waiting", "Needs exclusive access")
        room_empty.acquire()
        log.add(name, "writing", "Exclusive access granted")
        time.sleep(0.10)
        log.add(name, "finished", "Released the shared resource")
        room_empty.release()

    workers = [threading.Thread(target=reader, args=(i,)) for i in range(1, readers + 1)]
    workers += [threading.Thread(target=writer, args=(i,)) for i in range(1, writers + 1)]
    run_threads(workers)
    assert read_count == 0
    write_trace(log, "readers_writers_semaphore.html")
    return log.snapshot()


# 2. Readers-Writers with a writer-priority monitor.
def readers_writers_monitor(readers=3, writers=2):
    log = EventLog("Readers-Writers", "Monitor")
    condition = threading.Condition()
    active_readers = 0
    waiting_writers = 0
    writer_active = False

    def reader(number):
        nonlocal active_readers
        name = f"Reader {number}"
        with condition:
            log.add(name, "waiting", "Waiting while a writer is active or queued")
            while writer_active or waiting_writers > 0:
                condition.wait()
            active_readers += 1
            log.add(name, "reading", f"Active readers: {active_readers}")
        time.sleep(0.07)
        with condition:
            active_readers -= 1
            log.add(name, "finished", f"Readers still active: {active_readers}")
            if active_readers == 0:
                condition.notify_all()

    def writer(number):
        nonlocal waiting_writers, writer_active
        name = f"Writer {number}"
        with condition:
            waiting_writers += 1
            log.add(name, "waiting", "Queued for exclusive access")
            while writer_active or active_readers > 0:
                condition.wait()
            waiting_writers -= 1
            writer_active = True
            log.add(name, "writing", "Exclusive access granted")
        time.sleep(0.09)
        with condition:
            writer_active = False
            log.add(name, "finished", "Released the shared resource")
            condition.notify_all()

    workers = [threading.Thread(target=reader, args=(i,)) for i in range(1, readers + 1)]
    workers += [threading.Thread(target=writer, args=(i,)) for i in range(1, writers + 1)]
    run_threads(workers)
    assert active_readers == 0 and not writer_active and waiting_writers == 0
    write_trace(log, "readers_writers_monitor.html")
    return log.snapshot()


# 3. Dining Philosophers with one semaphore per fork and a room semaphore.
def dining_philosophers_semaphore(count=4):
    log = EventLog("Dining Philosophers", "Semaphore")
    forks = [threading.Semaphore(1) for _ in range(count)]
    room = threading.Semaphore(count - 1)

    def philosopher(i):
        left, right = i, (i + 1) % count
        name = f"Philosopher {i}"
        log.add(name, "thinking", "Thinking before requesting forks")
        time.sleep(0.025 * (i % 3 + 1))
        log.add(name, "hungry", f"Requests forks {left} and {right}")
        room.acquire()
        try:
            forks[left].acquire()
            log.add(name, "fork acquired", f"Acquired fork {left}")
            forks[right].acquire()
            log.add(name, "eating", f"Using forks {left} and {right}")
            time.sleep(0.06)
            forks[right].release()
            forks[left].release()
            log.add(name, "finished eating", "Released both forks")
        finally:
            room.release()
        log.add(name, "done", "Returned to the thinking state")

    run_threads([threading.Thread(target=philosopher, args=(i,)) for i in range(count)])
    write_trace(log, "dining_philosophers_semaphore.html")
    return log.snapshot()


# 4. Dining Philosophers using a monitor: allocate both forks as one decision.
def dining_philosophers_monitor(count=4):
    log = EventLog("Dining Philosophers", "Monitor")
    condition = threading.Condition()
    states = ["thinking"] * count

    def left_of(i):
        return (i - 1) % count

    def right_of(i):
        return (i + 1) % count

    def can_eat(i):
        return states[left_of(i)] != "eating" and states[right_of(i)] != "eating"

    def philosopher(i):
        name = f"Philosopher {i}"
        log.add(name, "thinking", "Thinking before requesting both forks")
        time.sleep(0.025 * (i % 3 + 1))
        with condition:
            states[i] = "hungry"
            log.add(name, "hungry", "Waiting until both adjacent forks are available")
            while not can_eat(i):
                condition.wait()
            # The condition lock makes checking and claiming the pair atomic.
            states[i] = "eating"
            log.add(name, "eating", f"Allocated forks {i} and {(i + 1) % count}")
        time.sleep(0.06)
        with condition:
            states[i] = "thinking"
            log.add(name, "finished eating", "Released both forks")
            condition.notify_all()
        log.add(name, "done", "Returned to the thinking state")

    run_threads([threading.Thread(target=philosopher, args=(i,)) for i in range(count)])
    assert all(state == "thinking" for state in states)
    write_trace(log, "dining_philosophers_monitor.html")
    return log.snapshot()


def main():
    parser = argparse.ArgumentParser(description="Run OS synchronization demonstrations.")
    parser.add_argument("--problem", choices=["all", "rw-sem", "rw-monitor", "dp-sem", "dp-monitor"],
                        default="all", help="Choose one implementation or run all four.")
    args = parser.parse_args()
    runs = {
        "rw-sem": readers_writers_semaphore,
        "rw-monitor": readers_writers_monitor,
        "dp-sem": dining_philosophers_semaphore,
        "dp-monitor": dining_philosophers_monitor,
    }
    selected = runs.items() if args.problem == "all" else [(args.problem, runs[args.problem])]
    for key, function in selected:
        events = function()
        print(f"{key}: completed successfully; recorded {len(events)} events")
    print("\nOpen the generated HTML files in a browser to replay each event trace.")


if __name__ == "__main__":
    main()
