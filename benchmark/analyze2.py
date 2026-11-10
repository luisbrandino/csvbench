#!/usr/bin/env python3
import json, os, random, statistics as st, sys

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw.json")
B = 10000
rng = random.Random(42)

def q(xs):
    xs = sorted(xs); n = len(xs)
    lo, hi = xs[: n // 2], xs[(n + 1) // 2:]
    return {"med": st.median(xs), "iqr": st.median(hi) - st.median(lo),
            "min": xs[0], "max": xs[-1], "n": n}

def boot(fn, *samples):
    vals = []
    for _ in range(B):
        vals.append(fn(*[[rng.choice(s) for _ in s] for s in samples]))
    vals.sort()
    return vals[int(0.025 * B)], vals[int(0.975 * B) - 1]

def ratio(w, n):
    r = st.median(w) / st.median(n)
    return {"ratio": r, "ci": boot(lambda a, b: st.median(a) / st.median(b), w, n)}

d = json.load(open(RAW))
out = {"env_start": d["env_start"], "env_end": d.get("env_end")}

s = d["startup"]
out["startup"] = {k: q([x for x in s[k] if x]) for k in s} | {"ratio": ratio(s["web"], s["native"])}

f = {k: [x for run in d["filter"][k] for x in run] for k in d["filter"]}
out["filter"] = {k: q(f[k]) for k in f} | {"ratio": ratio(f["web"], f["native"]),
                 "n_per_run": {k: [len(r) for r in d["filter"][k]] for k in f},
                 "run_medians": {k: [st.median(r) for r in d["filter"][k]] for k in f}}

idle = {}
for k, runs in d["idle"].items():
    at = lambda t, key: [next(p[key] for p in r["series"] if p["t"] == t) / 1024 for r in runs]
    idle[k] = {"pss_1_5": q(at(1.5, "pss_kb")), "rss_1_5": q(at(1.5, "rss_kb")),
               "pss_10": q(at(10.0, "pss_kb")),
               "pss_series_med": {t: st.median(at(t, "pss_kb")) for t in (0.5, 1.5, 3.0, 5.0, 10.0)},
               "settle_change_pct": q([100 * (b - a) / a for a, b in zip(at(1.5, "pss_kb"), at(10.0, "pss_kb"))]),
               "rss_pss": st.median([r / p for r, p in zip(at(1.5, "rss_kb"), at(1.5, "pss_kb"))]),
               "nproc": q([r["series"][1]["nproc"] for r in runs])}
    types = {}
    for r in runs:
        agg = {}
        for p in r["breakdown_1_5s"]:
            agg[p["type"]] = agg.get(p["type"], 0) + p["pss_kb"] / 1024
        for t, v in agg.items():
            types.setdefault(t, []).append(v)
    idle[k]["pss_by_type_med"] = {t: st.median(v) for t, v in types.items()}
pss = lambda k: [next(p["pss_kb"] for p in r["series"] if p["t"] == 1.5) for r in d["idle"][k]]
rss = lambda k: [next(p["rss_kb"] for p in r["series"] if p["t"] == 1.5) for r in d["idle"][k]]
idle["ratio_pss"] = ratio(pss("web"), pss("native"))
idle["ratio_rss"] = ratio(rss("web"), rss("native"))
out["idle"] = idle

EV = ["task-clock", "cycles", "instructions", "cache-references", "cache-misses",
      "branches", "branch-misses", "elapsed", "user", "sys"]
perf = {}
for side, modes in d["perf"].items():
    perf[side] = {}
    for mode, runs in modes.items():
        perf[side][mode] = {e: q([r[e] for r in runs]) for e in EV if all(e in r for r in runs)}
        perf[side][mode]["multiplexed_any"] = any(r.get("multiplexed") for r in runs)
    perf[side]["delta"] = {}
    for e in EV:
        a = [r[e] for r in modes["filter"]]; b = [r[e] for r in modes["startup"]]
        dm = st.median(a) - st.median(b)
        perf[side]["delta"][e] = {"med_diff": dm,
                                 "ci": boot(lambda x, y: st.median(x) - st.median(y), a, b)}
    dl = perf[side]["delta"]
    perf[side]["delta_derived"] = {
        "ipc": dl["instructions"]["med_diff"] / dl["cycles"]["med_diff"],
        "branch_miss_rate_pct": 100 * dl["branch-misses"]["med_diff"] / dl["branches"]["med_diff"],
        "cache_miss_rate_pct": 100 * dl["cache-misses"]["med_diff"] / dl["cache-references"]["med_diff"]}
    for mode in ("startup", "filter"):
        m = perf[side][mode]
        perf[side][mode]["ipc"] = m["instructions"]["med"] / m["cycles"]["med"]
        perf[side][mode]["branch_miss_rate_pct"] = 100 * m["branch-misses"]["med"] / m["branches"]["med"]
        perf[side][mode]["cache_miss_rate_pct"] = 100 * m["cache-misses"]["med"] / m["cache-references"]["med"]
        perf[side][mode]["eff_ghz"] = m["cycles"]["med"] / (m["task-clock"]["med"] * 1e6)
perf["ratios"] = {}
for scope in ("startup", "filter"):
    perf["ratios"][scope] = {}
    for e in EV:
        w = [r[e] for r in d["perf"]["web"][scope]]; n = [r[e] for r in d["perf"]["native"][scope]]
        perf["ratios"][scope][e] = ratio(w, n)
perf["ratios"]["delta"] = {}
for e in EV:
    wf = [r[e] for r in d["perf"]["web"]["filter"]]; ws = [r[e] for r in d["perf"]["web"]["startup"]]
    nf = [r[e] for r in d["perf"]["native"]["filter"]]; ns = [r[e] for r in d["perf"]["native"]["startup"]]
    fn = lambda a, b, c, e_: (st.median(a) - st.median(b)) / (st.median(c) - st.median(e_))
    perf["ratios"]["delta"][e] = {"ratio": fn(wf, ws, nf, ns), "ci": boot(fn, wf, ws, nf, ns)}
out["perf"] = perf

json.dump(out, open(RAW.replace("raw.json", "summary.json"), "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
