
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

import json
import subprocess
from typing import List
from icecream import ic
import asyncio
import re
from playwright.async_api import async_playwright, Playwright, expect
from playwright.async_api._generated import Browser, BrowserContext, Locator, Page
from playwright_stealth import stealth_async

async def start_debug_browser():
   command: List[str] = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--remote-debugging-port=9222"]
   subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

async def setup_browser(playwright: Playwright) -> Browser:
   curl_command: list[str] = [
                  "curl", "-f", "http://localhost:9222/json/version",
   ]
      # Run the curl command using subprocess
   result: subprocess.CompletedProcess[str] = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
   result_text: str = result.stdout.strip()
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
async def ask_chatgbt(playwright: Playwright, prompts: list[str], context_nubmer, reload_chatgbt: bool=False) -> str | None:
   # Connect to an existing instance of Chrome using the connect_over_cdp method.
   # context: BrowserContext = await init_playwright_new_context(playwright, context_nubmer)
   context: Page = await init_playwright_page(playwright)
   new_page: Page = await init_new_page(context.context)
   # prompts = []
   prompts.append("thanks")
   
   for prompt in prompts:
      print("fffe")
      await send_prompt_to_chatgbt_page(new_page, prompt)
      # task1 = check_login_poppup(new_page)
      # await task
   new_page_content: str = await new_page.content()
   return new_page_content

async def change_free_gen_to_free_when_prompt_is_generating(page: Page, *, selector):
   
   # number_of_prompts_in_page: int = await page.locator("div.whitespace-pre-wrap").count()
   # if number_of_prompts_in_page == 0:
   #    pass
   locator_tag: Locator = page.locator(selector)
   while True:
      if not locator_tag:
         await write_free_gen("gen")
         continue
      else:
         await write_free_gen("free")
         break
      
   # Check if the locator tag exists on the page
   # for page in context.pages:
   #    # Check if the page URL contains the specified domain
   #    if domain not in page.url:
   #       continue
   #    number_of_prompts_in_page = await page.locator("div.whitespace-pre-wrap").count()
   #    if number_of_prompts_in_page == 0: 
   #       continue
   #    locator_tag: Locator = page.locator(selector,
   #                                        has_text=r'Ranking\|Company Name'
   #                                        ).nth(number_of_prompts_in_page-1)
   #    # Check if the locator tag exists on the page
   #    # await expect(locator_tag).to_be_attached()
   #    await expect(locator_tag).to_contain_text(re.compile(r'Ranking\|Company Name'), timeout=6000)
   #    await expect(page.get_by_label("Stop streaming")).to_be_attached(timeout=70000)
   #    # if await .count() > 0:
   #    #    return True
   #    # return False

async def wait_for_free_gen_to_be_free() -> None:
   free_gen: str = await read_free_gen()
   while free_gen != "free": 
      # if free_gen != "free":
      free_gen: str = await read_free_gen()
      ic(free_gen)
      ic("continue")
      continue
      

async def send_prompt_to_chatgbt_page(page: Page, prompt: str) -> str | None:
   send: Locator = page.get_by_label("Send prompt")
   await expect(send).to_be_disabled(timeout=100000)
   chat_box: Locator = page.locator("div.ProseMirror")
   await chat_box.fill(prompt)
   await expect(send).to_be_enabled(timeout=100000)
   # await wait_for_free_gen_to_be_free()
   await send.click()
   # await change_free_gen_to_free_when_prompt_is_generating(page, selector="div > pre")
   
   await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
   
   try:
      await expect(page.get_by_label("Stop streaming")).to_be_attached(timeout=5000)
   except AssertionError:
      regenerate_response_button: Locator = page.get_by_test_id("regenerate-thread-error-button")
      await expect(regenerate_response_button).to_be_enabled(timeout=5000)
      await regenerate_response_button.click()
      await expect(page.get_by_label("Stop streaming")).to_be_attached(timeout=5000)
   
   await expect(page.get_by_label("Stop streaming")).not_to_be_attached(timeout=100000)
   # await expect(page.locator("'div.result-streaming.markdown.prose'")).not_to_be_attached(timeout=100000)
   # response: Locator = page.locator("code[class]").last
   
   # response_text: str | None = await response.text_content()
   # return response_text


async def init_new_page(context: BrowserContext):
   # browser: Browser = page.context.browser # type: ignore
   # context: BrowserContext = page.context # type: ignore
   # await context.clear_cookies(domain=re.compile("chatgbt"))
   new_page: Page = await context.new_page()
   print("ee")
   # await stealth_async(new_page)
   await new_page.goto("https://chatgpt.com/")
   try:
      # if 
      await expect(new_page.locator("a[href='#']")).to_be_enabled(timeout=10000)
      await new_page.locator("a[href='#']").click(timeout=10000)
   except AssertionError:
      pass
   try:
      await expect(new_page.locator("button > span", has_text="Summarize text").first).to_be_enabled(timeout=10000)
   except AssertionError:
      try:
         await expect(new_page.locator("div.truncate").first).to_be_enabled(timeout=10000)
      except AssertionError:
         await expect(new_page.locator("div.line-clamp-3").first).to_be_enabled(timeout=10000)
         
   return new_page
   # context: BrowserContext = page.context # type: ignore
   # await context.clear_cookies(domain=re.compile("chatgbt"))
   # new_page: Page = await context.new_page()
   # await new_page.goto("https://chatgpt.com/")
   # try:
   #    await expect(new_page.locator("button > span", has_text="Summarize text").first).to_be_enabled(timeout=10000)
   # except AssertionError:
   #    await expect(new_page.locator("div.truncate").first).to_be_enabled(timeout=10000)
      
   # return new_page
   
async def init_playwright_page(playwright: Playwright, reload_chatgbt: bool=False) -> Page:
   browser: Browser = await setup_browser(playwright)
   default_context: BrowserContext = browser.contexts[0]
   page: Page = default_context.pages[0]
   if reload_chatgbt:
      await reload_chatgbt_page(page)
   return page

async def init_playwright_new_context(playwright: Playwright, context_nubmer, reload_chatgbt: bool=False) -> BrowserContext:
   browser: Browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
   default_context: BrowserContext = await browser.new_context()
   await default_context.new_page()
   await setup_new_context(default_context, context_nubmer)
   
   return default_context

async def load_cookies_from_file(context: BrowserContext, filename="cookies.json"):
   # Load cookies from a file
   with open(filename, "r") as file:
      cookies = json.load(file)
   
   # Add cookies to the context
   await context.add_cookies(cookies)

async def setup_new_context(context: BrowserContext, context_nubmer):
   await load_cookies_from_file(context, filename=f"cookies{str(context_nubmer)}.json")
   
   
async def reload_chatgbt_page(page: Page):
   await page.context.clear_cookies(domain="chatgpt.com")
   await page.reload()
   await page.wait_for_load_state("load")
   try:
      await expect(page.get_by_text("What can I help with?")).to_be_visible(timeout=10000)
   except AssertionError:
      await page.goto("https://chatgpt.com/")
      # try: 
      #    await expect(page.get_by_text("Stay logged out")).to_be_visible(timeout=10000)
      #    await page.get_by_text("Stay logged out").click()
      # except AssertionError:
         # await reload_chatgbt_page(page)
   
   # try:
   #    # Try to locate the element with the specified text
   #    element = await page.wait_for_selector("text=Stay logged out", timeout=5000)
      
   #    # If the element is found, click it
   #    if element:
   #          await element.click()
   #          print("Clicked 'Stay logged out' link successfully!")
   #    else:
   #          print("'Stay logged out' link not found.")

   # except:
   #    print("'Stay logged out' link not found within the timeout period.")

# async def gather(playwright, prompts, context_nubmer):
#    context = await init_playwright_new_context(playwright, context_nubmer)
#    task = ask_chatgbt(context, prompts, context_nubmer)
#    for i in context.pages:
#       if "chatgbt" in i.url:
#          task1 = check_login_poppup(i)
#    await asyncio.gather(task, task1)

async def run(prompts, context_nubmer, reload_chatgbt: bool=False) -> str | None:
   async with async_playwright() as playwright:
      # context = , context_nubmer)
      return await ask_chatgbt(playwright, prompts, context_nubmer)
   
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

# if "__main__" == __name__ :
#    # asyncio.run(run("whats up"))
#    # main()