#pragma once

#include <QWidget>
#include <QLineEdit>
#include <QTableView>
#include <QLabel>
#include <vector>

#include "record.h"
#include "tablemodel.h"

class MainWindow : public QWidget {
    Q_OBJECT

public:
    explicit MainWindow(std::vector<Record> records, QWidget *parent = nullptr);

    void setFilterText(const QString &text);
    double lastFilterMs() const;

signals:
    void firstFramePainted();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private slots:
    void onFilterTextChanged(const QString &text);

private:
    double applyFilter(const QString &text);

    std::vector<Record> m_records;
    TableModel *m_model;
    QLineEdit *m_filterEdit;
    QTableView *m_tableView;
    QLabel *m_footer;
    double m_lastFilterMs;
    bool m_firstPaintEmitted;
};
