from transformers import T5Tokenizer, LongT5ForConditionalGeneration
import torch
import json
import re
import ast
import GetWorkoutExercises

def model_fn(model_dir):
    model = LongT5ForConditionalGeneration.from_pretrained(model_dir)
    tokenizer = T5Tokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token

    if torch.cuda.is_available():
        device = torch.device("cuda")
        model.half().to(device)
        print("Using GPU:", torch.cuda.get_device_name(0))
    else:
        device = torch.device("cpu")
        model.to(device)
        print("Using CPU")

    model.eval()
    return model, tokenizer


def input_fn(request_body, request_content_type):
    if request_content_type == 'application/json':
        input_data = json.loads(request_body)
        return input_data['inputs']
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")
    

def predict_fn(input_data, model_and_tokenizer):
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
        
        instruction = f"### Instruction:\nGenerate a workout block in JSON format for the following block title."
        normalized_input = normalize_userinput(text)
        input_text = f"\n\n### Input:\n{normalized_input}"
        return instruction + input_text
    input_data= GetWorkoutExercises.get_main_workout_ex(input_data)
    input_text = format_model_input(input_data)
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)

    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids,
            eos_token_id=1,
            max_length=1200,
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
    stop_sequence = "### Response"
    stop_index = decoded_output.find(stop_sequence, decoded_output.find(stop_sequence) + len(stop_sequence))
    if stop_index != -1:
        output = decoded_output[:stop_index]
    else:
        output = decoded_output

    def str_to_list(generated):
        s = generated
        s = s.replace("</s>", "").strip()
        s = s.strip("<pad> ### Response: ")
    
        try:
            s = ast.literal_eval(s)
        except (ValueError, SyntaxError):  #POST PROCESSING
          last_bracket_index = s.rfind('}')
          if last_bracket_index != -1:
              s = s[:last_bracket_index + 1]
              s += ']}'
              try:
                  s=ast.literal_eval(s)
              except (ValueError, SyntaxError):
                  return -1
          if type(s) != dict:
            return -1
        else:
          return s
    
    def check_parameters_correctness(model_output_list, param_list=['reps','time','distance']):
        required_keys = {'exercise', 'sets'}
        for keys in model_output_list:
          for j, dictionary in enumerate(model_output_list[keys]):
            if not required_keys.issubset(dictionary.keys()):
                return -2
    
            allowed_keys = required_keys.union(param_list)
            if not set(dictionary.keys()).issubset(allowed_keys):
              return -3
        return 1
    
    def get_set_and_param_consistency(model_output_list,param_list=['reps','time','distance']):
      required_keys = {'exercise', 'sets'}
      for keys in model_output_list:
        for j in range(0,len(model_output_list[keys])):
          sets = model_output_list[keys][j]['sets']
          if sets == 0:
            return -1
          for param in param_list:
            if param in model_output_list[keys][j]:
              param_len = len(model_output_list[keys][j][param])
              if sets > param_len:
                last_value = model_output_list[keys][j][param][-1]
                model_output_list[keys][j][param].extend([last_value] * (sets - param_len))
              elif sets < param_len:
                model_output_list[keys][j][param] = model_output_list[keys][j][param][:sets]
      return model_output_list
    
    def remove_consecutive_duplicates(model_outputs_list):
      for key in model_outputs_list:
        j = 0
        while j < len(model_outputs_list[key]) - 1:
            if model_outputs_list[key][j]['exercise'] == model_outputs_list[key][j + 1]['exercise']:
                del model_outputs_list[key][j + 1]
            else:
                j += 1
      return model_outputs_list

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
    if response_content_type == 'application/json':
        return json.dumps({'prediction': prediction})
    else:
        raise ValueError(f"Unsupported content type: {response_content_type}")
