from Functions.DataBaseQueries import *
from Functions.DataSetManipulation import *

#----------- I- User Input -------------
#TOTAL : 20084, 481, 13528, 15356, 15686, 16006, 20085, 12186, 12242, 18380, 435, 943, 17542, 19770, 19767, 19087,19820,13275
#Used so far: 20084, 12186, 13528, 15356, 943, 435, 19767, 19770, 20085, 18380, 12242, 19087,17542,15686,16006
#NOTE: BELOW JUST REMOVE CURRENT ORGs AND WRITW NEW ORGS U WANT TO APPEND TO CURRENT DATASET
block_query = f"""
SELECT workoutID, blockid, name
FROM block
WHERE organizationID IN (15356, 943, 435, 19767, 19770, 20085, 18380, 12242, 19087,17542,15686,16006)
  AND workoutID > 0
ORDER BY sequence;
"""

block_df = run_query(block_query)
print("---")

grouped_block_df = block_df.groupby('workoutID').agg({
    'name': list,
    'blockid': list,
}).reset_index()

#----------- Get Exercises Relevant Info -------------
sample_blockid_array = (block_df['blockid'].tolist())
blockid_list = ','.join(map(str, sample_blockid_array))

param_list=["reps","time","distance"]
print("---")
exercise_df=get_blocks_workout(block_df,param_list) #FOR ALL PARAMS
print("---")
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


grouped_block_df = grouped_block_df.drop(columns=['blockid'])
print(grouped_block_df)
#CAREFUL NOT TO OVERWRITE EXISINT FILE< CHANGE DIRECTORY TO DATAi+1!!!!!!!!
grouped_block_df.to_csv('/Users/mn/Desktop/BridgeAthletics/Proj2/Proj2DataPreprocessing/Data2/IO_Workout_Sample.csv', index=False)



                                                                                                                              
