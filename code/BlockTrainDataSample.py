from Functions.DataSetManipulation import *
from Functions.DataBaseQueries import *

#----------- I- User Input -------------
#----------- Get User Input Relevant Info (Block note) -------------

block_df=get_input_info()
print("\nInput Example:\n", block_df)

#----------- Get User Input Query from Block Name ----------------
inputs=block_df
#---------------------------------------

#----------- II- User Output -------------
#----------- Get Block Exercises Relevant Info -------------

exercise_df=get_block_exercises(block_df)

print("\nExercise DF:", exercise_df, sep='\n')
exercise_list_df = exercises_reps_to_list(exercise_df)
print("\nExercise and Reps List DataFrame:", exercise_list_df, sep='\n')

#---------- Format Output Info ------------
out_df = combine_exercise_and_rep(exercise_df)
out_df = add_sets_for_output_df(out_df)

pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)
print("\nOutput Example:\n")
print((out_df['info'][0][0]))


#------Input/Output Information pairs--------
IO_merged_df = merge_IO(block_df,out_df)

pd.set_option('display.max_colwidth', 25)
pd.set_option('display.expand_frame_repr', True)
print("\nInput/Output Example:\n")
print(IO_merged_df)

# Save the DataFrame to a CSV file
IO_merged_df.to_csv('IO_Block_Sample.csv', index=False)

#------Input/Output to JSON--------
IO_format_df = add_IO_labels(IO_merged_df)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)
print("\nIO Format:\n",IO_format_df)
IO_format_json = json_format(IO_format_df)
json_save(IO_format_json,'dataset.json')





                                                                                                                              
