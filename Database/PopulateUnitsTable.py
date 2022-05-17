#  To Test and manipulate the loacl MySQL database
# 
import mysql.connector
from getpass import getpass
from mysql.connector import connect, Error
import pandas as pd
import os

# ============================================================
# Read the Units File into a Pandas Data famne
print("[INFO] Loading Units File: ") 
UnitsDataFrame = pd.read_csv("units.csv")
#
print(UnitsDataFrame)
NumberOfUnits = len(UnitsDataFrame.index)
print("[INFO] Number of Units Loaded: ", NumberOfUnits)

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
        
            
     
        create_ctg_waypoints_query = """
        CREATE TABLE ctgwaypoints(
        id INT AUTO_INCREMENT PRIMARY KEY,
        scenario_id INT,
        wp_lat FLOAT,
        wp_long FLOAT,
        FOREIGN KEY(scenario_id) REFERENCES scenarios(id))
        """      
        
        with connection.cursor() as cursor:
            # Now perfom the Table Creation SQL Queries: 
            #print("Creating the Scenarios Table: ", create_scenarios_table_query )
            #cursor.execute(create_scenarios_table_query)
           
            # Iterate through the Dataframe Rows
            for index, row in UnitsDataFrame.iterrows():
                print("Attempting to Insert Row: ", row['tn'], row['type'], row['hostility'])
           
                # Compile an SQL Statement  - Note multiple python parametrs must be enclosed as a single Tuple parameter
                cursor.execute("INSERT INTO units (tn,unit_type,hostility) VALUES (%s,%s,%s);",(row['tn'], row['type'], row['hostility']))

            connection.commit()
       
        
       
        print(" =============== Complete ================== ")
except Error as e:
    print(e)
    
