from Functions.DataSetManipulation import *
from Functions.DataBaseQueries import *

#----------- I- User Input -------------
#----------- Get User Input Relevant Info (Block note) -------------

block_df=get_input_info()
print("\nInput Example:\n", block_df['name'][0])

#----------- Get User Input Query from Block Name ----------------
inputs=block_df
#---------------------------------------

#----------- II- User Output -------------
#----------- Get Block Exercises Relevant Info -------------

#exercise_df=get_block_exercises_reps(block_df) #FOR REP PARAM ONLY
param_list=["reps","time","distance"]
exercise_df=get_block_exercises_params(block_df,param_list) #FOR ALL PARAMS

# print("\nExercise DF:", exercise_df, sep='\n')
exercise_list_df = exercises_params_to_list(exercise_df,param_list)
#print("\nExercise and Reps List DataFrame:", exercise_list_df, sep='\n')

#---------- Format Output Info ------------
out_df = combine_exercise_and_params(exercise_df,param_list)
out_df = add_sets_for_output_df(out_df,param_list)
# print("\nOutput Example:\n")
# print((out_df['info'][1]))
# print()
# print((out_df['info']))
# print()
# print((out_df))


#------Input/Output Information pairs--------
IO_merged_df = merge_IO(block_df,out_df)

# pd.set_option('display.max_colwidth', 25)
# pd.set_option('display.expand_frame_repr', True)
# print("\nInput/Output Example:\n")
# print(IO_merged_df)

# Save the DataFrame to a CSV file
IO_merged_df.to_csv('IO_Block_Sample.csv', index=False)

# #------Input/Output to JSON--------
filename='Dataset2_allparams/initialdataset.json'
IO_format_df = add_IO_labels(IO_merged_df)
# pd.set_option('display.max_colwidth', None)
# pd.set_option('display.expand_frame_repr', False)
# print("\nIO Format:\n",IO_format_df)
IO_format_json = json_format(IO_format_df)
json_save(IO_format_json,filename)
IO_format_json =  json_read(filename)

IO_format_json = clean_params(IO_format_json,param_list)
with open(filename, "w") as file:
    json.dump(IO_format_json, file, indent=1)






                





                                                                                                                              
