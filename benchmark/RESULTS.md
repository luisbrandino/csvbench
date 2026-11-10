# Coleta v2 — revisão pós-pareceristas

Dados brutos: `raw.json` · estatística: `summary.json` (gerado por `analyze2.py`) · coleta: `harness2.py`, log em `harness2.log`.

Ambiente: mesma máquina da coleta anterior; governor `performance` (amd-pstate-epp, EPP performance),
perf_event_paranoid=-1, nmi_watchdog=0, **sem compositor** (picom encerrado durante a coleta), kernel 7.2.11.
Execuções intercaladas nativa/web com ordem alternada; 2 aquecimentos descartados.

| Métrica | Nativa | Web | Razão (IC 95% bootstrap) |
|---|---|---|---|
| STARTUP_MS mediana (IQR), n=15 | 401,38 (13,38) | 1.733,00 (12,00) | 4,32× (4,26–4,38) |
| FILTER_MS mediana (IQR), n=100 | 11,55 (0,47) | 20,38 (0,25) | 1,76× (1,75–1,78) |
| PSS ocioso MiB, n=15 | 287,7 (0,06) | 580,8 (2,10) | 2,02× (2,01–2,02) |
| RSS ocioso MiB, n=15 | 302,7 (0,23) | 969,7 (3,00) | 3,20× (3,20–3,21) |
| CPU (task-clock), modo inicialização | 0,41 s | 2,46 s | 6,04× |
| CPU, fase de filtro (filtro − inicialização) | 0,41 s | 0,72 s | 1,78× (1,72–1,84) |
| Ciclos, fase de filtro | 1.847 M | 3.140 M | 1,70× (1,67–1,78) |
| Taxa branch-miss: inicialização / filtro | 0,52% / 0,47% | 4,85% / 0,22% | — |

Achado que corrige a coleta anterior: a taxa de branch-misses ~5× maior no web
vem da **inicialização**, não do algoritmo de filtro. Os CPU-segundos da coleta anterior foram
subestimados: o polling de /proc a 5 ms não conta processos encerrados entre amostras.
O task-clock do perf (com herança de contadores) os inclui.

Dependências (ldd): nativa = 40 bibliotecas (74,6 MiB; Qt6 22,5 MiB). Electron = 91 bibliotecas
do sistema (41,8 MiB), além da libffmpeg embarcada. A afirmação "0 dependências" da coleta anterior estava errada.
