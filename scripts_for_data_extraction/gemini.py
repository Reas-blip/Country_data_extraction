
r"""this script connects to a already open gemini ai open tab in chrome to set this up run 
   this command `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
   and go to the tab you want in this case gemini ai to test if it worked then go to 
   `http://localhost:9222/json/version`
   you should see something like
   ```{
   "Browser": "Chrome/130.0.6723.92",
   "Protocol-Version": "1.3",
   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
   "V8-Version": "13.0.245.18",
   "WebKit-Version": "537.36 (@ef4f16c57010eb3e047ef101019b869296173bd9)",
   "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/2d4e860b-d15a-4338-9323-1b851f4002cf"
}```
   then use ```browser: Browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
   default_context: BrowserContext = browser.contexts[0]
   page: Page = default_context.pages[0]``` 
   to connect to the browser
   """

import asyncio
from playwright.async_api import async_playwright, Playwright, expect
from playwright.async_api._generated import Browser, BrowserContext, Locator, Page

# Start a new session with Playwright using the sync_playwright function.
async def ask_gemini(playwright: Playwright, prompts) -> str | None:
   # Connect to an existing instance of Chrome using the connect_over_cdp method.
   page: Page = await init_playwright(playwright)
   for prompt in prompts:
      await send_prompt_to_gemini_page(page, prompt)
   return await page.content()
   
async def send_prompt_to_gemini_page(page: Page, prompt: str) -> str | None:
   await page.goto("https://gemini.google.com/app")
   chat_box: Locator = page.get_by_label("Enter a prompt here")
   await chat_box.fill(prompt)
   await page.get_by_label("Send message").click()
   
   await page.wait_for_selector("img.ng-star-inserted")
   await page.wait_for_load_state("load")
   response: Locator = page.locator("div.markdown.markdown-main-panel.response-optimization.stronger").last
   response_text: str | None = await response.text_content()
   return response_text

async def init_playwright(playwright: Playwright) -> Page:
   browser: Browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
   default_context: BrowserContext = browser.contexts[0]
   page: Page = default_context.pages[0]
   return page
   
async def run(prompt)  -> str | None:
   async with async_playwright() as playwright:
      return await ask_gemini(playwright, prompt)

if "__main__" == __name__ :
   asyncio.run(run("whats up"))
   