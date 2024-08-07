from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import json
import re
import ast
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def model_fn(model_dir):
    try:
        logger.info(f"Loading model from {model_dir}")
        model = T5ForConditionalGeneration.from_pretrained(model_dir)
        logger.info("Model loaded successfully")
        
        logger.info(f"Loading tokenizer from {model_dir}")
        tokenizer = T5Tokenizer.from_pretrained(model_dir)
        tokenizer.pad_token = tokenizer.eos_token
        logger.info("Tokenizer loaded successfully")
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
            model.half().to(device)
            logger.info("Using GPU: %s", torch.cuda.get_device_name(0))
        else:
            device = torch.device("cpu")
            model.to(device)
            logger.info("Using CPU")
        
        model.eval()
        return model, tokenizer
    
    except Exception as e:
        logger.error(f"Error loading model or tokenizer: {str(e)}")
        raise

def input_fn(request_body, request_content_type):
    print("Processing input")
    if request_content_type == 'application/json':
        input_data = json.loads(request_body)
        return input_data['inputs']
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model_and_tokenizer):
    print("Generating prediction")
    model, tokenizer = model_and_tokenizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def format_model_input(text):
        def normalize_userinput(text):
            text = text.lower()
            text = re.sub(r'[:/\\.]', ',', text)
            text = re.sub(r'\-', '', text)
            text = re.sub(r'\+', 'and', text)
            text = re.sub(r'\&', 'and', text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\s*,\s*', ', ', text)
            if ((text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"'))):
                text = text[1:-1]
            return text
        
        instruction = "### Instruction:\nGenerate a workout block in JSON format for the following block title."
        normalized_input = normalize_userinput(text)
        input_text = f"\n\n### Input:\n{normalized_input}"
        return instruction + input_text
    
    input_text = format_model_input(input_data)
    print("Formatted input:", input_text)
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)

    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids,
            eos_token_id=1,
            max_length=400,
            num_beams=2,
            num_return_sequences=1,
            early_stopping=True,
            repetition_penalty=3.0,
            do_sample=True,
            top_k=9,
            top_p=0.93,
            temperature=1.2,
        )

    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
    print("Decoded output:", decoded_output)
    stop_sequence = "### Response"
    stop_index = decoded_output.find(stop_sequence, decoded_output.find(stop_sequence) + len(stop_sequence))
    if stop_index != -1:
        output = decoded_output[:stop_index]
    else:
        output = decoded_output

    def str_to_list(generated):
        s = generated
        s = s.replace("</s>", "").strip()
        s = s.strip("<pad>")
        s = s.strip(" ### Response: ")
        try:
            s = ast.literal_eval(s)
        except (ValueError, SyntaxError):  # POST PROCESSING
            last_bracket_index = s.rfind('}')
            if last_bracket_index != -1:
                s = s[:last_bracket_index + 1]
                s += ']'
                try:
                    s = ast.literal_eval(s)
                except (ValueError, SyntaxError):
                    return -1
        if type(s) != list or not all(isinstance(item, dict) for item in s):
            return -1
        else:
            return s

    def check_parameters_correctness(model_output_list, param_list=['reps','time','distance']):
        required_keys = {'exercise', 'sets'}
        for dictionary in model_output_list:
            if not required_keys.issubset(dictionary.keys()):
                return -2
            allowed_keys = required_keys.union(param_list)
            if not set(dictionary.keys()).issubset(allowed_keys):
                return -3
        return 1

    def get_set_and_param_consistency(model_output_list, param_list=['reps','time','distance']):
        required_keys = {'exercise', 'sets'}
        for d in range(len(model_output_list)):
            sets = model_output_list[d]['sets']
            if sets == 0:
                return -1
            for param in param_list:
                if param in model_output_list[d]:
                    param_len = len(model_output_list[d][param])
                    if sets > param_len:
                        last_value = model_output_list[d][param][-1]
                        model_output_list[d][param].extend([last_value] * (sets - param_len))
                    elif sets < param_len:
                        model_output_list[d][param] = model_output_list[d][param][:sets]
        return model_output_list

    def remove_consecutive_duplicates(model_outputs_list):
        cleaned_output = []
        for j in range(len(model_outputs_list)):
            if j == 0 or model_outputs_list[j]['exercise'] != model_outputs_list[j-1]['exercise']:
                cleaned_output.append(model_outputs_list[j])
        return cleaned_output

    output_list = str_to_list(output)
    if output_list == -1:
        return "Error in output"

    if check_parameters_correctness(output_list) != 1:
        return "Error in output"

    output_list = get_set_and_param_consistency(output_list)
    if output_list == -1:
        return "Error in output"

    output_list = remove_consecutive_duplicates(output_list)

    return output_list

def output_fn(prediction, response_content_type):
    print("Processing output")
    if response_content_type == 'application/json':
        return json.dumps({'prediction': prediction})
    else:
        raise ValueError(f"Unsupported content type: {response_content_type}")
