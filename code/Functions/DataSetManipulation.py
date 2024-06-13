import pandas as pd

def exercises_reps_to_list(ex_df):
    r = ex_df.groupby('blockid').agg({
        'exercise': list,
        'reps': list
    }).reset_index()
    return r

def combine_exercise_and_rep(ex_df):
    r = ex_df.groupby('blockid').apply(
        lambda x: pd.Series({
            'info': [{'exercise': ex, 'reps': rep} for ex, rep in zip(x['exercise'], x['reps'])]
        })
    ).reset_index()
    return r

def add_sets_for_param_col(exercise_list, reps_only=True):
    result = []
    current_exercise = None
    current_set = 0

    if reps_only == True:
        current_reps = []
        for item in exercise_list:
            if item['exercise'] == current_exercise:
                current_reps.append(item['reps'])
                current_set +=1
            else:
                if current_exercise is not None:
                    result.append({'exercise': current_exercise, 'sets': current_set, 'reps': current_reps})
                current_exercise = item['exercise']
                current_reps = [item['reps']]
                current_set = 1  
        if current_exercise is not None:
            result.append({'exercise': current_exercise, 'sets': current_set, 'reps': current_reps})
    # else:
    #     # TO FILL FOR ALL PARAMS

    return result

def add_sets_for_output_df(out_df):
    out_df['info']=out_df['info'].apply(add_sets_for_param_col)
    return out_df

def merge_IO(I,O):
    return pd.merge(I, O, on='blockid').reset_index(drop=True)


