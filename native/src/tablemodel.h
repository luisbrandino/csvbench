#pragma once

#include <QAbstractTableModel>
#include <vector>

#include "record.h"

class TableModel : public QAbstractTableModel {
    Q_OBJECT

public:
    explicit TableModel(std::vector<Record> *records, QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role) const override;

    void setFilteredIndices(std::vector<int> newIndices);

private:
    std::vector<Record> *m_records;
    std::vector<int> m_filteredIndices;
};
