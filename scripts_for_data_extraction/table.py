import json
import os
from pathlib import Path
import re
import asyncio
import aiofiles
from icecream import ic

# from scripts_for_data_extraction.data_extracting_script import write_country_to_resume_temp_file

async def append_prompt_data_to_file(csv_file_path:  Path | str, prompt_table_data: str):
   async with aiofiles.open(csv_file_path, "a") as csv_file:
      # print()
      await csv_file.write(prompt_table_data)

async def extract_prompt_data(html_file_dir: Path | str, industry: str, data: str="", save_data_file_dir: Path | str="industry_data.csv") -> None:
   # html_text = ""
   industry_dict: dict[str, list[str]] = await read_industry_dict_from_file("information_files/text.json")
   with open(html_file_dir, "r") as file:
      html_text: str = file.read()
   print(html_file_dir)
   table_list = re.findall(r'<code[^>]*bash[^>]>\s*(?=[^|]+?\|[^|]+?\|)([^<]+)<', html_text)   
   reference_list = []
   subindustry_completed_list = []
   data += f"|||{industry.title()}\n"
   print(len(table_list))
   
   for prompt_data, subindustry in zip(table_list, industry_dict[industry.title()]):
      prompt_data: str = await remove_amp_string(prompt_data)
      prompt_data = re.sub(r'[0-9]{2}(?=.{1,2}\|)|(?<![0-9])([0-9]|[0-9]")(?!0)(?=.{1}\||R)', "", prompt_data)
      print(prompt_data)
      # subindustry = re.findall(r'(?<=\|\|\|)(.*)\b', prompt_data)[0] 
      prompt_data = re.sub(r'\|\|\|(.*)\b', "", prompt_data) # type: ignore
      print(subindustry)
      data += f"|||{subindustry.capitalize()}\n{prompt_data}\n"
      subindustry_completed_list.append(subindustry)
      await append_prompt_data_to_file(save_data_file_dir, data)
      data = ""
      
async def read_data_from_file(file_path: Path | str):
   with open(file_path, "r") as file:
      return file.read()     
      
async def run():
   path: Path = Path(r'../data_extracted')
   files: Path = Path(rf'C:\Users\Okeniyi Treasure\Documents\Python\requests\Country_data_extraction\2024-11-23')
   csv_file_list = path.rglob("*.csv")      
   print(list(files.rglob("*.csv")))
   country_dict = {}
   for file in csv_file_list:
      country = file.stem
      file_str = (await read_data_from_file(file)).replace(f"|||{country}", "")
      no_of_tables = re.findall(r'[0-9].{1,2}\|.+\|.+\|.+\|.+\|.+', file_str)
      print(len(no_of_tables))
      if len(no_of_tables) == 163:
         continue        
      industry_table_list = re.findall(r'\|\|\|[^|]*?(?=\s+\|\|\|)[\w\W]*?(?=\|\|\|[^|]*?\s+\|\|\|)', file_str+"||| |||")
      industry_list = []
      for table in industry_table_list:
         content_list = re.findall(r'[0-9]{1,2}\|.+\|.+\|.+\|.+\|.+', table)
         ic(len(content_list))
         if len(content_list) % 10 != 0:
            industry = re.search(r'(?<=\|\|\|)([^|]*?)(?=\s+\|\|\|)', table).group(1)
            ic(industry)
            industry_list.append(industry)
         if industry_list:country_dict[country] = industry_list
      print(country_dict)
   await write_country_list_without_filelock(country_dict, "information_files/country_incomplete.json")
            
            

   # await write_country_list_without_filelock(country_list, "country.json")
      # print(file)
      # await extract_prompt_data(file, industry, "ghana.csv")
   # with open("industry_data.csv", "r")as filee:
   #    industry_dict = filee.read()
   # for html_dir in path.rglob("*.html"):
   #    print(html_dir)
   #    c+=await extract_prompt_data(c,html_dir, html_dir.name.strip(".html"))
   # print(html_dir)

async def read_industry_dict_from_file(file_path: str) -> dict[str, list[str]]:
   with open(file_path, "r") as file:
      industry_dict: str = file.read()
   return json.loads(industry_dict)
async def write_country_list_without_filelock(country_list: list[str], file_path: Path | str=r"information_files\country.json"):
   with open(file_path, "w") as file:
      file.write(json.dumps(country_list))



   
# def main():
   # i used this to correct the incomplete response chatgbt give and replaced it with
   # complete one which was in the html content an example is in industry/example.html
   # parent = Path(r"C:\Users\Okeniyi Treasure\Documents\Python\requests\industries")
   # for html in parent.glob("*.html"):
   #    with open(html, "r") as file:
   #       html_content = file.read()
      
   #    completed = re.search("```([^`]*)```", html_content)
   #    completed_data  = completed.group(1)
   #    print(completed_data)
   #    html_content = re.sub(r"```[^`]*```", "", html_content)
   #    incompelete = re.findall(r'<code[^>]*bash\">\s*([^<]*)<', html_content)[-1]
   #    html_content = html_content.replace(incompelete, completed_data)
   #    with open(html, "w") as file:
   #       file.write(html_content)
   
async def remove_amp_string(html_text) -> str:
   return re.sub("amp;", "", html_text)
if "__main__" == __name__ :
   # main()
   asyncio.run(run())
      