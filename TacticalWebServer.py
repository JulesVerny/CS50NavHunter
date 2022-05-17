# =====================================================================================================================
# This is a Tactical Picture Web Server to generate Unknown Surface Tracks, as a consequence of reading a ScenarioFile.csv
# This server runs a Periodic Timer, to read a scenario file, process Track Creations, and updates their positions
# This is in lieu of a form Track Query Service
# 
# This Web Server offer Track Queries for Mission Route Planning and LPD Displays
# The Scenario can be paused, restaretd and Stopped
# This Web Server also offers an emulation of a Helo Surveillance vehicle, which hovers ober, and identifes the Track, setting the 
# Identity of each Track to Known
#
# Track Upadtes are done in rough X,Y coordinates with Track XVel and YVel, Only very rough Lat/Long to XY conversions are provided 
# =====================================================================================================================
from flask import Flask, render_template, request,jsonify,json
from flask_cors import CORS
import random, math, copy
import numpy as np 
import pandas as pd
import collections
import Track
from threading import Timer
import mysql.connector
from mysql.connector import connect, Error
import os
# ==================================================================
# Main Constants
TOTALSIMTIME = 600
SCENARIOWAITING = 0
SCENARIORUNNING =1
SCENARIOPAUSED = 2
HELOSPEED = 20
SURVEILLANCEDWELLTIME = 5

HELOWAITING = 0
HELOTRAVERSING = 1
HELOSENSING = 2

# ======================================================================
# Main Variables
TrackList = []
UnitsList = []
ScenarioStatus = SCENARIOWAITING
ScenarioTime = 0
#MissionStatus = 0
NumberOfTracks = 0
NextScenarioEvent = 0
MissionTNSequence = []
HeloX = 0.0
HeloY = 0.0
NextHeloMissionIndex = -1
NextHeloTrackIndex=-1
HeloMissionStatus = HELOWAITING
HeloDwellCount = 0
CurrentScenarioID = 0
TheBaseLat = 50.0
TheBaseLong = 0.0

# ============================================================================
def LatLongToXY(Lat,Long): 
	global TheBaseLat, TheBaseLong
	Xcoord = (Long-TheBaseLong) * 100.0
	Ycoord = (Lat-TheBaseLat) * 150.0
	return Xcoord,Ycoord

def XYToLatLong(Xvalue,Yvalue): 
	global TheBaseLat, TheBaseLong
	LongValue = Xvalue*0.01 + TheBaseLong
	LatValue = Yvalue*0.00666 + TheBaseLat
	return LatValue,LongValue
# =========================================================================
# MAIN Run Time
#
print("=====================================================================")
print(" [INFO]: The Tactical Server Started")
app = Flask(__name__)
#
# Need to enable CORS for calls from Java Script Http Requests apparently
# pip install -U flask-cors
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# ====================================================================
# ==========================================================================
# Read the Scenario From the Database into ScenarioDataFrame
def LoadScenario():
	global CurrentScenarioID, ScenarioDataFrame,NumberOfScenarioEvents, TheBaseLat, TheBaseLong
	print("[INFO] Reading The Scenario: ", CurrentScenarioID) 

	# ============================================
	# First Need to Ensure that a proper Scenario ID Exists (May Have Navigated into via another route)
	if(CurrentScenarioID == 0):
		try:
			with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
				with connection.cursor(buffered=True) as cursor:
					cursor.execute("SELECT id, base_lat, base_long FROM scenarios WHERE selected =1 LIMIT 1")			
					for aqueryresult in cursor:
					
						(CurrentScenarioID,BaseLat,BaseLong) = aqueryresult
						TheBaseLat = BaseLat
						TheBaseLong = BaseLong 	
		except Error as e:	
			print()
			print("[Database ERROR ]: ",e)
			print()
	#  Check That a Scenario ID has Ben Loaded
	# ==========================================
	# Now Read the Scenario Events File
	if(CurrentScenarioID != 0):
		try:
			with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
				with connection.cursor(buffered=True) as cursor:
					cursor.execute("SELECT time, tn, event_type, suspicion, x_pos, y_pos, x_vel, y_vel FROM scenarioevents WHERE scenario_id=%s",(CurrentScenarioID,))
					QueryAllRows = cursor.fetchall()
					ScenarioDataFrame = pd.DataFrame(QueryAllRows)
					print()
					print("[DEBUG]: raw scenario Data frame: Nbr Columns: ", len(ScenarioDataFrame.columns))
					print()
					print("Raw DataFrame: ")
					print(ScenarioDataFrame)
					print()
					# Now Need to rename nd recover the DataFrame Column Names, as these wer not loaded
					ScenarioDataFrame.columns = ['time','tn','event','suspicion','xpos','ypos','xvel','yvel']

		except Error as e:	
			print()
			print("[Database ERROR ]: ",e)
			print()
		# QueryScenarioID()

		print()
		print("[INFO] Have Loaded the following Scenario: ", CurrentScenarioID)
		print(ScenarioDataFrame)
		NumberOfScenarioEvents = len(ScenarioDataFrame.index)
		print("[INFO] Number of Scenario Events: ", NumberOfScenarioEvents)
		print()
	# ==========================================

# LoadScenario()
# ==========================================================================
def LoadUnits():
	global UnitsList
	UnitsList = []
	print("[INFO] Reading The Units: ") 
	try:
		with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
			with connection.cursor(buffered=True) as cursor:
				cursor.execute("SELECT tn, unit_type, hostility FROM units")  
				for aunitquery in cursor:
					unitdisplayrow = {'tn':aunitquery[0],'unit_type':aunitquery[1],'hostility':aunitquery[2] }
					UnitsList.append(unitdisplayrow)

	except Error as e:	
		print()
		print("[Database ERROR ]: ",e)
		print()
	# QueryScenarioID()

	print()
	print("[INFO] Have Loaded the followng Units Table: ")
	print(UnitsList)
# LoadUnits()
# ==============================================================================
def SetTrackIdentity(TheTrackID):
	global TrackList,UnitsList
	CorrectUnitIdentity = "UNKNOWN"

	for aunit in UnitsList:
		if (aunit['tn'] == TrackList[TheTrackID].TN):
			CorrectUnitIdentity = aunit['hostility'] + aunit['unit_type']

	TrackList[TheTrackID].IdentifyTrack(CorrectUnitIdentity)

	print("[INFO]: Updating Identity of TN: ",TrackList[TheTrackID].TN, " To A : ", TrackList[TheTrackID].Identity)
	print()

# SetTrackIdentity
# ===============================================================================
def FindTrackIdbyTN(TrackNumber):
	global TrackList
	RtnTrackId = -1
	for i in range (0,len(TrackList)):
		if(TrackList[i].TN == TrackNumber):
			RtnTrackId = i
	return RtnTrackId
# ==============================================================================
# Web Services Functions
@app.route("/")
def hello():
    return "Hello: This is The Tactical Server  !"
# ====================================================================
@app.route("/ScenarioInstruction",methods=['POST'])
def Process_ScenarioInstruction():
	global TrackList, ScenarioStatus, ScenarioTime, NumberOfTracks, NextScenarioEvent, ScenarioDataFrame,NumberOfScenarioEvents
	req_data = request.get_json()
	print("[INFO]: Scenario Instruction: ", req_data)
	instruction = req_data['sinstruction']      # 'start',  'pause', 'stop' 
	responsecode = 'requestfailure'

	if(instruction=='start'):
		TrackList = []

		# Reload the Scenairo from the Database  
		LoadScenario()
		NumberOfScenarioEvents = len(ScenarioDataFrame.index)	
		NextScenarioEvent = 0
		ScenarioTime = 0

		ScenarioStatus = SCENARIORUNNING
		# Start the Timer
		Timer(2, ScenarioTimeStep).start()
		print("[INFO]: Scenario Started ")
		responsecode = 'success'	
	if(instruction=='pause'):
		ScenarioStatus  = SCENARIOPAUSED
		print("[INFO]: Pausing the Scenario")
		responsecode = 'success'
	if(instruction=='restart'):
		print("[INFO]: Restarting  the Scenario")
		ScenarioStatus  = SCENARIORUNNING
		Timer(2, ScenarioTimeStep).start()
		responsecode = 'success'

	if(instruction=='stop'):
		print("[INFO] Stopping the Scenario")
		# Stop the Scenario	
		ScenarioStatus = SCENARIOWAITING
		# Clear down 
		TrackList = []
		NextScenarioEvent = 0
		ScenarioTime = 0
		responsecode = 'success'	

	return jsonify({'result':responsecode, 'currentstatus': ScenarioStatus})
# Process_ScenarioInstruction():
# ======================================================================
# Request Scenario Id
@app.route("/GetCurrentScenarioID",methods=['POST'])
def QueryScenarioID():
	global CurrentScenarioID, UnitsList, TheBaseLat, TheBaseLong

	# Use this as a prompt to Load the Units Table 
	LoadUnits()

	print("[INFO]: Current ScenarioQuery" )
	CurrentScenarioID = 0
	try:
		with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
			with connection.cursor(buffered=True) as cursor:
				cursor.execute("SELECT id, base_lat, base_long FROM scenarios WHERE selected =1 LIMIT 1")			
				for aqueryresult in cursor:
					#print("[DEBUG]: Query result: ", aqueryresult)
					(CurrentScenarioID,BaseLat,BaseLong) = aqueryresult
					TheBaseLat = BaseLat
					TheBaseLong = BaseLong 	

		return jsonify({'currentscenarioid':CurrentScenarioID, 'base_lat':BaseLat, 'base_long':BaseLong })	

	except Error as e:	
		print()
		print("[Database ERROR ]: ",e)
		print()

# QueryScenarioID():
# =======================================================================
@app.route("/LoadTaskGroupScenario",methods=['GET'])
def QueryCTGWayPoints():
	global CurrentScenarioID
	print("[INFO]: LoadTaskGroupScenario  Request" )
	
	# Use this as a prompt to Load the Units Table 
	LoadUnits()

	# And Now Load the Scenario Events
	LoadScenario()

	# Now Load and return a Display of the CTG Region 
	print("[INFO]: Query the CTG List" )
	try:
		ctgwaypointlist = []
		with connect(host="localhost", user= os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database="hunter_db",) as connection:
			with connection.cursor(buffered=True) as cursor:
				cursor.execute("SELECT wp_lat, wp_long FROM ctgwaypoints WHERE scenario_id=%s",(CurrentScenarioID,))
				for asequery in cursor:
					wprow = {'lat':asequery[0],'lng':asequery[1]}
					ctgwaypointlist.append(wprow)

		return jsonify({'ctwaypointslist':ctgwaypointlist})

	except Error as e:	
		print()
		print("[Database ERROR ]: ",e)
		print()
# QueryScenarioID()
# =======================================================================
# Start Scenario 
@app.route("/StartScenario",methods=['POST'])
def Process_Start_Scenario():
	global TrackList, ScenarioStatus, ScenarioTime, NumberOfTracks, NextScenarioEvent, ScenarioDataFrame,NextHeloMissionIndex,HeloMissionStatus
	TrackList = []
	HeloMissionStatus = HELOWAITING
	NextHeloMissionIndex = -1
	# Reload the Scenario File, to enable it to be Eidted
	LoadScenario()

	NextScenarioEvent = 0
	ScenarioTime = 0
	ScenarioStatus = SCENARIORUNNING
	print("[INFO]: Re Starting the Scenario" )
	Timer(2, ScenarioTimeStep).start()
	return jsonify({'status':'Success'})	
# Process_Start_Scenario():
# ======================================================================
@app.route("/StartHeloMission",methods=['POST'])
def Process_StartHeloMission():
	global MissionTNSequence, NextHeloMissionIndex,HeloMissionStatus,NextHeloTrackIndex,HeloX,HeloY
	responsecode = 'requestfailure'
	req_data = request.get_json()
	JRouteTNSequence = req_data['routetnsequence']
	MissionTNSequence = []    
	for JTN in JRouteTNSequence:
		MissionTNSequence.append(JTN['TN'])

	print("[INFO]:Helo Mission Request: TN Sequence: ", MissionTNSequence)

	# Find the Next Track to move towards
	if((len(MissionTNSequence) >1) and (HeloMissionStatus== HELOWAITING)):
		# Set the Helo Position to Own Ship : Track [0]	
		HeloX = TrackList[0].Xpos
		HeloY = TrackList[0].Ypos

		NextHeloMissionIndex = 1
		HeloMissionStatus = HELOTRAVERSING
		responsecode = 'success'

	return jsonify({'result':responsecode})
# Process_StartHeloMission():
# ======================================================================
@app.route("/NominateTrack",methods=['POST'])
def Process_NominateTrack():
	global TrackList
	responsecode = 'requestfailure'
	req_data = request.get_json()
	NominatedTNumber = int(req_data['tracknumber'])
	print("[INFO]: Track being Nominated: ", NominatedTNumber)	

	for i in range (0,len(TrackList)):
		if(TrackList[i].TN == NominatedTNumber):
			TrackList[i].SetNominated()
			responsecode = 'success'

	return jsonify({'result':responsecode})
# Process_NominateTrack():
# ======================================================================
@app.route("/UnNominateTrack",methods=['POST'])
def Process_UnNominateTrack():
	global TrackList
	responsecode = 'requestfailure'
	req_data = request.get_json()
	NominatedTNumber = int(req_data['tracknumber'])
	print("[INFO]: Track being De Nominated: ", NominatedTNumber)	

	for i in range (0,len(TrackList)):
		if(TrackList[i].TN == NominatedTNumber):
			TrackList[i].SetUnNominated()
			responsecode = 'success'

	return jsonify({'result':responsecode})
# Process_NominateTrack():
# ======================================================================
def ScenarioTimeStep():
	global TrackList, ScenarioStatus, ScenarioTime, NextScenarioEvent,NumberOfScenarioEvents,ScenarioDataFrame, MissionTNSequence,HeloMissionStatus,NextHeloMissionIndex,HeloX,HeloY,HeloDwellCount,UnitsList
	if(ScenarioStatus == SCENARIORUNNING):
	#  Perform Time Step Processing
		NextScenarioRow = ScenarioDataFrame.loc[NextScenarioEvent,:]
		if(ScenarioTime==int(NextScenarioRow['time'])):
			# Process the Scenario Event
			print("[INFO]: Scenario Time: ", ScenarioTime, " Processing a: ", NextScenarioRow["event"], " Event")
			# ========================================			
			if(NextScenarioRow["event"] == "CREATE"):
				NewTrack = Track.Track(0,int(NextScenarioRow["tn"]),float(NextScenarioRow["xpos"]), float(NextScenarioRow["ypos"]), float(NextScenarioRow["xvel"]),float(NextScenarioRow["yvel"]), int(NextScenarioRow["suspicion"]))
				TrackList.append(NewTrack)
				print("[INFO]: Scenario Time: ", ScenarioTime," Creating Track: ", NextScenarioRow["tn"])
							
			if(NextScenarioRow["event"] == "UPDATE"):	
				UpdatedTN = int(NextScenarioRow["tn"])
				# Find the Corresponding Track by TN
				for i in range (0,len(TrackList)):
					if(TrackList[i].TN == UpdatedTN):
						TrackList[i].UpdateTrack(float(NextScenarioRow["xvel"]),float(NextScenarioRow["yvel"]), int(NextScenarioRow["suspicion"]))
				
			if(NextScenarioRow["event"] == "DELETE"):	
				DeletedTN = int(NextScenarioRow["tn"])
				# Find the Corresponding Track by TN
				ItemToDelete = -1
				for i in range (0,len(TrackList)):
					if(TrackList[i].TN == DeletedTN):
						ItemToDelete = i			
				if(ItemToDelete>-1):
					del TrackList[ItemToDelete]
			# Now Move the Next Scenario Event forward
			if(NextScenarioEvent < NumberOfScenarioEvents-1):
				NextScenarioEvent = NextScenarioEvent+1
		# =================================================================================
		#  Now Update those Live Track Positions
		for TrackItem in TrackList:
			TrackItem.UpdatePosition()
		# ================================================================
		# Now Update the Helo Positions
		if((len(MissionTNSequence) >1) and (HeloMissionStatus== HELOTRAVERSING)):
			# Note We have to keep rechecking the next TN => Track Id, next X,Y, as the Track may get deleted anytime 

			NextTN = MissionTNSequence[NextHeloMissionIndex]
			NextTrackId = FindTrackIdbyTN(NextTN)
			HelVelX = 0.0
			HelVelY = 0.0
			if(NextTrackId>-1):
				# TN Still exists so set that Direction
				NextX = TrackList[NextTrackId].Xpos
				NextY = TrackList[NextTrackId].Ypos
				DeltaX = NextX - HeloX
				DeltaY = NextY - HeloY		
				Magnitude = math.sqrt(DeltaX*DeltaX + DeltaY*DeltaY)
		
				if(Magnitude>0.001):
					HelVelX = HELOSPEED*DeltaX/Magnitude
					HelVelY = HELOSPEED*DeltaY/Magnitude
				else:
					HelVelX = 0.0
					HelVelY = 0.0

				# Check if Reached that next Track
				if(Magnitude<5.0):
					HelVelX = 0.0
					HelVelY = 0.0
					if(NextTN == 0):
						# Reached Final Ship [0] Tracke Return
						HeloMissionStatus = HELOWAITING
						print("[INFO] Helo Has Returned to Ship (Mission Complete): ",HeloMissionStatus)
					else:
						HeloMissionStatus = HELOSENSING
						HeloDwellCount = SURVEILLANCEDWELLTIME
						print("[INFO] Helo started Surveillance at: ",NextTN)
			else:
				# TN Does Not exist so move onto next  (note the Final TN 0 should always exist !)
				NextHeloMissionIndex = NextHeloMissionIndex+1
				print("[INFO]: The Helo Could not find TN: ", NextTN, " So Moving On to: ",MissionTNSequence[NextHeloMissionIndex])
				
			# So Now Perform Helo Position Update if Still deemed to be Traversing		
			if(HeloMissionStatus== HELOTRAVERSING):
				# Update Helo Position 
				HeloX = HeloX + 0.2*HelVelX
				HeloY = HeloY + 0.2*HelVelY	
				
		if(HeloMissionStatus== HELOSENSING):
			HeloDwellCount = HeloDwellCount -1
			if(HeloDwellCount == 0):
				# Finished Surveiallnce so can now Set the Identity Observed
				NextTrackId = FindTrackIdbyTN(MissionTNSequence[NextHeloMissionIndex])
				
				SetTrackIdentity(NextTrackId)			# Sets the Track Correct Identity using the Units Table List
				
				NextHeloMissionIndex = NextHeloMissionIndex+1
				HeloMissionStatus = HELOTRAVERSING
				print("[INFO]: Helo Completed Surveillance now Moving on to: ",MissionTNSequence[NextHeloMissionIndex])

		# ===================================================================================
		ScenarioTime = ScenarioTime+1
		# Restart the next Interval - Period of every 2 seconds
		Timer(2, ScenarioTimeStep).start()
# ScenarioTimeStep()
# ===============================================================================
@app.route("/Tracks")
def Process_Get_Tracks():
	global TrackList, ScenarioTime
	responsetracklist = []
	for TrackItem in TrackList:
		TrackLat,TrackLong= XYToLatLong(TrackItem.Xpos,TrackItem.Ypos)
		resptrackitem = {"TN":TrackItem.TN, "Lat":TrackLat,"Long":TrackLong,"XVel": TrackItem.Xvel, "YVel": TrackItem.Yvel,"Suspicion":TrackItem.Suspicion, "Identity":TrackItem.Identity, "Nominated":TrackItem.Nominated}
		
		responsetracklist.append(resptrackitem)
	return jsonify({'tracks':responsetracklist, 'simtime':ScenarioTime})
# Process_Get_Tracks():
# ========================================================================
@app.route("/TracksXY")
def Process_Get_TracksXY():
	global TrackList
	responsetracklist = []
	for TrackItem in TrackList:
		resptrackitem = {"TN":TrackItem.TN, "XPos":TrackItem.Xpos,"YPos":TrackItem.Ypos,"XVel": TrackItem.Xvel, "YVel": TrackItem.Yvel,"Suspicion":TrackItem.Suspicion,"Identity":TrackItem.Identity,"Nominated":TrackItem.Nominated}
		responsetracklist.append(resptrackitem)
	return jsonify({'tracks':responsetracklist})
# ========================================================================
'''@app.route("/CTG")
def Process_Get_CTG():
	global MissionStatus,HeloLat,HeloLong,NextWaypoint,HeloSPEED, DippingPeriod, DippingCount, QNLZLatLong
	ScenarioDataFrame = pd.read_csv("Scenario.csv")
	NumberItems = len(ScenarioDataFrame.index)
	CTGLocations = []
	CTGLocations.clear()
	#MissionStatus = WAITING
	QNLZLatLong = {'Lat':-777.7, 'Long':-333.333}
	print(" CTG Requested: ")
	for ScenarioIndex in range(NumberItems):
		ScenarioRow = ScenarioDataFrame.loc[ScenarioIndex,:]
		if(ScenarioRow['Item'] == 'QNLZ'):
			QNLZLatLong = {'Lat': ScenarioRow['Lat'], 'Long':ScenarioRow['Long']} 
		if(ScenarioRow['Item'] == 'CTG'):
			CTGItem = {'lat': ScenarioRow['Lat'], 'lng':ScenarioRow['Long']} 
			CTGLocations.append(CTGItem)
		if(ScenarioRow['Item'] == 'Helo'):
			HeloSPEED = ScenarioRow['Speed']
			DippingPeriod = ScenarioRow['DipPeriod']
	print("QNLZ: ", QNLZLatLong, " CTG Polygon: ",CTGLocations)
	return jsonify({'qnlzlocation':QNLZLatLong,'ctglocations':CTGLocations})
# Process_Get_CTG():
'''
# ========================================================================
@app.route("/Helo")
def Process_Get_Helo():
	global HeloMissionStatus,HeloX,HeloY
	HeloLat,HeloLong = XYToLatLong(HeloX,HeloY)
	return jsonify({'helolat': HeloLat,'helolng':HeloLong,'helostatus': HeloMissionStatus})
# ====================================================================================
# Main method to Start the Web Server - avoids setting up Environment variables
if __name__ == "__main__":
	print(" [INFO]: ==================================== ")
	print(" [INFO]: Running the Tactical Picture  Web Server ")
	app.run(debug=True,port = 8080)			# Note set to Debug to avoid having to restart the python Web App Server upon changs