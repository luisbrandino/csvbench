#include <QApplication>
#include <QFont>
#include <QIcon>
#include <cstdio>
#include <string>

#include "csvloader.h"
#include "mainwindow.h"
#include "proctime.h"

enum class BenchMode { None, Startup, Filter, Idle };

int main(int argc, char *argv[]) {
    double execEpochMs = getExecEpochMs();

    if (argc < 2) {
        std::fprintf(stderr, "usage: csvbench <path.csv> [--bench-startup|--bench-filter=STR|--bench-idle]\n");
        return 1;
    }

    std::string csvPath = argv[1];
    BenchMode mode = BenchMode::None;
    std::string filterTarget;

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--bench-startup") {
            mode = BenchMode::Startup;
        } else if (arg.rfind("--bench-filter=", 0) == 0) {
            mode = BenchMode::Filter;
            filterTarget = arg.substr(std::string("--bench-filter=").size());
        } else if (arg == "--bench-idle") {
            mode = BenchMode::Idle;
        }
    }

    QApplication app(argc, argv);
    app.setFont(QFont("DejaVu Sans Mono", 10));

    std::vector<Record> records = loadCsv(csvPath);

    MainWindow window(std::move(records));
    window.setWindowIcon(QIcon());
    window.setFixedSize(1280, 800);
    window.setWindowTitle("csvbench");

    bool firstFrameHandled = false;
    QObject::connect(&window, &MainWindow::firstFramePainted, [&]() {
        if (firstFrameHandled) {
            return;
        }
        firstFrameHandled = true;
        QApplication::sync();
        double paintEpochMs = nowEpochMs();

        if (mode == BenchMode::Startup) {
            std::printf("STARTUP_MS=%.3f\n", paintEpochMs - execEpochMs);
            std::fflush(stdout);
            QCoreApplication::quit();
        } else if (mode == BenchMode::Idle) {
            std::printf("READY\n");
            std::fflush(stdout);
        } else if (mode == BenchMode::Filter) {
            for (int i = 0; i < 20; i++) {
                window.setFilterText(QString());
                window.setFilterText(QString::fromStdString(filterTarget));
                std::printf("FILTER_MS=%.3f\n", window.lastFilterMs());
                std::fflush(stdout);
            }
            QCoreApplication::quit();
        }
    });

    window.show();

    return app.exec();
}
