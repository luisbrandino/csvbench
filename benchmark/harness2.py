#!/usr/bin/env python3
import json, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = f"{ROOT}/bench.csv"
BINS = {"native": [f"{ROOT}/native/build/csvbench"],
        "web": [f"{ROOT}/web/dist/csvbench-1.0.0.AppImage"]}
FILTER = "--bench-filter=item_5"
OUT = os.path.join(HERE, "raw.json")
EVENTS = "task-clock,cycles,instructions,cache-references,cache-misses,branches,branch-misses"
IDLE_TIMES = [0.5, 1.5, 3.0, 5.0, 10.0]

def log(*a):
    print(time.strftime("%H:%M:%S"), *a, file=sys.stderr, flush=True)

def order(i):
    return ["native", "web"] if i % 2 == 0 else ["web", "native"]

def env_info():
    rd = lambda p: open(p).read().strip()
    govs = sorted({rd(f"/sys/devices/system/cpu/{c}/cpufreq/scaling_governor")
                   for c in os.listdir("/sys/devices/system/cpu") if re.fullmatch(r"cpu\d+", c)})
    cpu0 = "/sys/devices/system/cpu/cpu0/cpufreq/"
    return {"governors": govs, "driver": rd(cpu0 + "scaling_driver"),
            "epp": rd(cpu0 + "energy_performance_preference"),
            "perf_event_paranoid": rd("/proc/sys/kernel/perf_event_paranoid"),
            "nmi_watchdog": rd("/proc/sys/kernel/nmi_watchdog"),
            "compositor_running": subprocess.run(["pgrep", "-x", "picom|compton|xcompmgr"], capture_output=True).returncode == 0,
            "loadavg": rd("/proc/loadavg"), "kernel": os.uname().release}

def startup(side):
    p = subprocess.run(BINS[side] + [CSV, "--bench-startup"], capture_output=True, text=True, timeout=60)
    m = re.search(r"STARTUP_MS=([\d.]+)", p.stdout)
    return float(m.group(1)) if m else None

def filt(side):
    p = subprocess.run(BINS[side] + [CSV, FILTER], capture_output=True, text=True, timeout=60)
    return [float(x) for x in re.findall(r"FILTER_MS=([\d.]+)", p.stdout)]

def tree(root):
    pids, changed = {root}, True
    while changed:
        changed = False
        for p in os.listdir("/proc"):
            if not p.isdigit() or int(p) in pids:
                continue
            try:
                m = re.search(r"PPid:\s*(\d+)", open(f"/proc/{p}/status").read())
            except OSError:
                continue
            if m and int(m.group(1)) in pids:
                pids.add(int(p)); changed = True
    return pids

def proc_type(pid):
    try:
        cmd = open(f"/proc/{pid}/cmdline").read().split("\0")
    except OSError:
        return "?"
    for a in cmd:
        if a.startswith("--type="):
            t = a[7:]
            if t == "utility":
                for b in cmd:
                    if b.startswith("--utility-sub-type="):
                        return "utility:" + b.split("=")[1].split(".")[-1]
            return t
    return os.path.basename(cmd[0]) if cmd and cmd[0] else "?"

def smaps(pid):
    try:
        c = open(f"/proc/{pid}/smaps_rollup").read()
        return (int(re.search(r"^Rss:\s*(\d+)", c, re.M).group(1)),
                int(re.search(r"^Pss:\s*(\d+)", c, re.M).group(1)))
    except (OSError, AttributeError):
        return (0, 0)

def idle(side):
    p = subprocess.Popen(BINS[side] + [CSV, "--bench-idle"], stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True)
    t0 = time.time()
    while time.time() - t0 < 30:
        line = p.stdout.readline()
        if not line or line.strip() == "READY":
            break
    t_ready = time.time()
    series, breakdown = [], None
    for t in IDLE_TIMES:
        time.sleep(max(0, t_ready + t - time.time()))
        pids = tree(p.pid)
        rows = [(pid, proc_type(pid), *smaps(pid)) for pid in pids]
        series.append({"t": t, "nproc": len(pids),
                       "rss_kb": sum(r[2] for r in rows), "pss_kb": sum(r[3] for r in rows)})
        if t == 1.5:
            breakdown = [{"type": r[1], "rss_kb": r[2], "pss_kb": r[3]} for r in rows]
    p.send_signal(signal.SIGTERM)
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()
    time.sleep(0.5)
    return {"series": series, "breakdown_1_5s": breakdown}

def perf(side, mode):
    arg = "--bench-startup" if mode == "startup" else FILTER
    outf = os.path.join(HERE, ".perf.tmp")
    subprocess.run(["perf", "stat", "-e", EVENTS, "-o", outf, "--"] + BINS[side] + [CSV, arg],
                   capture_output=True, text=True, timeout=60)
    txt = open(outf).read()
    r = {}
    for line in txt.splitlines():
        m = re.match(r"^\s*([\d,.]+)\s+(?:msec\s+)?([a-z\-]+)", line)
        if m and m.group(2) in EVENTS.split(","):
            r[m.group(2)] = float(m.group(1).replace(",", ""))
        m = re.match(r"^\s*([\d.]+) seconds (time elapsed|user|sys)", line)
        if m:
            r[m.group(2).replace("time elapsed", "elapsed")] = float(m.group(1))
    r["multiplexed"] = "%" in "".join(l for l in txt.splitlines() if "cycles" in l or "branch" in l)
    return r

def main():
    data = {"env_start": env_info(), "startup": {"native": [], "web": []},
            "filter": {"native": [], "web": []}, "idle": {"native": [], "web": []},
            "perf": {s: {"startup": [], "filter": []} for s in BINS}}
    save = lambda: json.dump(data, open(OUT, "w"), indent=1)
    log("env", data["env_start"])

    for i in range(2):
        for s in order(i):
            startup(s)
    log("warm-up done")

    for i in range(15):
        for s in order(i):
            data["startup"][s].append(startup(s))
        log("startup", i, {s: data["startup"][s][-1] for s in BINS})
    save()

    for i in range(5):
        for s in order(i):
            data["filter"][s].append(filt(s))
        log("filter", i)
    save()

    for i in range(15):
        for s in order(i):
            data["idle"][s].append(idle(s))
        log("idle", i, {s: data["idle"][s][-1]["series"][1]["pss_kb"] for s in BINS})
        save()

    for i in range(10):
        for mode in (["startup", "filter"] if i % 2 == 0 else ["filter", "startup"]):
            for s in order(i):
                data["perf"][s][mode].append(perf(s, mode))
        log("perf", i)
        save()

    data["env_end"] = env_info()
    save()
    log("DONE")

if __name__ == "__main__":
    main()
