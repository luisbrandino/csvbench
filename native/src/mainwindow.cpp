#include "mainwindow.h"

#include <QVBoxLayout>
#include <QHeaderView>
#include <QEvent>
#include <ctime>

MainWindow::MainWindow(std::vector<Record> records, QWidget *parent)
    : QWidget(parent), m_records(std::move(records)), m_lastFilterMs(0.0), m_firstPaintEmitted(false) {
    m_model = new TableModel(&m_records, this);

    m_filterEdit = new QLineEdit(this);
    m_filterEdit->setFixedHeight(32);

    m_tableView = new QTableView(this);
    m_tableView->setModel(m_model);
    m_tableView->verticalHeader()->setVisible(false);
    m_tableView->verticalHeader()->setDefaultSectionSize(24);
    m_tableView->horizontalHeader()->setFixedHeight(24);
    m_tableView->horizontalHeader()->setSectionResizeMode(QHeaderView::Fixed);
    m_tableView->horizontalHeader()->setStretchLastSection(false);
    m_tableView->setColumnWidth(0, 80);
    m_tableView->setColumnWidth(1, 200);
    m_tableView->setColumnWidth(2, 140);
    m_tableView->setColumnWidth(3, 120);
    m_tableView->setColumnWidth(4, 120);
    m_tableView->setSelectionMode(QAbstractItemView::NoSelection);
    m_tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_tableView->setShowGrid(true);
    m_tableView->setSortingEnabled(false);
    m_tableView->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);

    m_footer = new QLabel(this);
    m_footer->setFixedHeight(24);

    QVBoxLayout *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(0);
    layout->addWidget(m_filterEdit);
    layout->addWidget(m_tableView);
    layout->addWidget(m_footer);
    setLayout(layout);

    connect(m_filterEdit, &QLineEdit::textChanged, this, &MainWindow::onFilterTextChanged);

    applyFilter(QString());

    m_tableView->viewport()->installEventFilter(this);
}

bool MainWindow::eventFilter(QObject *watched, QEvent *event) {
    if (watched == m_tableView->viewport() && event->type() == QEvent::Paint && !m_firstPaintEmitted) {
        m_firstPaintEmitted = true;
        emit firstFramePainted();
    }
    return QWidget::eventFilter(watched, event);
}

void MainWindow::setFilterText(const QString &text) {
    m_filterEdit->setText(text);
}

double MainWindow::lastFilterMs() const {
    return m_lastFilterMs;
}

void MainWindow::onFilterTextChanged(const QString &text) {
    m_lastFilterMs = applyFilter(text);
}

double MainWindow::applyFilter(const QString &text) {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    std::string needle = text.toStdString();
    std::vector<int> indices;
    for (int i = 0; i < static_cast<int>(m_records.size()); i++) {
        if (m_records[i].name.find(needle) != std::string::npos) {
            indices.push_back(i);
        }
    }

    double sum = 0.0;
    for (int idx : indices) {
        sum += m_records[idx].value;
    }

    m_model->setFilteredIndices(std::move(indices));
    m_tableView->scrollToTop();

    QString footerText = QString("%1 rows | sum: %2")
                              .arg(m_model->rowCount())
                              .arg(QString::number(sum, 'f', 2));
    m_footer->setText(footerText);

    clock_gettime(CLOCK_MONOTONIC, &t1);
    return (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
}
