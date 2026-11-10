const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');

function nowEpochMs() {
    return Date.now();
}

function getExecEpochMs() {
    const statContent = fs.readFileSync('/proc/self/stat', 'utf8');
    const lastParen = statContent.lastIndexOf(')');
    const rest = statContent.slice(lastParen + 2);
    const fields = rest.trim().split(/\s+/);
    const starttimeTicks = parseInt(fields[19], 10);
    const clkTck = 100;

    const uptimeContent = fs.readFileSync('/proc/uptime', 'utf8');
    const uptimeSeconds = parseFloat(uptimeContent.trim().split(/\s+/)[0]);

    const nowEpochSeconds = nowEpochMs() / 1000;
    const bootEpochSeconds = nowEpochSeconds - uptimeSeconds;
    const execEpochSeconds = bootEpochSeconds + starttimeTicks / clkTck;

    return execEpochSeconds * 1000;
}

const execEpochMs = getExecEpochMs();

const isPackaged = app.isPackaged;
const userArgs = isPackaged ? process.argv.slice(1) : process.argv.slice(2);

const csvPath = userArgs[0];
let benchMode = null;
let filterTarget = '';

for (const arg of userArgs.slice(1)) {
    if (arg === '--bench-startup') {
        benchMode = 'startup';
    } else if (arg.startsWith('--bench-filter=')) {
        benchMode = 'filter';
        filterTarget = arg.slice('--bench-filter='.length);
    } else if (arg === '--bench-idle') {
        benchMode = 'idle';
    }
}

if (!csvPath) {
    process.stderr.write('usage: csvbench <path.csv> [--bench-startup|--bench-filter=STR|--bench-idle]\n');
    app.exit(1);
}

function printLine(line, cb) {
    process.stdout.write(line + '\n', cb);
}

Menu.setApplicationMenu(null);

app.whenReady().then(() => {
    const additionalArguments = ['--csv-path=' + csvPath];
    if (benchMode === 'startup') {
        additionalArguments.push('--bench-startup');
    } else if (benchMode === 'filter') {
        additionalArguments.push('--bench-filter=' + filterTarget);
    } else if (benchMode === 'idle') {
        additionalArguments.push('--bench-idle');
    }

    const win = new BrowserWindow({
        width: 1280,
        height: 800,
        useContentSize: true,
        resizable: false,
        title: 'csvbench',
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            additionalArguments: additionalArguments,
        },
    });

    win.loadFile(path.join(__dirname, 'index.html'));

    let filterCount = 0;

    ipcMain.on('first-frame', (event, data) => {
        const paintEpochMs = data.paintEpochMs;
        if (benchMode === 'startup') {
            printLine('STARTUP_MS=' + (paintEpochMs - execEpochMs).toFixed(3), () => app.exit(0));
        } else if (benchMode === 'idle') {
            printLine('READY');
        }
    });

    ipcMain.on('filter-ms', (event, ms) => {
        filterCount++;
        const line = 'FILTER_MS=' + ms.toFixed(3);
        if (filterCount >= 20) {
            printLine(line, () => app.exit(0));
        } else {
            printLine(line);
        }
    });
});
