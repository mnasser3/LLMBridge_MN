from Functions.DataBaseQueries import *

def run_query(command):
    conn = pymysql.connect(host='bridge-tracker-test-20240528.cbdc52orwtsz.us-east-1.rds.amazonaws.com',
                        user='rds_tracker1',
                        password='hUyaMs9C4m3fEz84',
                        port=3306,
                        db='bridge_tracker')

    sql_query = command

    df = pd.read_sql_query(sql_query, conn)

    #df.to_csv('output.csv', index=False)
    conn.close()
    return df

#----------- I- User Input -------------
#----------- Get User Input Relevant Info (Workout note) -------------
command = """
SELECT MIN(workoutid) AS workoutid, note
FROM workout
WHERE note LIKE "%focusing%"
GROUP BY note LIMIT 3;
"""

workout_df=run_query(command)
print("\nInput Example:\n", workout_df)
#---------------------------------------

#----------- II- User Output -------------
#----------- Get Block Relevant Info -------------
sample_workoutid_array = workout_df['workoutid'].tolist()

workoutid_list = ','.join(map(str, sample_workoutid_array))

block_query = f"""
SELECT workoutID, blockID, name
FROM block
WHERE workoutID IN ({workoutid_list});
"""

block_df = run_query(block_query)

grouped_block_df = block_df.groupby('workoutID').agg({
    'blockID': list,
    'name': list
}).reset_index()

print("\nGrouped Block DataFrame:\n", grouped_block_df)


#----------- Get Exercises Relevant Info -------------
sample_blockid_array = (block_df['blockID'].tolist())
blockid_list = ','.join(map(str, sample_blockid_array))

exercise_query = f"""
SELECT blockID, exerciseID, reps
FROM blockset
WHERE blockID IN ({blockid_list});
"""
exercise_df = run_query(exercise_query)

grouped_ex_df = exercise_df.groupby('blockID').agg({
    'exerciseID': list,
    'reps': list
}).reset_index()

print("\nGrouped Exercise DataFrame:", grouped_ex_df, sep='\n')


#---------- Combine Output Info ------------
merged_df = pd.merge(block_df, grouped_ex_df, on='blockID', how='left')
merged_df = merged_df.drop(columns=["blockID"])

# Step 3: Group by workoutID and aggregate the data into a structured format
out_df = merged_df.groupby('workoutID').apply(
    lambda x: pd.Series({
        'blocks': x[['name', 'exerciseID', 'reps']].to_dict('records')
    })
).reset_index()



# Set pandas options to display full output
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)
print("\nOutput Example:\n")
print(out_df['blocks'][0])



#------Input/Output Table--------
out_df = out_df.rename(columns={'workoutID': 'workoutid'})

IO_merged_df = pd.merge(workout_df, out_df, on='workoutid').reset_index(drop=True)

# Set pandas options to display full output
pd.set_option('display.max_colwidth', 25)
pd.set_option('display.expand_frame_repr', True)

# Print the final merged dataframe
print("\nInput/Output Example:\n")
print(IO_merged_df)
# Save the DataFrame to a CSV file
IO_merged_df.to_csv('IO_Workout_Sample.csv', index=False)


                                                                                                                              
