#include "proctime.h"

#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unistd.h>
#include <sys/time.h>

double nowEpochMs() {
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;
}

double getExecEpochMs() {
    std::ifstream statFile("/proc/self/stat");
    std::string content;
    std::getline(statFile, content);

    size_t lastParen = content.rfind(')');
    std::string rest = content.substr(lastParen + 2);

    std::istringstream iss(rest);
    std::vector<std::string> fields;
    std::string tok;
    while (iss >> tok) {
        fields.push_back(tok);
    }

    long long starttimeTicks = std::stoll(fields[19]);
    long clkTck = sysconf(_SC_CLK_TCK);

    std::ifstream uptimeFile("/proc/uptime");
    double uptimeSeconds = 0.0;
    uptimeFile >> uptimeSeconds;

    double nowEpochSeconds = nowEpochMs() / 1000.0;
    double bootEpochSeconds = nowEpochSeconds - uptimeSeconds;
    double execEpochSeconds = bootEpochSeconds + static_cast<double>(starttimeTicks) / clkTck;

    return execEpochSeconds * 1000.0;
}
