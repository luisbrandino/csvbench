#include "tablemodel.h"

TableModel::TableModel(std::vector<Record> *records, QObject *parent)
    : QAbstractTableModel(parent), m_records(records) {}

int TableModel::rowCount(const QModelIndex &) const {
    return static_cast<int>(m_filteredIndices.size());
}

int TableModel::columnCount(const QModelIndex &) const {
    return 5;
}

QVariant TableModel::data(const QModelIndex &index, int role) const {
    if (role != Qt::DisplayRole) {
        return QVariant();
    }
    int row = index.row();
    if (row < 0 || row >= static_cast<int>(m_filteredIndices.size())) {
        return QVariant();
    }
    const Record &r = (*m_records)[m_filteredIndices[row]];
    switch (index.column()) {
        case 0: return QString::fromStdString(r.id);
        case 1: return QString::fromStdString(r.name);
        case 2: return QString::fromStdString(r.category);
        case 3: return QString::fromStdString(r.valueStr);
        case 4: return QString::fromStdString(r.date);
    }
    return QVariant();
}

QVariant TableModel::headerData(int section, Qt::Orientation orientation, int role) const {
    if (role != Qt::DisplayRole || orientation != Qt::Horizontal) {
        return QVariant();
    }
    switch (section) {
        case 0: return QStringLiteral("id");
        case 1: return QStringLiteral("name");
        case 2: return QStringLiteral("category");
        case 3: return QStringLiteral("value");
        case 4: return QStringLiteral("date");
    }
    return QVariant();
}

void TableModel::setFilteredIndices(std::vector<int> newIndices) {
    beginResetModel();
    m_filteredIndices = std::move(newIndices);
    endResetModel();
}
