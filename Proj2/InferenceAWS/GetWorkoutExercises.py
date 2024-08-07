import pandas as pd
from sqlalchemy import create_engine
import pymysql
import json
import ast

def run_query(command):
    engine = create_engine('mysql+pymysql://rds_tracker1:hUyaMs9C4m3fEz84@bridge-tracker-test-20240528.cbdc52orwtsz.us-east-1.rds.amazonaws.com:3306/bridge_tracker')
    with engine.connect() as connection:
        df = pd.read_sql_query(command, connection)
    return df

def run_block_query(workoutID):
    block_query = f"""
    SELECT workoutID, blockid, name
    FROM block
    WHERE workoutID = {workoutID}
    ORDER BY sequence;
    """
    return run_query(block_query)

def get_blocks_workout(block_df, param_list):
    blockid_list = block_df["blockid"].tolist()
    if not blockid_list:
        return pd.DataFrame()  
    batch_ids_str = ",".join(map(str, blockid_list))
    select_command_line = "SELECT bs.blockID, ei.exercise, exercise.exerciseType,"
    for param in param_list: 
        select_command_line += f"bs.{param},"
    select_command_line = select_command_line.rstrip(",")
    exercise_query = f"""
    WITH min_org AS (
        SELECT exerciseID, MIN(OrganizationID) as min_org_id
        FROM exerciseinfo
        WHERE OrganizationID > 1
        GROUP BY exerciseID
    ),
    filtered_exerciseinfo AS (
        SELECT ei.exerciseID, ei.name as exercise
        FROM exerciseinfo ei
        JOIN min_org mo ON ei.exerciseID = mo.exerciseID AND ei.OrganizationID = mo.min_org_id
    )
    {select_command_line}
    FROM blockset bs
    JOIN filtered_exerciseinfo ei ON bs.exerciseID = ei.exerciseID
    JOIN exercise ON ei.exerciseID = exercise.exerciseID
    WHERE bs.blockID IN ({batch_ids_str})
    ORDER BY bs.blockID, bs.sequence;
    """
    result = run_query(exercise_query).rename(columns={"blockID": "blockid"})
    for param in param_list:
        result[param] = result[param].fillna(0).astype(int)
    return result

def combine_exercise_and_params(ex_df, param_list):
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
    
def extract_main_set_exercises(main_info):
    exercises = set()
    for block in main_info:
        for exo in block:
            if exo['exerciseType'][0].lower() == 'main set':
                exercises.add(exo['exercise'])
    return list(exercises)

def get_main_workout_ex(workoutID):
    block_df = run_block_query(workoutID)
    param_list=["reps","time","distance"]
    exercise_df=get_blocks_workout(block_df,param_list)
    param_list.append("exerciseType")
    out_df = combine_exercise_and_params(exercise_df,param_list)
    out_df = add_sets_for_output_df(out_df,param_list)
    df1_exploded = block_df
    merged_df = df1_exploded.merge(out_df, on='blockid', how='left')
    grouped_block_df = merged_df.groupby('workoutID').agg({
        'name': list,
        'blockid': list,
        'info': list
    }).reset_index()
    df = grouped_block_df.drop(columns=['blockid'])
    
    #remove warmups and recoveries
    for index, row in df.iterrows():
        for i in range(len(row['name'])-1,-1,-1):
            if 'warm' in row['name'][i].lower() or 'prep' in row['name'][i].lower() or 'recovery' in row['name'][i].lower() or 'regeneration' in row['name'][i].lower() or 'core' in row['name'][i].lower() or 'auxiliary' in row['name'][i].lower():
                df.at[index, 'name'].pop(i)
                df.at[index,'info'].pop(i)
    
    df['input'] = None
    df.at[0, 'input'] = extract_main_set_exercises(df.loc[0, 'info'])
    df.drop(columns=['name','info'])
    return str(df['input'][0])[1:-1]