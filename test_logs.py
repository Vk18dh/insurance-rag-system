import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on('console', lambda msg: print(f'BROWSER LOG: {msg.text}'))
        
        await page.goto('http://localhost:3000/')
        await page.wait_for_timeout(2000)
        conv_links = await page.locator('a[href^="/c/"]').all()
        if conv_links:
            await conv_links[0].click()
            await page.wait_for_timeout(3000)
        
        print('SCROLLING UP NOW...')
        await page.mouse.wheel(0, -500)
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
