function populateTable(tableId, items, columns) {
    let table = document.getElementById(tableId);
    let thead = document.createElement('thead');
    let tbody = document.createElement('tbody');

    // Headers
    let headerRow = document.createElement('tr');
    columns.forEach(col => {
        let th = document.createElement('th');
        th.textContent = col.replace('_', ' ').toUpperCase();
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    // Data Rows
    items.forEach(item => {
        let row = document.createElement('tr');
        if (tableId === 'services-table') {
            let serviceTd = document.createElement('td');
            serviceTd.textContent = item['role'];
            row.appendChild(serviceTd);

            let hoursTd = document.createElement('td');
            hoursTd.textContent = `${item['hours_booked']} Hours`;
            row.appendChild(hoursTd);

            let costTd = document.createElement('td');
            costTd.textContent = `$${item['cost']}`;
            row.appendChild(costTd);
        } else {
            columns.forEach(col => {
                let td = document.createElement('td');
                td.textContent = item[col];
                row.appendChild(td);
            });
        }
        tbody.appendChild(row);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
}
