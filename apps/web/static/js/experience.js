// Shared interactions use native controls so data remains available without JS.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('label.form-label').forEach((label, index) => {
        if (label.htmlFor) return;
        const control = label.parentElement.querySelector('input,select');
        if (!control) return;
        control.id ||= 'filter-' + index;
        label.htmlFor = control.id;
    });
    document.querySelectorAll('.company-logo').forEach(logo => {
        if (logo.tagName !== 'IMG') return;
        const fallback = () => {
            const replacement = document.createElement('span');
            replacement.className = logo.className + ' company-monogram d-flex align-items-center justify-content-center';
            replacement.textContent = (logo.alt || '').slice(0, 2);
            replacement.setAttribute('aria-label', logo.alt || 'Company');
            logo.replaceWith(replacement);
        };
        logo.addEventListener('error', fallback, {once: true});
        if (logo.complete && !logo.naturalWidth) fallback();
    });
    document.querySelectorAll('a[target="_blank"]').forEach(link => link.rel = 'noopener noreferrer');
    document.querySelectorAll('.btn').forEach(button => {
        if (!button.textContent.trim() && !button.getAttribute('aria-label')) {
            const symbol = button.closest('tr')?.querySelector('td.fw-bold')?.textContent.trim();
            const name = symbol ? 'View ' + symbol : 'View company';
            button.setAttribute('aria-label', name);
            button.title = name;
        }
    });
    document.querySelectorAll('[data-sortable]').forEach(table => {
        table.querySelectorAll('thead th').forEach((heading, column) => {
            if (heading.dataset.noSort !== undefined) return;
            const button = document.createElement('button');
            button.className = 'table-sort';
            button.type = 'button';
            const label = heading.textContent.trim();
            button.textContent = label + ' \u2195';
            button.setAttribute('aria-label', 'Sort by ' + label);
            heading.replaceChildren(button);
            button.addEventListener('click', () => {
                const ascending = heading.getAttribute('aria-sort') !== 'ascending';
                table.querySelectorAll('th').forEach(th => th.removeAttribute('aria-sort'));
                heading.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
                const value = row => {
                    const cell = row.cells[column];
                    const text = cell.dataset.sortValue ?? cell.textContent.trim();
                    const number = Number(text.replace(/[\u20b9,%\s,]/g, ''));
                    return text && Number.isFinite(number) ? number : text.toLocaleLowerCase();
                };
                const rows = [...table.tBodies[0].rows];
                rows.sort((a, b) => {
                    const left = value(a), right = value(b);
                    const empty = item => item === '' || item === '\u2014' || item === 'none';
                    if (empty(left) || empty(right)) return Number(empty(left)) - Number(empty(right));
                    const result = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right));
                    return ascending ? result : -result;
                });
                table.tBodies[0].append(...rows);
            });
        });
    });
    document.querySelectorAll('[data-export]').forEach(button => button.addEventListener('click', () => {
        const table = document.getElementById(button.dataset.export);
        if (!table) return;
        const quote = value => {
            const text = String(value).trim();
            const safe = /^[=+@-]/.test(text) && !/^-?\d+(\.\d+)?$/.test(text) ? "'" + text : text;
            return '"' + safe.replaceAll('"', '""') + '"';
        };
        const csv = [...table.rows].map(row => [...row.cells].filter(cell => !cell.hasAttribute('data-no-export')).map(cell => quote(cell.textContent.replace(' \u2195', '').trim())).join(',')).join('\r\n');
        const url = URL.createObjectURL(new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8'}));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'scannifty100-results.csv';
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }));
});

if (window.Chart) {
    Chart.defaults.color = '#637179';
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.font.size = 11;
    Chart.defaults.borderColor = '#e5ebed';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
    Chart.defaults.plugins.tooltip.backgroundColor = '#202a30';
    Chart.defaults.animation = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : {duration: 350};
} else {
    document.querySelectorAll('.chart-container').forEach(container => {
        const note = document.createElement('p');
        note.className = 'chart-fallback';
        note.textContent = 'Chart unavailable. Financial values are available below.';
        container.replaceChildren(note);
    });
}
