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
       
        print(" =============== Complete ================== ")
except Error as e:
    print(e)
    
