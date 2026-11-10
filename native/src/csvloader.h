#pragma once

#include <string>
#include <vector>

#include "record.h"

std::vector<Record> loadCsv(const std::string &path);
