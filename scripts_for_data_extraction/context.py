import asyncio
import json
import re
import subprocess
from typing import List
from playwright._impl._api_structures import Cookie
from playwright.async_api import async_playwright, Playwright, expect
from playwright.async_api._generated import Browser, BrowserContext, Locator, Page
from playwright_stealth import stealth_async

async def check_if_ready(page: Page, confirmation_url: str):
   while True:
      print("ch")
      await asyncio.sleep(4)
      if re.search(rf'{confirmation_url}', page.url):
         print("ech")
         break

async def start_debug_browser():
   command: List[str] = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--remote-debugging-port=9222"]
   subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

async def setup_browser(playwright: Playwright) -> Browser:
   curl_command: list[str] = [
                  "curl", "-f", "http://localhost:9222/json/version",
   ]
      # Run the curl command using subprocess
   result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
   result_text: str = result.stdout.strip()
   if "webSocketDebuggerUrl" not in result_text:
      await start_debug_browser()
   browser: Browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
   return browser
   
async def open_multiple_contexts():
   async with async_playwright() as p:
      # Launch the browser
      browser: Browser = await setup_browser(p)
      default_context: BrowserContext = browser.contexts[0]
      page: Page = default_context.pages[0]
      await stealth_async(page)
      # Create multiple contexts
      # context1 = await browser.new_context()
      # context2 = await browser.new_context()
      # context3 = await browser.new_context()
      # context4 = await browser.new_context()

      # # Open pages in the respective contexts
      # page1 = await context1.new_page()
      # await page1.goto('https://example.com')
      
      # page2 = await context2.new_page()
      # await page2.goto('https://example.com')
      
      # page3 = await context3.new_page()
      # await page3.goto('https://example.com')
      
      # page4 = await context4.new_page()
      # await page4.goto('https://example.com')

      # # Keep the script running indefinitely
      # print("Contexts have been opened. Press Ctrl+C to stop the script.")
      # await asyncio.Event().wait()  # Keeps the script running indefinitely

      async def save_cookies_to_file(context: BrowserContext, filename="cookies6.json"):
         # Collect the cookies from the context
         cookies: List[Cookie] = await context.cookies()
         
         # Save cookies to a file in JSON format
         with open(filename, "w") as file:
            json.dump(cookies, file)
         print(f"Cookies have been saved to {filename}")

      # print("Contexts are still open.")
      # for i in range(0, 4):
         # print("pre3")
         # await check_if_ready(page, "ready.com")
         # print("pre")
      await save_cookies_to_file(page.context, f"cookies4.json")
         # await page.wait_for_url("https://chatgpt.com/")
      # page.context.clear_cookies()

# Run the async function
asyncio.run(open_multiple_contexts())

async def load_cookies_from_file(context: BrowserContext, filename="cookies.json"):
   # Load cookies from a file
   with open(filename, "r") as file:
      cookies = json.load(file)
   
   # Add cookies to the context
   await context.add_cookies(cookies)
