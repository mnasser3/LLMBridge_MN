import pymysql
import pandas as pd

def run_query(command):
    conn = pymysql.connect(host="ENTER INFO HERE",
                        user="ENTER INFO HERE",
                        password="ENTER INFO HERE",
                        port="ENTER INFO HERE",
                        db="ENTER INFO HERE")

    sql_query = command
    df = pd.read_sql_query(sql_query, conn)
    conn.close()
    return df

def get_input_info():
    #Dataset1: 20076, 20707, 17385, 16980, 210, 199, 279, 24000, 21000
    #Dataset2: 20084,481,13528,15356,15686,16006,20085,12186,18380,435,943,17542, 19770, 19767, 19087,19820,13275
    input_info = """
    SELECT MIN(blockID) as blockid, name
    FROM block
    WHERE organizationID IN (20084, 481, 13528, 15356, 15686, 16006, 20085, 12186, 12242, 18380, 435, 943, 17542, 19770, 19767, 19087,19820,13275)
    GROUP BY name, organizationID;
    """
    return run_query(input_info)


def get_block_exercises_reps(block_df):
    blockid_list = block_df["blockid"].tolist()
    blockid_list = ",".join(map(str, blockid_list))

    exercise_query = f"""
    SELECT bs.blockID, ei.exercise, bs.reps
    FROM blockset bs
    JOIN (
        SELECT exerciseID, MIN(name) as exercise
        FROM exerciseinfo 
        WHERE OrganizationID = (
            SELECT MIN(OrganizationID)
            FROM exerciseinfo ei2
            WHERE ei2.exerciseID = exerciseinfo.exerciseID AND OrganizationID > 1
        )
        GROUP BY exerciseID
    ) ei ON bs.exerciseID = ei.exerciseID
    WHERE bs.blockID IN ({blockid_list})
    ORDER BY bs.blockID, bs.sequence;
    """
    r = run_query(exercise_query).rename(columns={"blockID": "blockid"})
    r["reps"] = r["reps"].fillna(0)
    r["reps"] = r["reps"].astype(int)
    return r

def get_block_exercises_params(block_df,param_list):
    blockid_list = block_df["blockid"].tolist()
    blockid_list = ",".join(map(str, blockid_list))

    selec_command_line = "SELECT bs.blockID, ei.exercise,"
    for i in param_list: 
        selec_command_line=selec_command_line+"bs."+i+"," 
    selec_command_line=selec_command_line[:len(selec_command_line)-1]  
    exercise_query = f"""
    {selec_command_line}
    FROM blockset bs
    JOIN (
        SELECT exerciseID, MIN(name) as exercise
        FROM exerciseinfo 
        WHERE OrganizationID = (
            SELECT MIN(OrganizationID)
            FROM exerciseinfo ei2
            WHERE ei2.exerciseID = exerciseinfo.exerciseID AND OrganizationID > 1
        )
        GROUP BY exerciseID
    ) ei ON bs.exerciseID = ei.exerciseID
    WHERE bs.blockID IN ({blockid_list})
    ORDER BY bs.blockID, bs.sequence;
    """
    r = run_query(exercise_query).rename(columns={"blockID": "blockid"})

    for param in param_list:
        r[param] = r[param].fillna(0)
        r[param] = r[param].astype(int)
    return r
from tqdm import tqdm
def get_blocks_workout(block_df, param_list):
    blockid_list = block_df["blockid"].tolist()
    batch_size = 1500  # Adjust the batch size according to your needs
    results = []

    # Process data in batches with a progress bar
    for i in tqdm(range(0, len(blockid_list), batch_size), desc="Processing batches"):
        batch_ids = blockid_list[i:i+batch_size]
        batch_ids_str = ",".join(map(str, batch_ids))

        # Create SELECT statement dynamically
        select_command_line = "SELECT bs.blockID, ei.exercise, exercise.exerciseType,"
        for param in param_list: 
            select_command_line += f"bs.{param},"
        select_command_line = select_command_line.rstrip(",")

        # Optimized query for batch
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

        # Execute the query and retrieve the results for the current batch
        batch_result = run_query(exercise_query).rename(columns={"blockID": "blockid"})

        # Fill NaN values and convert to int
        for param in param_list:
            batch_result[param] = batch_result[param].fillna(0).astype(int)
        
        results.append(batch_result)

    # Combine all batch results into a single DataFrame
    final_result = pd.concat(results, ignore_index=True)
    return final_result
