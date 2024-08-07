import pandas as pd
import json
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, message="pandas only supports SQLAlchemy connectable")
warnings.filterwarnings("ignore", category=FutureWarning, message="Downcasting object dtype arrays on .fillna")

def exercises_params_to_list(ex_df, param_list):
    agg_dict = {"exercise": list}
    agg_dict.update({param: list for param in param_list})
    r = ex_df.groupby("blockid").agg(agg_dict).reset_index()
    return r

def combine_exercise_and_params(ex_df,param_list):
    def create_info_dict(row, param_list):
        return {param: row[param] for param in param_list}

    r = ex_df.groupby("blockid").apply(
        lambda x: pd.Series({
            "info": [
                {"exercise": row["exercise"], **create_info_dict(row, param_list)} 
                for _, row in x.iterrows()
            ]
        })
    ).reset_index()
    return r

def add_sets_for_param_col(exercise_list,param_list):
    result = []
    current_exercise = None
    current_set = 0
    current_params = {param: [] for param in param_list}
    for item in exercise_list:
        if item["exercise"] == current_exercise:
            for param in param_list:
                current_params[param].append(item[param])
            current_set +=1
        else:
            if current_exercise is not None:
                result.append({
                    "exercise": current_exercise,
                    "sets": current_set,
                    **current_params
                })
            current_exercise = item["exercise"]
            current_params = {param: [item[param]] for param in param_list}
            current_set = 1  

    if current_exercise is not None:
        result.append({
            "exercise": current_exercise,
            "sets": current_set,
            **current_params
        })
    return result

def add_sets_for_output_df(out_df,param_list):
    out_df["info"]=out_df["info"].apply(lambda exercise_list: add_sets_for_param_col(exercise_list, param_list))
    return out_df

def merge_IO(I,O):
    r = pd.merge(I, O, on="blockid").reset_index(drop=True)
    r = r.drop(columns=['blockid'])
    return r

def add_IO_labels(df):
    return df.apply(lambda row: {'input': row['name'], 'output': row['info']}, axis=1)

def json_format(df):
    return df.to_json(orient='records')

def json_save(j,filename):
    data = json.loads(j)  
    with open(filename, 'w') as f:
        json.dump(data, f, indent=1)

def json_read(filename):
    with open(filename, "r") as file:
        json_data = json.load(file)
    return json_data


def remove_zero_params(exercise_list, param_list):
    result = []
    for exercise in exercise_list:
        filtered_exercise = {k: v for k, v in exercise.items()}
        for param in param_list:
            if param in filtered_exercise and not any(filtered_exercise[param]):
                del filtered_exercise[param]

        result.append(filtered_exercise)
    return result

def clean_params(json_out, param_list):
    for i in range (len(json_out)):
        json_out[i]['output']=remove_zero_params(json_out[i]['output'],param_list)
    return json_out
