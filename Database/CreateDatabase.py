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
    ) as connection:
        print("The Database Connection: ", connection)
        
        # ===============================================
        # Create the "hunter_db" Database
        create_db_query = "CREATE DATABASE hunter_db"
        with connection.cursor() as cursor:
            cursor.execute(create_db_query)
            # Now Show All the Databases
            print("The Databases : ")
            show_db_query = "SHOW DATABASES"
            cursor.execute(show_db_query)
            for db in cursor:
                print(db)
        print(" =============== Complete ================== ")
except Error as e:
    print(e)
    
