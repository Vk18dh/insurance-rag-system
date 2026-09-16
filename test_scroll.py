import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://localhost:3000/')
        await page.wait_for_timeout(2000)
        conv_links = await page.locator('a[href^="/c/"]').all()
        if conv_links:
            await conv_links[0].click()
            await page.wait_for_timeout(3000)
        await page.mouse.wheel(0, -500)
        await page.wait_for_timeout(4000)
        await page.screenshot(path='screenshot.png', full_page=True)
        await browser.close()
        print('Success')

if __name__ == '__main__':
    asyncio.run(main())
