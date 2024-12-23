
r"""this script connects to a already open blackbox ai open tab in chrome to set this up run 
   this command `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
   and go to the tab you want in this case blackbox ai to test if it worked then go to 
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

import json
from typing import Literal
from icecream import ic
import asyncio
import re
from playwright.async_api import async_playwright, Playwright, expect
from playwright.async_api._generated import Browser, BrowserContext, Locator, Page, LocatorAssertions
from websocket import send

async def start_debug_browser():
   chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
   args = ["--remote-debugging-port=9222"]

   process = await asyncio.create_subprocess_exec(
      chrome_path, *args,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
   )

   # Wait for the process to start and capture the output
   stdout, stderr = await process.communicate()

async def setup_browser(playwright: Playwright) -> Browser:
   curl_command = r"curl -f http://localhost:9222/json/version"
   result = await asyncio.create_subprocess_shell(
      curl_command,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
   )
   stdout, _ = await result.communicate()
   result_text = stdout.decode().strip()
   print(result_text)
   if "webSocketDebuggerUrl" not in result_text:
      await start_debug_browser()
   browser: Browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
   return browser
   

async def write_free_gen(state_to_write ,dir='free_gen.txt'):
   with open(dir, "w") as file:
      file.write(state_to_write)
   string: str = await read_free_gen(dir)
   print(string)
   return string

async def check_login_poppup(page: Page) -> None:
   while page:
      if not page.locator("a[href='#']"):
         continue
      try:
         await expect(page.locator("a[href='#']")).to_be_enabled(timeout=10000)
         await page.locator("a[href='#']").click(timeout=10000)
      except AssertionError:
         continue
      else:
         break
      
   
async def read_free_gen(dir='free_gen.txt') -> str:
   with open(dir, "r") as file:
      return file.read()

# Start a new session with Playwright using the sync_playwright function.
async def ask_blackbox(playwright: Playwright, prompts: list[str], context_number=1, reload_blackbox: bool=False):# -> Any | str:
   # Connect to an existing instance of Chrome using the connect_over_cdp method.
   context: BrowserContext = await init_playwright_new_context(playwright)
   new_page: Page = await init_new_page(context)
   subindustry_list  = []
   table_text_list  = []
   for prompt in prompts:
      ic(context_number)
      table_text = await send_prompt_to_blackbox_page_recursive_retry(new_page, prompt)
      table_text = re.search(r'(?<=```)([\w\W]*)(?=```)', table_text).group(1) # type: ignore
      subindustry_match = re.search(r'(?<=in the )(.*?)(?= Sector)', prompt)
      subindustry_list.append(subindustry_match.group(1)) # type: ignore
      table_text_list.append(table_text)   
      # print(table_text)   
   if len(table_text_list) != len(prompts):
      await context.close()
      ic("restarting prompt")
      return await ask_blackbox(playwright, prompts, context_number)
    
   data: str = ""
   for i,table_text in enumerate(table_text_list):
      if not await verify_table_complete(table_text):
         return await ask_blackbox(playwright, prompts, context_number)  
      data += f"<code bash'>{table_text.replace('\"', '', 1)}\n|||{subindustry_list[i]}<\n"
 
   if not data: 
      await context.close()
      ic("restarting empty data")
      return await ask_blackbox(playwright, prompts, context_number)
   
   new_page_content: str = data
   await context.close()
   return new_page_content
async def verify_table_complete(table_text,):
   industry_amount: int = len(re.findall(r'[0-9]{1,2}\|.+?\|.+?\|.+?\|.+?\|.+?', table_text))
   if industry_amount != 10:
      ic("incomplete")
      return False
   return True 
      
async def change_free_gen_to_free_when_prompt_is_generating(page: Page, *, selector):
   
   locator_tag: Locator = page.locator(selector)
   while True:
      if not locator_tag:
         await write_free_gen("gen")
         continue
      else:
         await write_free_gen("free")
         break
      
async def wait_for_free_gen_to_be_free() -> None:
   free_gen: str = await read_free_gen()
   while free_gen != "free": 
      # if free_gen != "free":
      free_gen: str = await read_free_gen()
      ic(free_gen)
      ic("continue")
      continue
      
async def send_prompt_to_blackbox_page_recursive_retry(page: Page, prompt: str):# -> Any | str:
   try:
      table_text: str = await send_prompt_to_blackbox_page(page, prompt)
      if not await verify_table_complete(table_text):
         table_text: str = await send_prompt_to_blackbox_page_recursive_retry(page, prompt)
      print("success")
      return table_text
   except AssertionError as e:
      await page.reload()
      print(e)
      return await send_prompt_to_blackbox_page_recursive_retry(page, prompt)
   
async def send_prompt_to_blackbox_page(page: Page, prompt: str, prompt_no: int=0) -> str:
   send_button: Locator = page.locator("button[type='submit']")
   await expect(send_button).to_be_enabled(timeout=30000)
   chat_box: Locator = page.locator("textarea#chat-input-box")
   await chat_box.fill(prompt, timeout=20000)
   print(chat_box)

   expected_url = "https://www.blackbox.ai/api/chat"

   async with page.expect_response(
      lambda response: response.url == expected_url and response.status == 200
   ) as response_info:
   
      await send_button.click()
   
   await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
   await expect(send_button).to_be_enabled(timeout=50000)

   return await (await response_info.value).text()
   


async def init_new_page(context: BrowserContext):
   ic("new page")
   new_page: Page = await context.new_page()

   try:
      await new_page.goto("https://www.blackbox.ai/?model=gpt-4o", wait_until="domcontentloaded",timeout=20000)
      await expect(new_page.locator("button[type='submit']")).to_be_enabled(timeout=10000)
      print("submit found")
   except Exception as e:
      print(e)
      await context.close()
      return await init_new_page(context)

   else:return new_page
   
async def init_playwright_page(playwright: Playwright, reload_blackbox: bool=False) -> Page:
   browser: Browser = await playwright.chromium.launch(channel="msedge", headless=True)
   
   default_context: BrowserContext = browser.contexts[0]
   page: Page = default_context.pages[0]
   if reload_blackbox:
      await reload_blackbox_page(page)
   return page

async def init_playwright_new_context(playwright: Playwright) -> BrowserContext:
   browser: Browser = await playwright.chromium.launch(channel="msedge", headless=True)

   default_context: BrowserContext = await browser.new_context(viewport={'width': 1280, 'height': 720})
   
   return default_context

async def load_cookies_from_file(context: BrowserContext, filename="cookies.json"):
   # Load cookies from a file
   with open(filename, "r") as file:
      cookies = json.load(file)
   
   # Add cookies to the context
   await context.add_cookies(cookies)

async def setup_new_context(context: BrowserContext, context_nubmer):
   await load_cookies_from_file(context, filename=f"cookies{str(context_nubmer)}.json")
   
   
async def reload_blackbox_page(page: Page):
   await page.context.clear_cookies(domain="chatgpt.com")
   await page.reload()
   await page.wait_for_load_state("load")
   try:
      await expect(page.get_by_text("What can I help with?")).to_be_visible(timeout=10000)
   except AssertionError:
      await page.goto("https://chatgpt.com/")

async def run(prompts, context_nubmer=1, reload_blackbox: bool=False):# -> Any | str:
   async with async_playwright() as playwright:
      # context = , context_nubmer)
      return await ask_blackbox(playwright, prompts, context_nubmer)
   
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
   
   ic(await extract_table_data(html_text))
