
r"""this script connects to a already open chatgbt ai open tab in chrome to set this up run 
   this command `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
   and go to the tab you want in this case chatgbt ai to test if it worked then go to 
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
import re
from typing import Any, List
from playwright.async_api import async_playwright, Playwright, expect
from playwright.async_api._generated import Browser, BrowserContext, Locator, Page
import table

async def ask_chatgbt_async(playwright: Playwright,
                            dict_of_industries_to_sectors_prompt_list: dict[str, list[str]]):
   pages: list[Page] = await init_playwright(playwright)
   batch_size: int = len(pages)
   industry_dict: dict[str, list[str]] = dict_of_industries_to_sectors_prompt_list
   for industry, sectors_prompt_list in industry_dict.items():
      tasks = []
      for i in range(0, len(industry_dict), batch_size):
         task = ask_chatgbt(page, sectors_prompt_list)
      await asyncio.gather(*tasks)

async def write_page_content(file_dir, page_html_content):
   with open(file_dir, "w") as file:
      file.write(page_html_content)

async def save_response(page: Page, prompts: list[Any], ):
   html = await ask_chatgbt(page, prompts)
   
   
   await table.extract_prompt_data()
   
# Start a new session with Playwright using the sync_playwright function.
async def ask_chatgbt(page: Page, prompts: list[Any], reload_chatgbt: bool=False) -> str | None:
   # Connect to an existing instance of Chrome using the connect_over_cdp method.
   for prompt in prompts:
      await send_prompt_to_chatgbt_page(page, prompt)
   page_content: str = await page.content()
   await reload_chatgbt_page(page)
   return page_content
   
async def send_prompt_to_chatgbt_page(page: Page, prompt: str) -> str | None:
   chat_box: Locator = page.locator("div.ProseMirror")
   await chat_box.fill(prompt)
   send: Locator = page.get_by_label("Send prompt")
   await send.click()
   await page.wait_for_selector('div.result-streaming.markdown.prose', state='detached')
   await expect(page.get_by_label("Stop streaming")).to_be_hidden(timeout=100000)
   # await expect(send).to_be_disabled(timeout=100000)
   # response: Locator = page.locator("code[class]").last
   
   # response_text: str | None = await response.text_content()
   # return response_text

async def init_playwright(playwright: Playwright, reload_chatgbt: bool=False) -> List[Page]:
   browser: Browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
   default_context: BrowserContext = browser.contexts[0]
   page_list: list[Page] = default_context.pages
   await asyncio.gather(*(reload_chatgbt_page(page) for page in page_list))
   return page_list

async def reload_chatgbt_page(page):
    await page.goto("https://chat.openai.com/")
   
async def run(prompts, reload_chatgbt: bool=False) -> str | None:
   async with async_playwright() as playwright:
      return await ask_chatgbt_async(playwright, prompts, reload_chatgbt)
   
async def remove_amp_string(html_text) -> str:
    return re.sub("amp;", "", html_text)
 
async def extract_table_data(html_text: str):
   table_str: str = ""
   html_text_amp_removed: str = await remove_amp_string(html_text)
   
   column_list: list[str] = re.findall(r'<th>\s*<strong>\s*([\w\s]+)\s*</strong>', html_text_amp_removed)
   table_str += "| ".join(column_list) + "\n"
   


async def main():
   with open("table.html", "r") as file:
      html_text: str = file.read()
   
   print(await extract_table_data(html_text))

# if "__main__" == __name__ :
#    # asyncio.run(run("whats up"))
#    # main()