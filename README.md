# csvbench — aplicações nativas vs. WebView

Material de replicação do artigo "Aplicações nativas vs. *WebView*: análise comparativa de desempenho em ambiente *desktop*" (Interface Tecnológica).

Uma mesma aplicação de exibição e filtragem de um CSV de 1.000.000 de linhas foi implementada em duas versões:

- `native/`: C++ com Qt 6 Widgets;
- `web/`: Electron, empacotada como AppImage.

As duas versões executam o mesmo algoritmo, na mesma ordem e em uma única linha de execução:

- leitura do arquivo inteiro na inicialização, sem leitura incremental;
- vetor de registros com cinco campos textuais e o valor numérico convertido na carga;
- busca linear a cada alteração do filtro, sem *debounce*, índice ou memorização de resultados;
- soma linear recalculada a cada filtro;
- tabela virtualizada, com o mesmo número de linhas visíveis.

Com o filtro `item_5`, as duas versões retornam as mesmas 111.092 linhas e a mesma soma (554.439.808,12).

## Conteúdo

| Caminho | Descrição |
|---|---|
| `gen_csv.py` | Gera `bench.csv` (semente fixa 42) |
| `native/` | Código-fonte da versão nativa e `build.sh` |
| `web/` | Código-fonte da versão Electron e `build.sh` |
| `benchmark/harness2.py` | Script de coleta (inicialização, filtro, memória ociosa e `perf stat`) |
| `benchmark/analyze2.py` | Estatística: mediana, IQR e IC 95% por *bootstrap* (gera `summary.json`) |
| `benchmark/raw.json` | Dados brutos da coleta usada no artigo, com a descrição do ambiente (`env_start`/`env_end`) |
| `benchmark/summary.json` | Estatísticas calculadas a partir de `raw.json` |
| `benchmark/harness2.log` | Registro da execução da coleta |
| `benchmark/RESULTS.md` | Resumo dos resultados |

## Ambiente da coleta

- AMD Ryzen 7 5800X (8 núcleos/16 *threads*), 62 GiB de RAM e NVMe.
- Devuan GNU/Linux 6, Linux 7.2.11, glibc 2.41 e X.Org 21.1.16 (X11), sem compositor gráfico.
- *Driver* amd-pstate-epp, com governador e EPP em `performance`.
- Qt 6.8.2, CMake 3.31.6 e GCC 14.2.0.
- Electron 43.4.0 (Node.js 24.18.1, Chromium 150.0.7871.224) e electron-builder 26.15.3.

## Como reproduzir

Os caminhos são relativos à raiz deste diretório.

```sh
# 1. Dados (SHA-256 esperado: 0441c414983e685ca7f640d4440401583d1ea435ba03ebdee63c74474414e327)
python3 gen_csv.py
sha256sum bench.csv

# 2. Compilação
native/build.sh          # gera native/build/csvbench (Release)
web/build.sh             # gera web/dist/csvbench-1.0.0.AppImage

# 3. Execução manual
native/build/csvbench bench.csv --bench-startup          # imprime STARTUP_MS
native/build/csvbench bench.csv --bench-filter=item_5    # imprime FILTER_MS (20 iterações)
native/build/csvbench bench.csv --bench-idle             # fica ocioso até SIGTERM
web/dist/csvbench-1.0.0.AppImage bench.csv --bench-startup
```

### Coleta completa

Requer `perf` e acesso aos contadores de *hardware*. As configurações usadas foram estas (exigem root):

```sh
sudo sysctl -w kernel.perf_event_paranoid=-1
sudo sysctl -w kernel.nmi_watchdog=0
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | sudo tee "$g"; done
```

Encerre o compositor gráfico, se houver, e execute:

```sh
python3 benchmark/harness2.py     # sobrescreve benchmark/raw.json (cerca de 10 min)
python3 benchmark/analyze2.py     # gera benchmark/summary.json
```

Ao terminar, restaure as configurações do sistema (por exemplo, `perf_event_paranoid=3`, `nmi_watchdog=1` e o governador original).

Para recalcular as estatísticas do artigo sem refazer a coleta, basta executar `python3 benchmark/analyze2.py` sobre o `raw.json` incluído.
