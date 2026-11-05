"""Run: python3 check_routes.py — uses installed Chrome and Playwright."""
import asyncio
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel='chrome')
        page = await browser.new_page(viewport={'width': 390, 'height': 844})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(Path(__file__).with_name('index.html').resolve().as_uri())
        assert await page.locator('.route-open').count() == 14
        for i in range(14):
            await page.evaluate('(i)=>document.querySelectorAll(".route-open")[i].click()', i)
            assert await page.locator('.route-page.open').count() == 1
            assert not await page.locator('.route-page').evaluate('(e)=>e.scrollWidth>e.clientWidth')
            assert await page.locator('.route-steps li').count() >= 2
            links = await page.locator('.route-page .route-actions a').evaluate_all('(xs)=>xs.map(x=>x.href)')
            for link in links:
                if 'maps.apple.com' in link:
                    assert parse_qs(urlparse(link).query).get('daddr')
                if 'google.com/maps' in link:
                    assert parse_qs(urlparse(link).query).get('destination')
            await page.locator('.route-back').click()
            assert await page.locator('.route-page.open').count() == 0
        for day in ['d6', 'd7', 'd8']:
            await page.locator('.tab[data-date="'+day+'"]').click()
            panel = page.locator('#'+day)
            sun_titles = await panel.locator('.stop h3').all_text_contents()
            await panel.locator('.mode[data-mode="rain"]').click()
            rain_titles = await panel.locator('.stop h3').all_text_contents()
            assert sun_titles != rain_titles, day
            assert all(a != b for a,b in zip(sun_titles,rain_titles)), day
            for button in await panel.locator('.route-open').all():
                await button.click()
                assert await page.locator('.route-page.open').count() == 1
                assert not await page.locator('.route-page').evaluate('(e)=>e.scrollWidth>e.clientWidth')
                if await page.locator('.fare').count():
                    assert '约人民币' in await page.locator('.fare-cny').inner_text()
                    assert '2026-11-04' in await page.locator('.route-page').inner_text()
                if day == 'd8':
                    links = await page.locator('.route-page .route-actions a').evaluate_all('(xs)=>xs.map(x=>x.href)')
                    assert not any('Repulse' in u or 'The+Pulse' in u for u in links), links
                await page.locator('.route-back').click()
                await page.wait_for_timeout(30)
            if day == 'd8':
                assert '时代广场' in ' '.join(rain_titles)
                await panel.locator('.route-open').last.click()
                assert await page.locator('.fare-cny').inner_text() == '约人民币 ¥43–77 + ¥298–425'
                await page.locator('.route-back').click()
                await page.wait_for_timeout(30)
            await panel.locator('.mode[data-mode="sun"]').click()
            assert await panel.locator('.stop h3').all_text_contents() == sun_titles
        await page.goto(Path(__file__).with_name('index.html').resolve().as_uri() + '#route-10-rain')
        assert '时代广场' in await page.locator('.route-page h2').inner_text()
        await page.locator('.route-back').click()
        assert await page.locator('.route-page.open').count() == 0
        await page.locator('.tab[data-date="d6"]').click()
        await page.locator('.route-open').first.click()
        await page.go_back()
        assert await page.locator('.route-page.open').count() == 0
        await page.goto(Path(__file__).with_name('index.html').resolve().as_uri() + '#route-13')
        assert await page.locator('.route-page.open').count() == 1
        assert '第二程' in await page.locator('.route-page').inner_text()
        assert not errors, errors
        assert not await page.locator('a[href*="amap.com"]').count()
        print('PASS: 14 sunny + 14 rainy detail pages; true weather switching; dual currencies; mobile fit; navigation; history; no JS errors.')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
