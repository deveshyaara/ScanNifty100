const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
    const browser = await chromium.launch({channel: 'chrome', headless: true});
    const output = path.resolve('reports/ui');
    fs.mkdirSync(output, {recursive: true});
    const failures = [];
    const results = [];
    for (const viewport of [{width: 1440, height: 1000}, {width: 768, height: 1024}, {width: 390, height: 844}, {width: 320, height: 740}]) {
        const page = await browser.newPage({viewport});
        page.on('pageerror', error => failures.push(error.message));
        for (const route of ['/', '/companies/', '/screener/', '/sectors/', '/companies/RELIANCE/', '/sectors/IT/']) {
            const response = await page.goto('http://127.0.0.1:8000' + route, {waitUntil: 'networkidle'});
            if (response.status() !== 200) failures.push(route + ': HTTP ' + response.status());
            const state = await page.evaluate(() => ({
                overflow: document.documentElement.scrollWidth > innerWidth + 1,
                heading: document.querySelector('h1')?.textContent.trim(),
                charts: [...document.querySelectorAll('canvas')].map(canvas => {
                    const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
                    return {id: canvas.id, painted: pixels.some((value, index) => index % 4 === 3 && value > 0)};
                }),
                brokenImages: [...document.images].filter(img => !img.complete || !img.naturalWidth).length
            }));
            if (state.overflow) failures.push(route + ': overflow at ' + viewport.width);
            if (state.charts.some(chart => !chart.painted)) failures.push(route + ': blank chart');
            if (state.brokenImages) failures.push(route + ': broken images');
            results.push({route, width: viewport.width, ...state});
            const name = route === '/' ? 'overview' : route.replaceAll('/', '-').replace(/^-|-$/g, '');
            await page.screenshot({path: path.join(output, name + '-' + viewport.width + '.png'), fullPage: true});
        }
        if (viewport.width < 992) {
            await page.getByRole('button', {name: 'Toggle navigation'}).click();
            await page.getByRole('link', {name: 'Screener', exact: true}).click();
            if (!page.url().endsWith('/screener/')) failures.push('Mobile navigation did not open screener');
        }
        await page.goto('http://127.0.0.1:8000/companies/RELIANCE/');
        await page.getByRole('tab', {name: 'Balance sheet', exact: true}).click();
        await page.locator('#balance-sheet').waitFor({state: 'visible'});
        await page.getByRole('tab', {name: 'Cash flow', exact: true}).click();
        await page.locator('#cash-flow').waitFor({state: 'visible'});
        await page.goto('http://127.0.0.1:8000/screener/');
        await page.getByRole('button', {name: 'Sort by Revenue', exact: true}).click();
        if (await page.locator('th[aria-sort="ascending"]').count() !== 1) failures.push('Revenue sort state missing');
        const sortedRevenue = await page.evaluate(() => [...document.querySelectorAll('#screener-results tbody tr td:nth-child(5)')]
            .map(cell => Number(cell.textContent.replace(/[\u20b9,%\s,]/g, '')))
            .filter(Number.isFinite));
        if (sortedRevenue.some((value, index, list) => index && value < list[index - 1])) failures.push('Revenue ascending sort order failed');
        const danglingPercent = await page.locator('text=/[\u2014-]%/').count();
        if (danglingPercent) failures.push('Missing value rendered with trailing percent sign');
        const download = page.waitForEvent('download');
        await page.getByRole('button', {name: 'Export results'}).click();
        await (await download).saveAs(path.join(output, 'results-' + viewport.width + '.csv'));
        await page.getByLabel('Health Score').fill('90');
        await page.getByRole('button', {name: 'Apply Filters'}).click();
        if (!page.url().includes('min_score=90')) failures.push('Screener filter did not submit');
        await page.goto('http://127.0.0.1:8000/companies/?q=no-company-matches-this');
        if (!await page.getByText('No companies found matching your criteria.').isVisible()) failures.push('Company empty state missing');
        await page.close();
    }
    await browser.close();
    fs.writeFileSync(path.join(output, 'verification.json'), JSON.stringify({results, failures}, null, 2));
    console.log(JSON.stringify({pages: results.length, failures}, null, 2));
    if (failures.length) process.exitCode = 1;
}
main().catch(error => {console.error(error); process.exitCode = 1;});
