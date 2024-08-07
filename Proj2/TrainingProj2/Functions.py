import json
import re
from sklearn.model_selection import train_test_split

def download_data(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data

def remove_extra_quotes(data):
    for i in range (0,len(data)):
        text=data[i]["input"]  
        if ((text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"'))):
            data[i]["input"]=data[i]["input"][1:-1]
    return data

def normalize_userinput(text):
    text = text.lower()
    text = re.sub(r'[:/\\.]', ',', text)
    text = re.sub(r'\-', '', text)
    text = re.sub(r'\+', 'and', text)
    text = re.sub(r'\&', 'and', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*,\s*', ', ', text)
    return text

def format_model_input(item):
    instruction = (
        f"### Instruction:\nGenerate a workout block in JSON format for the following block title."
    )
    normalized_input = normalize_userinput(item['input']) if item["input"] else ""
    input_text = f"\n\n### Input:\n{normalized_input}" 

    return instruction + input_text

def train_test_val_split(data,train_per=0.85,test_per=0.1):
    train_val_data, test_data = train_test_split(data, test_size=test_per, random_state=42)
    val_per_adjusted = 1 - (train_per/(1-test_per))
    train_data, val_data = train_test_split(train_val_data, test_size=val_per_adjusted, random_state=42)
    return train_data,test_data,val_data