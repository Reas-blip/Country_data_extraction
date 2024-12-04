from _collections_abc import dict_keys
import asyncio
from datetime import datetime
import json
import os
from icecream import ic
from pathlib import Path
from typing import Any, Coroutine
import blackbox
from table import extract_prompt_data
import aiofiles

async def generate_prompt(industry: str, sector: str, country: str) -> str | None:
   prompt: str = f"""According to the industry reputation and project history metrics, generate for the top 10 companies under the {industry} sub-industry in the {sector} Sector in {country} ,please write it in plain text accroding to the instructions below,1. Ranking 2. Company Name 3. Subindustry 4. Website 5. Careers Page 6. News/Information Page.

VERY IMPORTANT INSTRUCTION MUST OBEY LIKE SOMEONE'S LIFE DEPENDS ON IT
do not include disclamers or any notice in this response

please please write the text in a bash code form scripting language code
dont use bash syntax or anything related to bash just write the text in bash code form

use this example to format the table
"Ranking|Company Name|Subindustry|Website|Careers Page|News/Information Page
1|Game Nigeria|Specialty Retail|https://www.game.co.za/ng|https://www.game.co.za/ng/careers|https://www.game.co.za/ng/news
2|PZ Cussons|Specialty Retail|https://www.pzcussons.com|https://www.pzcussons.com/careers|https://www.pzcussons.com/news
3|Shoprite Holdings|Specialty Retail|https://www.shoprite.com.ng|https://www.shoprite.com.ng/careers|https://www.shoprite.com.ng/news
4|Supermart Nigeria|Specialty Retail|https://www.supermart.ng|https://www.supermart.ng/careers|https://www.supermart.ng/news
5|HealthPlus|Specialty Retail|https://www.healthplusng.com|https://www.healthplusng.com/careers|https://www.healthplusng.com/news
6|Medplus|Specialty Retail|https://www.medplusng.com|https://www.medplusng.com/careers|https://www.medplusng.com/news
7|Konga|Specialty Retail|https://www.konga.com|https://www.konga.com/careers|https://www.konga.com/news
8|Beverly Hills|Specialty Retail|https://www.beverlyhills.ng|https://www.beverlyhills.ng/careers|https://www.beverlyhills.ng/news
9|Ariya|Specialty Retail|https://www.ariya.com.ng|https://www.ariya.com.ng/careers|https://www.ariya.com.ng/news
10|Lagos Book Club|Specialty Retail|https://www.lagosbookclub.com|https://www.lagosbookclub.com/careers|https://www.lagosbookclub.com/news
"

"""
   # print(prompt)
   return prompt

async def read_industry_dict_from_file(file_path: str) -> dict[str, list[str]]:
   async with aiofiles.open(file_path, "r") as file:
      industry_dict: str = await file.read()
   return json.loads(industry_dict)

# async def format_prompt_response(prompt_response, sector) -> str:
#    csv_data: str = re.sub(r'---\|---\|---\|---\|---\|---\n',"" , prompt_response)
#    headings: str = f"""|||{sector}|||
# """
#    return headings + csv_data

async def read_country_list(file_path: Path | str="country.json"):
   async with aiofiles.open(file_path, "r") as file:
      country_list: str = await file.read()
   return json.loads(country_list)

async def write_country_list(country_list: list[str], file_path: Path | str="country.json"):
   async with aiofiles.open(file_path, "w") as file:
      await file.write(json.dumps(country_list))
   
async def add_country_to_resume_temp_file(country: str, file_path: str | Path):
   country_list = await read_country_list(file_path)
   country_list.append(country)
   await write_country_list(country_list, file_path)
   
   
async def main() -> None:
   country_list: list[str] = await read_country_list()
# ["Benin", "Botswana", "Burkina Faso", "Burundi"]
   # await create_new_file("industry_data.csv")
   data_str = ""
   tasks = []
   for country in country_list:
      # print()
      await send_prompt_per_country(country, country_list)
   #    tasks.append(send_prompt_per_country(country, country_list))
      
   # concurrency_limit = 1

   # # Create a semaphore to limit concurrency
   # semaphore = asyncio.Semaphore(concurrency_limit)

   # # Create a list of tasks with semaphore control
   # task_list = [run_task_with_semaphore(task, semaphore) for task in tasks]

   # # Run tasks dynamically, adding new ones as slots open up
   # await asyncio.gather(*task_list, return_exceptions=True)


async def send_prompt_per_country(country: str, country_list: list[str]):
   # data_str += f"|||{country}\n"
   # current_script_path = Path(os.path.abspath(__file__))
   industry_dict: dict[str, list[str]] = await read_industry_dict_from_file("./text.json")
   industry_sectorprompt_dict = await generate_dict_of_industries_to_sectors_prompt_list(industry_dict, country)
   await async_send_prompt_list(industry_sectorprompt_dict, country)
      # industry_list = list(industry_sectorprompt_dict.keys())
      # dir_dict = await send_prompt_list(industry_sectorprompt_dict, country)
      # await extract_prompt_data_from_html_files(dir_dict, file_path)
   print("prompting finished")
   retry_dict: dict[str, str] = await extract_data_for_each_country(country)
   await retry_failed_industries(retry_dict, industry_sectorprompt_dict)
   if retry_dict:
      await extract_data_for_each_country(country)
   reduced_country_list: list[str] = country_list
   await remove_country_and_write_new_list(country, reduced_country_list)

async def remove_country_and_write_new_list(country: str, country_list: list[str]):
   country_list.remove(country)
   await write_country_list(country_list)
   
async def extract_data_for_each_country(country):
   industry_dict = await read_industry_dict_from_file("./text.json")
   industries: dict_keys[str, list[str]] = industry_dict.keys()
   # current_script_path = Path(os.path.abspath(__file__))
   retry_dict: dict[str, str] = {}
   date = datetime.today().date()
   # print(date)
   save_data_file_dir = Path(rf".\{date}\{country}.csv")
   if save_data_file_dir.exists():
      save_data_file_dir.unlink()
   if not save_data_file_dir.parent.exists():
      save_data_file_dir.parent.mkdir()
   data: str = f"|||{country}\n"
   
   for industry in industries:
      file: Path = Path(rf'.\{country}\{industry}.html')
      print(save_data_file_dir.exists())
      try:
         await extract_prompt_data(file, industry, data, save_data_file_dir=save_data_file_dir)
      except FileNotFoundError:
         retry_dict[country] = industry
      data = ""
      ic(retry_dict)
   return retry_dict

async def generate_dict_of_industries_to_sectors_prompt_list(industry_dict, country):
   async def generate_prompt_for_industry(country, industry, sector_list):
      # list of prompts for sectors in a particular industry
      prompts_per_sector_list = []
      for sector in sector_list:
         # data_str += f"|||{sector}\n"
         prompt: str | None = await generate_prompt(industry, sector, country)
         prompts_per_sector_list.append(prompt)
      return prompts_per_sector_list
   
   # the dict of {industry: list of prompts for the sectors in this industry } 
   dict_of_industries_to_sectors_prompt_list = {}
   # print(len(industry_dict.keys()))
   for industry, sector_list in industry_dict.items():
      
      sector_list = await generate_prompt_for_industry(country, industry, sector_list)
      dict_of_industries_to_sectors_prompt_list[industry] = sector_list
   return dict_of_industries_to_sectors_prompt_list

async def write_page_content(file_dir: str | Path, page_html_content: str) -> None:
   directory = os.path.dirname(file_dir)
   # Check if the directory exists, if not, create it
   if not os.path.exists(directory):
      os.makedirs(directory)
   async with aiofiles.open(file_dir, 'w') as file:
      await file.write(page_html_content)
   print("wrote")
      
async def create_new_file(path:  Path | str) -> None:
   try:
      with open(path, 'x') as file:
         file.write("")
   except FileExistsError:
      pass

async def run_task_with_semaphore(task: Coroutine, semaphore: asyncio.Semaphore):
   async with semaphore:
      return await task  # Run the task when a slot is available


async def async_send_prompt_list(dict_of_industries_to_sectors_prompt_list: dict, country: str):
   industry_dict = dict_of_industries_to_sectors_prompt_list
   # dict_for_prompt_response_per_industry_to_html_path = {}
   async def send_prompts_per_industry(prompts_per_sector_list, industry, country: str, context_number: int=0):
      # ic(len(prompts_per_sector_list))
      page_content = await blackbox.run(prompts_per_sector_list, context_number)
      # if not page_content:
      #    page_content = await blackbox.run(prompts_per_sector_list, context_number)

      page_content_dir = Path(fr".\{country}\{industry}.html")
      ic()
      await write_page_content(page_content_dir, page_content)
   tasks: list[Coroutine[Any, Any, None]] = []
   context_number = 1
   concurrency_limit = 3
   for industry, prompts_per_sector_list in industry_dict.items():
      # print(len(prompts_per_sector_list))
      task: Coroutine[Any, Any, None] = send_prompts_per_industry(prompts_per_sector_list, industry, country, context_number)
      print(context_number)
      context_number += 1
      
      if context_number > concurrency_limit:
         context_number = 1
      tasks.append(task)
   
   # Create a semaphore to limit concurrency
   semaphore = asyncio.Semaphore(concurrency_limit)

   # Create a list of tasks with semaphore control
   task_list = [run_task_with_semaphore(task, semaphore) for task in tasks]
   len(task_list)
   # Run tasks dynamically, adding new ones as slots open up
   await asyncio.gather(*task_list, return_exceptions=True)

async def send_prompt_list(dict_of_industries_to_sectors_prompt_list: dict, country):
   industry_dict = dict_of_industries_to_sectors_prompt_list
   dict_for_prompt_response_per_industry_to_html_path = {}
   for industry, prompts_per_sector_list in industry_dict.items():
      await send_prompt_list_per_industry(country, industry, prompts_per_sector_list)
   # this line is not needed the paths to the html files for the industry are generated 
   # using the country and the industry name from the text.json file which contains
   # all the industries
   # return dict_for_prompt_response_per_industry_to_html_path

async def retry_failed_industries(failed_country_industry_dict, industry_sectorprompt_dict):
   tasks = []
   for country, industry in failed_country_industry_dict.items():
      prompts_per_sector_list = industry_sectorprompt_dict[industry]
      task = send_prompt_list_per_industry(country, industry, prompts_per_sector_list)
      tasks.append(task)
   concurrency_limit = 5
   semaphore = asyncio.Semaphore(concurrency_limit)
   
   task_list = [run_task_with_semaphore(task, semaphore) for task in tasks]
   await asyncio.gather(*task_list, return_exceptions=True)

async def send_prompt_list_per_industry(country: str, industry: str, prompts_per_sector_list: list[str]):
   page_content = await blackbox.run(prompts_per_sector_list) 
   page_content_dir = Path(fr".\{country}\{industry}.html")
      # await create_new_file(page_content_dir)
   await write_page_content(page_content_dir, page_content)
   # dict_for_prompt_response_per_industry_to_html_path[industry] = page_content_dir

async def extract_prompt_data_from_html_files(dict_for_prompt_response_per_industry_to_html_path: dict[str, str], 
                                             save_file_dir: str):
   industry_prompt_files_dict: dict[str, str] = dict_for_prompt_response_per_industry_to_html_path
   for industry, dir in industry_prompt_files_dict.items():
      await extract_prompt_data(dir, industry, save_file_dir)

         
if "__main__" == __name__ :
   asyncio.run(main())