#  To Test and manipulate the loacl MySQL database
# 
import mysql.connector
from getpass import getpass
from mysql.connector import connect, Error

# ============================================================

try:
    with connect(
        host="localhost",
        user=input("Enter username: "),
        password=getpass("Enter password: "),
        database="hunter_db",
    ) as connection:
        print("The Database Connection: ", connection)
        
        # ===============================================
        # Create Some Tables in "hunter_db" Database
       
        create_scenarios_table_query = """
        CREATE TABLE scenarios(
        id INT AUTO_INCREMENT PRIMARY KEY,
        selected INT,
        base_lat FLOAT,
        base_long FLOAT)
        """
        create_units_table_query = """
        CREATE TABLE units(
        tn INT PRIMARY KEY,
        unit_type CHAR(10),
        hostility CHAR(1))
        """
        
        create_scenario_events_query = """
        CREATE TABLE scenarioevents(
        id INT AUTO_INCREMENT PRIMARY KEY,
        scenario_id INT,
        time INT,
        tn INT,
        event_type CHAR(6),
        suspicion INT,
        x_pos INT,
        y_pos INT,
        x_vel INT,
        y_vel INT,
        FOREIGN KEY(scenario_id) REFERENCES scenarios(id),
        FOREIGN KEY(tn) REFERENCES units(tn))
        """      
     
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
            print("Creating the Scenarios Table: ", create_scenarios_table_query )
            cursor.execute(create_scenarios_table_query)
            print("Creating the Units Table: ", create_units_table_query)
            #cursor.execute(create_units_table_query)
            print("Creating the Scenario Events Table: ", create_scenario_events_query)
            cursor.execute(create_scenario_events_query)
            print("Creating the CTG Waypoints Table: ", create_ctg_waypoints_query)
            cursor.execute(create_ctg_waypoints_query) 

            connection.commit()
       
        
       
        print(" =============== Complete ================== ")
except Error as e:
    print(e)
    
