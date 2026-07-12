# Country Data Extraction

A pipeline that automates prompting multiple LLM web chat interfaces (ChatGPT, Gemini, Blackbox AI) to generate structured company/industry data per country, then parses the responses into clean CSV data — without using any paid LLM API.

## How it avoids API costs

Instead of calling an LLM API directly, each script (`chatgbt.py`, `chatgbt_async.py`, `gemini.py`, `blackbox.py`) connects Playwright to an **already-open, already-logged-in** Chrome tab via the Chrome DevTools Protocol:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

```python
browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
default_context = browser.contexts[0]
page = default_context.pages[0]
```

This attaches Playwright to a real, already-authenticated browser session instead of launching a fresh automated one — which means it rides on an existing login rather than needing separate API credentials for each LLM provider. `context.py` also uses `playwright-stealth` for cases where a fresh automated browser context is used instead of an attached one, to reduce the chance of being flagged as a bot.

## Pipeline

1. **Prompt generation** (`data_extracting_script.py`) — builds a tightly-specified prompt per industry/sub-industry/country combination, explicitly instructing the model to respond in a pipe-delimited table format (`Ranking|Company Name|Subindustry|Website|Careers Page|News/Information Page`) to make the response mechanically parseable
2. **Sending prompts** (`chatgbt.py` / `chatgbt_async.py` / `gemini.py` / `blackbox.py`) — drives the relevant chat UI, submits the prompt, and waits for the response to finish generating
3. **Extraction** (`table.py`) — regexes the pipe-delimited table out of the raw HTML response (`extract_prompt_data`) and appends the parsed rows to a CSV file
4. **Industry taxonomy prep** (`industry_text_to_dict.py`) — converts a plain-text, indent-based industry/sub-industry list into a structured JSON dict used to drive which prompts get generated

## Project structure

```
blackbox.py              # drives Blackbox AI's web chat via CDP
chatgbt.py                # drives ChatGPT's web chat via CDP (sync)
chatgbt_async.py          # async variant, for running multiple chats concurrently
gemini.py                  # drives Gemini's web chat via CDP
context.py                 # browser/context setup helpers, including playwright-stealth usage
data_extracting_script.py  # prompt generation + orchestration
data_extracting_script_working.py
                           # an in-progress/working variant of the above
industry_text_to_dict.py   # converts a raw industry/sub-industry text list into JSON
table.py                   # regex-based extraction of pipe-delimited tables from LLM HTML
                           # responses, written to CSV via aiofiles
```

## Concurrency safety

Writing extracted rows to a shared CSV from multiple async tasks risks interleaved/corrupted writes, so `data_extracting_script.py` uses `filelock` to serialize file access across concurrent extraction tasks, and `table.py` uses `aiofiles` for non-blocking async file appends.

## Requirements

- Python 3.10+
- Google Chrome, launched with `--remote-debugging-port=9222` and already logged into the relevant LLM site(s) before running any script
- `playwright` (with browsers installed: `playwright install`)
- `playwright-stealth`
- `aiofiles`
- `filelock`
- `icecream`

## Running it

```bash
pip install playwright playwright-stealth aiofiles filelock icecream
playwright install

# 1. Launch Chrome with remote debugging enabled, and log into the target LLM site manually
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# 2. Verify the debug port is live:
#    visit http://localhost:9222/json/version — you should see browser/version info back

# 3. Run the extraction pipeline
python data_extracting_script.py
```

## Known limitations

- Depends on a specific already-open Chrome instance and manual login — there's no unattended/headless mode
- The pipe-delimited table format is enforced through prompt instructions, not a strict output schema, so a model that ignores formatting instructions will produce rows that fail to parse
- Regex-based extraction (`table.py`) is coupled to each LLM's current response HTML structure and formatting quirks, so UI changes on the ChatGPT/Gemini/Blackbox side can break extraction
- No automated tests
- 
