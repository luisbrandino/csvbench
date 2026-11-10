#include "csvloader.h"

#include <fstream>
#include <iterator>

namespace {

std::vector<std::string> splitByChar(const std::string &s, char sep) {
    std::vector<std::string> parts;
    size_t start = 0;
    while (true) {
        size_t pos = s.find(sep, start);
        if (pos == std::string::npos) {
            parts.push_back(s.substr(start));
            break;
        }
        parts.push_back(s.substr(start, pos - start));
        start = pos + 1;
    }
    return parts;
}

}

std::vector<Record> loadCsv(const std::string &path) {
    std::ifstream file(path, std::ios::binary);
    std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    std::vector<std::string> lines = splitByChar(content, '\n');

    std::vector<Record> records;
    for (size_t i = 1; i < lines.size(); i++) {
        const std::string &line = lines[i];
        if (line.empty()) {
            continue;
        }
        std::vector<std::string> fields = splitByChar(line, ',');
        if (fields.size() < 5) {
            continue;
        }
        Record r;
        r.id = fields[0];
        r.name = fields[1];
        r.category = fields[2];
        r.valueStr = fields[3];
        r.date = fields[4];
        r.value = std::stod(r.valueStr);
        records.push_back(std::move(r));
    }

    return records;
}
