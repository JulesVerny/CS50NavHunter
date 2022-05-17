#  To Test and manipulate the loacl MySQL database
# 
import mysql.connector
from getpass import getpass
from mysql.connector import connect, Error
import pandas as pd
import os

# ============================================================
# Read the Scenario File into a Pandas Data famne

ScenarioID=input("Please Enter a Scenario ID: "),
print("[INFO] Loading a Scenario Events File: ") 
SEDataFrame = pd.read_csv("scenarioevents1.csv")
#
print(SEDataFrame)
NumberOfSE = len(SEDataFrame.index)
print("[INFO] Number of Scenario Events Loaded: ", NumberOfSE)

# ============================================================================
# Now attempt to commit list into the Database
try:
    with connect(
        host="localhost",
        user= os.getenv('DB_USER'),           # input("Enter username: "),
        password=os.getenv('DB_PASSWORD'),    # getpass("Enter password: "),
        database="hunter_db",
    ) as connection:
        print("The Database Connection: ", connection)
        print()
        # ===============================================
        with connection.cursor() as cursor:
            # Now perfom the Table Row Insertions SQL Queries: 
           
            # Iterate through the Dataframe Rows
            for index, row in SEDataFrame.iterrows():
                print("Attempting to Insert Row: ", row['tn'], row['eventtype'], row['suspicion'])
           
                # Compile an SQL Statement  - Note multiple python parametrs must be enclosed as a single Tuple parameter
                cursor.execute("INSERT INTO scenarioevents (scenario_id,time,tn,event_type,suspicion,x_pos,y_pos,x_vel,y_vel) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);",(row['scenarioid'], row['time'], row['tn'],row['eventtype'], row['suspicion'], row['xpos'], row['ypos'], row['xvel'], row['yvel']))

            connection.commit()
       
        
       
        print(" =============== Complete ================== ")
except Error as e:
    print(e)
    
