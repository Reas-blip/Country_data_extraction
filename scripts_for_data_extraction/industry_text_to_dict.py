import json


file_line_str = []
with open("text.txt", "r") as file:
   file_line_str: list[str] = file.readlines()
   
# print(file_str)
industry_dict: dict[str, list[str]] = {}
industry = ""
for line in file_line_str:
   line: str = line.strip()
   if "." not in line:
      industry: str =  line
      industry_dict[industry] = []
   if "." in line:
      sub_industry: str = line.split(".")[-1]
      industry_dict[industry].append(sub_industry.strip())
      
industry_dict_text: str = json.dumps(industry_dict, indent=4, separators=(', ', ': '))
print(industry_dict_text)
with open("text.json", "w") as file:
   file.write(industry_dict_text)