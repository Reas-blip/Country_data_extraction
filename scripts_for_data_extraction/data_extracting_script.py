from _collections_abc import dict_keys
# import asyncio
from asyncio import Semaphore, gather, run
from datetime import datetime
import json
import os
# from random import randint, random
from icecream import ic
from pathlib import Path
from typing import Any, Coroutine
import blackbox
from table import extract_prompt_data
# import aiofiles
from filelock import BaseFileLock, WindowsFileLock

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

async def write_or_read_with_file_lock(file_operation_coroutine: Coroutine, file_lock: BaseFileLock):
   with file_lock:
      return await file_operation_coroutine

async def read_industry_dict_from_file(file_path: str) -> dict[str, list[str]]:
   with open(file_path, "r") as file:
      industry_dict: str = file.read()
   return json.loads(industry_dict)

async def read_country_list(file_lock: BaseFileLock, country_list_file_path: Path | str=r"information_files\country.json"):
   async def read_country_list_without_file_lock(country_list_file_path: Path | str):
      with open(country_list_file_path, "r") as file:
         country_list: str = file.read()
      return json.loads(country_list)
   return await write_or_read_with_file_lock(read_country_list_without_file_lock(country_list_file_path), file_lock)
   
async def write_country_list_without_filelock(country_list: list[str], file_path: Path | str=r"information_files\country.json"):
   with open(file_path, "w") as file:
      file.write(json.dumps(country_list))

async def write_country_list(file_lock: BaseFileLock, country_list: list[str], file_path: Path | str=r"information_files\country.json"):
   return await write_or_read_with_file_lock(write_country_list_without_filelock(country_list, file_path), file_lock)
   
async def write_country_to_resume_temp_file(country: str, file_path: str | Path, file_lock: BaseFileLock):
   country_resume_list = await read_country_list(file_lock, file_path)
   country_resume_list.append(country)
   await write_country_list(file_lock, country_resume_list, file_path)
   
async def read_country_from_resume_temp_file(file_path: str | Path, file_lock: BaseFileLock):
   return await read_country_list(file_lock, file_path)

async def  remove_country_from_resume_temp_file(country: str, file_path: str | Path, file_lock: BaseFileLock):
   country_resume_list = await read_country_list(file_lock, file_path)
   country_resume_list.remove(country)
   print(country_resume_list)
   await write_country_list(file_lock, country_resume_list, file_path)
   
async def main() -> None:

   concurrency_limit = 3

   country_list_file_path = r"information_files\country.json"
   country_temp_file = r"information_files\contries_temp.json"
   file_lock = WindowsFileLock(r"information_files\contries_temp.json.lock")
   # print(str(file_lock))
   country_list: list[str] = await read_country_list(file_lock, country_list_file_path)
   # print(country_list)
   await resume_interupted_countries(country_list, concurrency_limit, country_temp_file, file_lock)
   await send_prompt_and_extract_data_for_countries(concurrency_limit, country_list, country_temp_file, file_lock)   

async def send_prompt_and_extract_data_for_countries(concurrency_limit: int, country_list, country_temp_file, file_lock: BaseFileLock):
   tasks = []
   for country in country_list:
      tasks.append(send_prompt_per_country(country, country_list, country_temp_file, file_lock))
   await semaphore_async(tasks, concurrency_limit)

async def resume_interupted_countries(country_list, concurrency_limit: int, country_temp_file, file_lock: BaseFileLock):
   country_temp_list = await read_country_from_resume_temp_file(country_temp_file, file_lock)
   resume_tasks = []
   if not country_temp_list:
      return
   for country in country_temp_list:
      resume_tasks.append(send_prompt_per_country(country,
                                                  country_list,
                                                  country_temp_file,
                                                  file_lock,
                                                  resume_interrupted_country=True))
   await semaphore_async(resume_tasks, concurrency_limit)

async def semaphore_async(tasks, concurrency_limit: int):
   async def run_task_with_semaphore(task: Coroutine, semaphore: Semaphore):
      async with semaphore:
         return await task  # Run the task when a slot is available

   # Create a semaphore to limit concurrency
   semaphore = Semaphore(concurrency_limit)

   # Create a list of tasks with semaphore control
   task_list = [run_task_with_semaphore(task, semaphore) for task in tasks]

   # Run tasks dynamically, adding new ones as slots open up
   return await gather(*task_list, return_exceptions=True)

async def send_prompt_per_country(country: str,
                                 country_list: list[str],
                                 country_temp_file: str,
                                 file_lock,
                                 resume_interrupted_country: bool=False):
  
   industry_dict: dict[str, list[str]] = await read_industry_dict_from_file("information_files/text.json")
   industry_sectorprompt_dict = await generate_dict_of_industries_to_sectors_prompt_list(industry_dict, country)
   # await write_country_list(file_lock, industry_sectorprompt_dict)
   # country_resume_list = await read_country_from_resume_temp_file(country_temp_file, file_lock)
   if not resume_interrupted_country:
      await write_country_to_resume_temp_file(country, country_temp_file, file_lock)
      await async_send_prompt_list(industry_sectorprompt_dict, country)
     
   print("prompting finished")
   retry_dict: dict[str, str] = await extract_data_for_each_country(country)
   await retry_failed_industries(retry_dict, industry_sectorprompt_dict)
   if retry_dict:
      await extract_data_for_each_country(country)
   # randoem = randint(3, 15)
   # print(randoem)
   # await sleep(randoem)
   reduced_country_list: list[str] = country_list
   await remove_country_from_resume_temp_file(country, country_temp_file, file_lock)
   await remove_country_and_write_new_list(country, reduced_country_list, file_lock)
   # await 

async def remove_country_and_write_new_list(country: str, country_list: list[str], file_lock: BaseFileLock):
   country_list = await read_country_list(file_lock)
   country_list.remove(country)
   await write_country_list(file_lock, country_list)
   
async def extract_data_for_each_country(country):
   industry_dict = await read_industry_dict_from_file("information_files/text.json")
   industries: dict_keys[str, list[str]] = industry_dict.keys()

   retry_dict: dict[str, str] = {}
   date = datetime.today().date()
   # print(date)
   save_data_file_dir = Path(rf"..\data_extracted\{date}\{country}.csv")
   if save_data_file_dir.exists():
      save_data_file_dir.unlink()
   if not save_data_file_dir.parent.exists():
      save_data_file_dir.parent.mkdir()
   data: str = f"|||{country}\n"
   
   for industry in industries:
      file: Path = Path(rf'..\data_extracted\{country}\{industry}.html')
      # print(save_data_file_dir.exists())
      try:
         await extract_prompt_data(file, industry, data, save_data_file_dir=save_data_file_dir)
      except FileNotFoundError:
         retry_dict[country] = industry
         continue
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
   
   for industry, sector_list in industry_dict.items():
      
      sector_list = await generate_prompt_for_industry(country, industry, sector_list)
      dict_of_industries_to_sectors_prompt_list[industry] = sector_list
   return dict_of_industries_to_sectors_prompt_list

async def write_page_content(file_dir: str | Path, page_html_content: str) -> None:
   directory = os.path.dirname(file_dir)
   # Check if the directory exists, if not, create it
   if not os.path.exists(directory):
      os.makedirs(directory)
   with open(file_dir, 'w') as file:
      file.write(page_html_content)
   print("wrote")
      
async def create_new_file(path:  Path | str) -> None:
   try:
      with open(path, 'x') as file:
         file.write("")
   except FileExistsError:
      pass



async def async_send_prompt_list(dict_of_industries_to_sectors_prompt_list: dict, country: str):
   async def send_prompts_per_industry(prompts_per_sector_list, industry, country: str, context_number: int=0):
      # ic()
      page_content = await blackbox.run(prompts_per_sector_list, context_number)
      print(industry)
      # if not page_content:
      #    page_content = await blackbox.run(prompts_per_sector_list, context_number)

      page_content_dir = Path(fr"..\data_extracted\{country}\{industry}.html")
      # ic()
      await write_page_content(page_content_dir, page_content)
   industry_dict = dict_of_industries_to_sectors_prompt_list

   tasks: list[Coroutine[Any, Any, None]] = []
   context_number = 1
   concurrency_limit = 11
   for industry, prompts_per_sector_list in industry_dict.items():
      task: Coroutine[Any, Any, None] = send_prompts_per_industry(prompts_per_sector_list, industry, country, context_number)
      print(context_number)
      context_number += 1
      
      if context_number > concurrency_limit:
         context_number = 1
      tasks.append(task)
   # ic()
   await semaphore_async(tasks, concurrency_limit)

# async def send_prompt_list(dict_of_industries_to_sectors_prompt_list: dict, country):
#    industry_dict = dict_of_industries_to_sectors_prompt_list
#    for industry, prompts_per_sector_list in industry_dict.items():
#       await send_prompt_list_per_industry(country, industry, prompts_per_sector_list)


async def retry_failed_industries(failed_country_industry_dict, industry_sectorprompt_dict):
   tasks = []
   context_no = 1
   for country, industry in failed_country_industry_dict.items():
      prompts_per_sector_list = industry_sectorprompt_dict[industry]
      task = send_prompt_list_per_industry(country, industry, prompts_per_sector_list, context_no)
      context_no += 1
      tasks.append(task)
   concurrency_limit = 5
   await semaphore_async(tasks, concurrency_limit)

async def send_prompt_list_per_industry(country: str, industry: str, prompts_per_sector_list: list[str], context_no):
   page_content = await blackbox.run(prompts_per_sector_list, context_no) 
   page_content_dir = Path(fr"..\data_extracted\{country}\{industry}.html")
   await write_page_content(page_content_dir, page_content)
   

async def extract_prompt_data_from_html_files(dict_for_prompt_response_per_industry_to_html_path: dict[str, str], 
                                             save_file_dir: str):
   industry_prompt_files_dict: dict[str, str] = dict_for_prompt_response_per_industry_to_html_path
   for industry, dir in industry_prompt_files_dict.items():
      await extract_prompt_data(dir, industry, save_file_dir)

         
if "__main__" == __name__ :
   run(main())