import pymysql
import pandas as pd

def run_query(command):
    conn = pymysql.connect(host="bridge-tracker-test-20240528.cbdc52orwtsz.us-east-1.rds.amazonaws.com",
                        user="rds_tracker1",
                        password="hUyaMs9C4m3fEz84",
                        port=3306,
                        db="bridge_tracker")

    sql_query = command
    df = pd.read_sql_query(sql_query, conn)
    conn.close()
    return df

def get_input_info():
    input_info = """
    SELECT MIN(blockID) as blockid, name
    FROM block
    WHERE organizationID IN (20076, 20707, 17385, 16980, 210, 199, 279, 24000, 21000)
    GROUP BY name, organizationID;
    """
    return run_query(input_info)


def get_block_exercises(block_df):
    blockid_list = block_df["blockid"].tolist()
    blockid_list = ",".join(map(str, blockid_list))

    exercise_query = f"""
    SELECT bs.blockID, ei.exercise, bs.reps
    FROM blockset bs
    JOIN (
        SELECT exerciseID, MIN(name) as exercise
        FROM exerciseinfo 
        WHERE OrganizationID=1
        GROUP BY exerciseID
    ) ei ON bs.exerciseID = ei.exerciseID
    WHERE bs.blockID IN ({blockid_list})
    ORDER BY bs.blockID, bs.sequence;
    """
    r = run_query(exercise_query).rename(columns={"blockID": "blockid"})
    r["reps"] = r["reps"].fillna(0)
    r["reps"] = r["reps"].astype(int)
    return r