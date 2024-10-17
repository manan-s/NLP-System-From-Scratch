import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os

file_path = '11711_datasources.xlsx'
sheet_name = 'URLs'

df = pd.read_excel(file_path, sheet_name=sheet_name)
urls = df.iloc[:, 0].dropna().tolist()

def fetch_and_parse(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_text(text):
    cleaned_text = re.sub(r'\s+', ' ', text) 
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    return cleaned_text.strip()

output_dir = 'parsed_files'
os.makedirs(output_dir, exist_ok=True)

for url in urls:
    print(f"Fetching: {url}")
    text_content = fetch_and_parse(url)
    if text_content:
        cleaned_content = clean_text(text_content)
        
        output_file_path = os.path.join(output_dir, f"{url.replace('http://', '').replace('https://', '').replace('/', '_').replace('&y=', '_').replace('?n=', '_').replace('&cat=0','').replace('?TYPE=', '').replace('&CID=','').replace('&v=d', '_').replace('?page=','')}.txt")
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)

print(f"Parsed content has been written to individual files in the '{output_dir}' directory.")