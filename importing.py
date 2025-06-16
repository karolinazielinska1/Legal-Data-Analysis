import os
import sys
sys.setrecursionlimit(50000)
import pickle
import json 
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

import os
import json
import pickle
import requests
from bs4 import BeautifulSoup

#currently there are 5163 pages
def download_judgments(start_page=0, end_page=5163, save_dir="orzeczenia"):
    os.makedirs(save_dir, exist_ok=True)
    
    for i in range(start_page, end_page):
        try:
            url = f"https://www.saos.org.pl/api/dump/judgments?pageSize=100&pageNumber={i}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            data = json.loads(soup.text)['items']
        except Exception as e:
            print(f"❌ Error in request on page {i}: {e}")
            continue

        print(f"✅ Downloaded page {i} of {end_page}")

        for j, item in enumerate(data):
            try:
                file_index = i * 100 + j
                file_path = os.path.join(save_dir, f"{file_index}.json")
                with open(file_path, "wb") as output:
                    pickle.dump(item, output, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                print(f"⚠️ Error saving item {file_index}: {e}")
                continue


download_judgments(start_page=0, end_page=5163)

try:
    with open("orzeczenia/105894.json", "rb") as f:
        obj = pickle.load(f)
        print(obj)
except Exception as e:
    print(f"Failed to read as pickle: {e}")


#appending the contents of files to the list 
texts = []

for i in range(105894, 155894, 1): 
    filepath = f"orzeczenia/{i}.json"
    try:
        if os.path.getsize(filepath) == 0:
            print(f"File {i} is empty, skipping.")
            continue

        with open(filepath, "rb") as f:
            obj = pickle.load(f)
            texts.append(obj)
            print(f"File {i} loaded: {type(obj)}")
    except Exception as e:
        print(f"File {i} failed: {e}")


with open('orzeczenia\texts.pkl', 'wb') as output:
    pickle.dump(texts, output, pickle.HIGHEST_PROTOCOL)

def try_get(x, key):
    try:
        return str(x.get(key, ''))
    except:
        return ''


texts_series = pd.Series(texts)

courtTypes = texts_series.map(lambda x: try_get(x, 'courtType'))
caseNumbers = texts_series.apply(lambda x: x['courtCases'][0]['caseNumber'] if x['courtCases'] else None)
judgmentTypes = texts_series.map(lambda x: try_get(x, 'judgmentType'))
textContents = texts_series.map(lambda x: try_get(x, 'textContent'))
judgmentDates = texts_series.map(lambda x: try_get(x, 'judgmentDate'))
publicationDates = texts_series.map(lambda x: try_get(x.get('source', {}), 'publicationDate'))
judgesNames = texts_series.apply(lambda x: x['judges'][0]['name'] if x['judges'] else None)

#creating a dataframe
data = pd.DataFrame({'courtType': courtTypes, 'caseNumber': caseNumbers, 'judgmentType': judgmentTypes, 'textContent': textContents, 'publicationDate': publicationDates, 'judgmentDate': judgmentDates, 'judgesName': judgesNames})

def clean_text(text):

    text = re.sub('\n', ' ', text)

    text = re.sub(r'[0-9]+', '', text)

    text = re.sub(r"[,\!?/:;''()``’“-”—#]", '', text)

    text = re.sub(r"([.]+)", '', text)

    text = text.lower()

    text = re.sub(r'\b\d+([./-]\d+)*\b', '', text)

    roman_pattern = r'\b(m{0,3}(c[md]|d?c{0,3})(x[cl]|l?x{0,3})(i[xv]|v?i{0,3})?)\b'
    text = re.sub(roman_pattern, '', text)

    text = re.sub(r'\s+', ' ', text).strip()
    return text

data['textContent']=data['textContent'].apply(clean_text)

#saving the df
data.to_csv("data.csv")

