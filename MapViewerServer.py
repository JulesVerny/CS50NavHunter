# Python Web Server using Flask
from flask import Flask, render_template,request,redirect
app = Flask(__name__)
import mysql.connector
from mysql.connector import connect, Error
import os
# ===================================================================================

@app.route("/")
@app.route("/home")
def home():
    return render_template('NavMainPage.html')
# =======================================================================================
@app.route("/about")
def about():
    return render_template('about.html')
# =======================================================================================
@app.route("/scenarios")
def listscenarios():
    # Attempt a database Query on Scenarios Table
    try:
        scenariosfordisplay = []
        with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
            print("[INFO] A Scenarios List Query Request: ", connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, selected, base_lat, base_long FROM scenarios")
                for ascenarioquery in cursor:
                    scenariodisplayrow = {'id':ascenarioquery[0],'selected':ascenarioquery[1],'base_lat':ascenarioquery[2],'base_long':ascenarioquery[3] }
                    scenariosfordisplay.append(scenariodisplayrow)

        return render_template("scenariolist.html", scenariolist=scenariosfordisplay)      
    except Error as e:
        print()
        print("[ERROR  A Database Error Has Occured ]: ",e)
        print()

# /listscenarios() 
# =======================================================================================
@app.route("/selectscenario", methods=["POST"])
def selectscenario():

    # Select the Scenario
    SelectedScenarioID = request.form.get("selectedscenarioid")
    print("[INFO] Update Selected Scenario Request: ", SelectedScenarioID)
    if SelectedScenarioID:
        # Attempt a databaseUpdate On Scenarios Table
        try:
            scenariosfordisplay = []
            with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
               
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE scenarios SET selected = 0") 
                    connection.commit()   
                    print("[INFO] Setting the Requested Selection in Db: ")             
                    cursor.execute("""UPDATE scenarios SET selected = 1 WHERE id = %s""", (SelectedScenarioID,))    # Set the Selected Scenario
                    connection.commit()

                    # Now perform a General scenarios query to repopulate the Display
                    cursor.execute("SELECT id, selected, base_lat, base_long FROM scenarios")
                    for ascenarioquery in cursor:
                        scenariodisplayrow = {'id':ascenarioquery[0],'selected':ascenarioquery[1],'base_lat':ascenarioquery[2],'base_long':ascenarioquery[3] }
                        scenariosfordisplay.append(scenariodisplayrow)
            return render_template("scenariolist.html", scenariolist=scenariosfordisplay)      
        except Error as e:
            print()
            print("[ERROR  A Database Error Has Occured ]: ",e)
            print()
# =======================================================================================
@app.route("/displayscenarioevents", methods=["POST"])
def displayscenario():

    # Select the Scenario
    SelectedScenarioID = request.form.get("displayscenarioid")
    print("[INFO] A Display Scenario Details: ", SelectedScenarioID)
    if SelectedScenarioID:
        # Attempt to Query the Hunter_DB: scenarioevents 
        try:
            sesfordisplay = []
            wpsfordisplay = []
            with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
               
                with connection.cursor() as cursor:
                    # Scenario Events List:
                    cursor.execute("SELECT time, tn, event_type, suspicion, x_pos, y_pos, x_vel, y_vel FROM scenarioevents WHERE scenario_id=%s",(SelectedScenarioID,))
                    for asequery in cursor:
                        sedisplayrow = {'time':asequery[0],'tn':asequery[1],'event_type':asequery[2],'suspicion':asequery[3], 'x_pos':asequery[4], 'y_pos':asequery[5],'x_vel':asequery[6],'y_vel':asequery[7]}
                        sesfordisplay.append(sedisplayrow)

                    # Task Group Waypoints List
                    cursor.execute("SELECT wp_lat, wp_long FROM ctgwaypoints WHERE scenario_id=%s",(SelectedScenarioID,))
                    for asequery in cursor:
                        wpdisplayrow = {'wp_lat':asequery[0],'wp_long':asequery[1]}
                        wpsfordisplay.append(wpdisplayrow)
            return render_template("scenariodetails.html", scenarioID=SelectedScenarioID, scenariodetailslist=sesfordisplay, ctgwplist= wpsfordisplay)  

        except Error as e:
            print()
            print("[ERROR  A Database Error Has Occured ]: ",e)
            print()
# // displayscenario()
# ==========================================================================================
@app.route("/units")
def listunits():
    # Attempt a database Query on Units Table
    try:
        unitsfordisplay = []
        with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
            print("[INFO] A Units List Query Request: ", connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT tn, unit_type, hostility FROM units")  
                for aunitquery in cursor:
                    unitdisplayrow = {'tn':aunitquery[0],'unit_type':aunitquery[1],'hostility':aunitquery[2] }
                    unitsfordisplay.append(unitdisplayrow)

        return render_template("unitslist.html", unitlist=unitsfordisplay)      
    except Error as e:
        print()
        print("[ERROR  A Database Error Has Occured ]: ",e)
        print()

# /listunits() 
# =======================================================================================
if __name__ == "__main__":
    app.run(debug=True)			# Note set to Debug to avoid having to restart the python Web App Server upon changs