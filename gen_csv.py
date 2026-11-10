#!/usr/bin/env python3
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench.csv")

random.seed(42)
with open(OUT, "w") as f:
    f.write("id,nome,categoria,valor,data\n")
    cats = ["alpha", "beta", "gamma", "delta", "epsilon"]
    for i in range(1_000_000):
        f.write(f"{i},item_{random.randint(0,99999)},{random.choice(cats)},"
                f"{random.uniform(0,10000):.2f},2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}\n")
print(OUT)
