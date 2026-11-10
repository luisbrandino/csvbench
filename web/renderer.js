const fs = require('fs');
const { ipcRenderer } = require('electron');

const ROW_HEIGHT = 24;
const POOL_SIZE = 60;
const VISIBLE_OVERSCAN = 15;

function parseArgs() {
    const args = process.argv;
    let csvPath = null;
    let benchMode = null;
    let filterTarget = '';

    for (const arg of args) {
        if (arg.startsWith('--csv-path=')) {
            csvPath = arg.slice('--csv-path='.length);
        } else if (arg === '--bench-startup') {
            benchMode = 'startup';
        } else if (arg.startsWith('--bench-filter=')) {
            benchMode = 'filter';
            filterTarget = arg.slice('--bench-filter='.length);
        } else if (arg === '--bench-idle') {
            benchMode = 'idle';
        }
    }

    return { csvPath, benchMode, filterTarget };
}

function loadCsv(csvPath) {
    const content = fs.readFileSync(csvPath, 'utf8');
    const lines = content.split('\n');

    const records = [];
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (line.length === 0) {
            continue;
        }
        const fields = line.split(',');
        if (fields.length < 5) {
            continue;
        }
        records.push({
            id: fields[0],
            name: fields[1],
            category: fields[2],
            valueStr: fields[3],
            date: fields[4],
            value: parseFloat(fields[3]),
        });
    }

    return records;
}

const { csvPath, benchMode, filterTarget } = parseArgs();

let records = loadCsv(csvPath);
let filteredIndices = [];

const scrollEl = document.getElementById('table-scroll');
const spacerEl = document.getElementById('table-spacer');
const footerEl = document.getElementById('footer');
const filterInput = document.getElementById('filter-input');

const rowPool = [];
for (let i = 0; i < POOL_SIZE; i++) {
    const row = document.createElement('div');
    row.className = 'row';

    const cId = document.createElement('div');
    cId.className = 'cell col-id';
    const cName = document.createElement('div');
    cName.className = 'cell col-name';
    const cCategory = document.createElement('div');
    cCategory.className = 'cell col-category';
    const cValue = document.createElement('div');
    cValue.className = 'cell col-value';
    const cDate = document.createElement('div');
    cDate.className = 'cell col-date';

    row.appendChild(cId);
    row.appendChild(cName);
    row.appendChild(cCategory);
    row.appendChild(cValue);
    row.appendChild(cDate);
    spacerEl.appendChild(row);

    rowPool.push({ el: row, cId, cName, cCategory, cValue, cDate });
}

function renderRows() {
    const scrollTop = scrollEl.scrollTop;
    const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - VISIBLE_OVERSCAN);

    for (let i = 0; i < POOL_SIZE; i++) {
        const dataIndex = startIndex + i;
        const pool = rowPool[i];

        if (dataIndex >= filteredIndices.length) {
            pool.el.style.display = 'none';
            continue;
        }

        pool.el.style.display = 'flex';
        pool.el.style.top = (dataIndex * ROW_HEIGHT) + 'px';

        const record = records[filteredIndices[dataIndex]];
        pool.cId.textContent = record.id;
        pool.cName.textContent = record.name;
        pool.cCategory.textContent = record.category;
        pool.cValue.textContent = record.valueStr;
        pool.cDate.textContent = record.date;
    }
}

scrollEl.addEventListener('scroll', renderRows);

function applyFilter(text) {
    const t0 = process.hrtime.bigint();

    const needle = text;
    const indices = [];
    for (let i = 0; i < records.length; i++) {
        if (records[i].name.indexOf(needle) !== -1) {
            indices.push(i);
        }
    }

    let sum = 0;
    for (let i = 0; i < indices.length; i++) {
        sum += records[indices[i]].value;
    }

    filteredIndices = indices;
    spacerEl.style.height = (filteredIndices.length * ROW_HEIGHT) + 'px';
    scrollEl.scrollTop = 0;
    renderRows();
    footerEl.textContent = filteredIndices.length + ' rows | sum: ' + sum.toFixed(2);

    const t1 = process.hrtime.bigint();
    return Number(t1 - t0) / 1e6;
}

filterInput.addEventListener('input', () => {
    applyFilter(filterInput.value);
});

applyFilter('');

requestAnimationFrame(() => {
    requestAnimationFrame(() => {
        const paintEpochMs = Date.now();
        ipcRenderer.send('first-frame', { paintEpochMs: paintEpochMs });

        if (benchMode === 'filter') {
            for (let i = 0; i < 20; i++) {
                applyFilter('');
                const ms = applyFilter(filterTarget);
                ipcRenderer.send('filter-ms', ms);
            }
        }
    });
});
