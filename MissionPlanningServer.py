# Mission Planning Web Server
# 
# This Solves the Travelling Salesman Problem (TSP) through the use of Genetic Algorithms
# The Weights dictionary holds different user preferences for route Fuel/Distance, Track CPA, Track Speed and Track Suspicion
# So that the user can influence the genetic Algorithm Fitness Function, and held the GA generated Routes
# 
# ========================================================================
from flask import Flask, render_template, request,jsonify,json
from flask_cors import CORS
import random, math, copy
import numpy as np 
import pandas as pd
import collections
import Track
from threading import Timer
import requests
import json
import operator
# ==================================================================
# Main Constants
BASELAT = 49.
BASELONG= -5.5

BESTDISTANCE = 0
BESTCPA = 1
BESTSPEED = 2
BESTSUSPICION   = 3
BESTBALANCED = 4

# =========================================================================
app = Flask(__name__)
#
# Note Need to enbale CORS for calls from Java Script Http Requests apparently
# pip install -U flask-cors
# 
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# ====================================================================
TrackList = []
TrackCoordinatesList = []
RouteListResponse =[]
CoordTrackIDLookup = []				# A List to reconnect Hash Coordinates => Track Id (Table)
TheCurrentOptimiser = BESTDISTANCE
WeightDict = { 
    "BestDistanceFitness": 1.0,
    "BestCPAFitness": 1.0,
    "BestSpeedFitness": 1.0,
    "BestSuspicionFitness": 1.0,
    "FuelWeight" : 0.25,
    "CPAWeight" : 0.25,
    "SpeedWeight" : 0.25,
    "SuspicionWeight" : 0.25
    }

# ===================================================================
class TrackCoord:
    def __init__(self, x, y,TheTrackId):
        self.x = x
        self.y = y
        self.TrackId = TheTrackId

    def distance(self, contact):
        xDis = abs(self.x - contact.x)
        yDis = abs(self.y - contact.y)
        distance = np.sqrt((xDis ** 2) + (yDis ** 2))
        return distance
    
    def __repr__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"
# =====================================================================================
class Fitness:
    def __init__(self, route):
        self.route = route
        #self.distance = 0
        self.fitness= 0.0
    # ==========================
   
    # ====================================
    # Fitness based upon Inverse Accumulated Distance
    def AccInvRouteDistance(self):
        accdistance = 0.0
        for i in range(0, len(self.route)):
            fromContact = self.route[i]
            toContact = None
            if i + 1 < len(self.route):
                toContact = self.route[i + 1]
            else:
                toContact = self.route[0]
            accdistance = accdistance+ fromContact.distance(toContact)
                
        if(self.fitness == 0):
            self.fitness = 100.0/accdistance
        return self.fitness      
    # ====================================
    # Fitness based upon Inverse Accumulated CPA
    def AccInvRouteCPA(self):
        accInvCPA = 0.0
        for i in range(0, len(self.route)):
            # Avoid Accumluating Own Ship
            if(self.route[i].TrackId>0):
                accInvCPA = accInvCPA + 1000.0/(TrackList[self.route[i].TrackId].CPA*(i+1))
                
        if(self.fitness == 0):
            self.fitness = accInvCPA
        return self.fitness
    # ====================================
    # Fitness based upon  Accumulated Speeds
    def AccRouteSpeed(self):
        accspeed = 0.0
        for i in range(0, len(self.route)):
            # Avoid Accumluating Own Ship
            if(self.route[i].TrackId>0):
                accspeed = accspeed + TrackList[self.route[i].TrackId].Speed/(i+1)
                
        if(self.fitness == 0):
            self.fitness = accspeed
        return self.fitness
    # ====================================

    # Fitness based upon Weighted Accumulated Suspicion
    def AccRouteSuspicion(self):
        accsuspicion = 0.0
        for i in range(0, len(self.route)):
            # Avoid Accumluating Own Ship
            if(self.route[i].TrackId>0):
                accsuspicion = accsuspicion + TrackList[self.route[i].TrackId].Suspicion/(i+1)
                
        if(self.fitness == 0):
            self.fitness = accsuspicion
        return self.fitness
# =====================================================================================
def createRoute(CoordinateList):
    route = random.sample(CoordinateList, len(CoordinateList))
    return route
# =====================================================================================
def initialPopulation(popSize, CoordinateList):
    population = []

    for i in range(0, popSize):
        population.append(createRoute(CoordinateList))
    return population
# =====================================================================================
def rankRoutes(population,CurrentOptimiser):
    fitnessResults = {}
    for i in range(0,len(population)):
        if(CurrentOptimiser==BESTDISTANCE):
            fitnessResults[i] = Fitness(population[i]).AccInvRouteDistance()
        if(CurrentOptimiser==BESTCPA):
            fitnessResults[i] = Fitness(population[i]).AccInvRouteCPA()
        if(CurrentOptimiser==BESTSPEED):
            fitnessResults[i] = Fitness(population[i]).AccRouteSpeed()
        if(CurrentOptimiser==BESTSUSPICION):
            fitnessResults[i] = Fitness(population[i]).AccRouteSuspicion()
        if(CurrentOptimiser==BESTBALANCED):
            # The Weighted Fitness = SUM(Weight * Fitness/BestFitness) over all weight features
            BalFuelFitness =  WeightDict["FuelWeight"]*Fitness(population[i]).AccInvRouteDistance()/WeightDict["BestDistanceFitness"]
            BalCPAFitness = WeightDict["CPAWeight"]*Fitness(population[i]).AccInvRouteCPA()/WeightDict["BestCPAFitness"]
            BalSpeedFitness = WeightDict["SpeedWeight"]*Fitness(population[i]).AccRouteSpeed()/WeightDict["BestSpeedFitness"]
            BalSuspicionFitness =  WeightDict["SuspicionWeight"]*Fitness(population[i]).AccRouteSuspicion()/WeightDict["BestSuspicionFitness"]
            
            fitnessResults[i] = BalFuelFitness + BalCPAFitness + BalSpeedFitness  + BalSuspicionFitness

            # Need to debug why CPA is being disadvanategd in the balance
           ## if(i==0):
           ##     print("[DEBUG CPA ]: balanced Fitness values ", BalFuelFitness, BalCPAFitness, BalSpeedFitness, BalSuspicionFitness)

    # Note fitnessResults is a long dict type  with {0: fitness0, 1:fitness1, 2:fitness2 ... 49:fitness49}
    
    rankedresults = sorted(fitnessResults.items(), key = operator.itemgetter(1), reverse = True)
    # rankedresults is a pop sized List  type [ consisting of a list of (popindex,fitness)]  sorted with highest fitness firts 
    # [(popbestindex, bestfitness), (nextpopbestindex, nextbestfitness), ...... (popworstindex, worstfitness)]
    # Bigger Higher Fitness first

    return rankedresults
# =====================================================================================
def selection(popRanked, eliteSize):
    selectionResults = []
    df = pd.DataFrame(np.array(popRanked), columns=["Index","Fitness"])
    df['cum_sum'] = df.Fitness.cumsum()
    df['cum_perc'] = 100*df.cum_sum/df.Fitness.sum()
    
    for i in range(0, eliteSize):
        selectionResults.append(popRanked[i][0])
    for i in range(0, len(popRanked) - eliteSize):
        pick = 100*random.random()
        for i in range(0, len(popRanked)):
            if pick <= df.iat[i,3]:
                selectionResults.append(popRanked[i][0])
                break
    return selectionResults
# =====================================================================================
def matingPool(population, selectionResults):
    matingpool = []
    for i in range(0, len(selectionResults)):
        index = selectionResults[i]
        matingpool.append(population[index])
    return matingpool
# =====================================================================================
def breed(parent1, parent2):
    child = []
    childP1 = []
    childP2 = []
    
    geneA = int(random.random() * len(parent1))
    geneB = int(random.random() * len(parent1))
    
    startGene = min(geneA, geneB)
    endGene = max(geneA, geneB)

    for i in range(startGene, endGene):
        childP1.append(parent1[i])
        
    childP2 = [item for item in parent2 if item not in childP1]

    child = childP1 + childP2
    return child
# =====================================================================================
def breedPopulation(matingpool, eliteSize):
    children = []
    length = len(matingpool) - eliteSize
    pool = random.sample(matingpool, len(matingpool))

    for i in range(0,eliteSize):
        children.append(matingpool[i])
    
    for i in range(0, length):
        child = breed(pool[i], pool[len(matingpool)-i-1])
        children.append(child)
    return children
# =====================================================================================
def mutate(individual, mutationRate):
    for swapped in range(len(individual)):
        if(random.random() < mutationRate):
            swapWith = int(random.random() * len(individual))
            
            Contact1 = individual[swapped]
            Contact2 = individual[swapWith]
            
            individual[swapped] = Contact2
            individual[swapWith] = Contact1
    return individual
# =====================================================================================
def mutatePopulation(population, mutationRate):
    mutatedPop = []
    
    for ind in range(0, len(population)):
        mutatedInd = mutate(population[ind], mutationRate)
        mutatedPop.append(mutatedInd)
    return mutatedPop
# =====================================================================================
def nextGeneration(currentGen, eliteSize, mutationRate,CurrentOptimiser):
    popRanked = rankRoutes(currentGen,CurrentOptimiser)
    selectionResults = selection(popRanked, eliteSize)
    matingpool = matingPool(currentGen, selectionResults)
    children = breedPopulation(matingpool, eliteSize)
    nextGeneration = mutatePopulation(children, mutationRate)
    return nextGeneration
# =====================================================================================
def geneticAlgorithm(population, popSize, eliteSize, mutationRate, generations,CurrentOptimiser):
    pop = initialPopulation(popSize, population)
    #print("Initial distance: " + str(1 / rankRoutes(pop)[0][1]))
    
    for i in range(0, generations):
        pop = nextGeneration(pop, eliteSize, mutationRate,CurrentOptimiser)
    
    #print("Final distance: " + str(1 / rankRoutes(pop)[0][1]))   # Grabs the best ranked population[0], and then [1] is then the corresponding fitness value (1/distance)
    bestRouteIndex = rankRoutes(pop,CurrentOptimiser)[0][0]     # Grab the bext ranked population [0], and then the RouteIndex [0] of the 
    bestRoute = pop[bestRouteIndex]   # An orderred List Sequence of city/contact coordinates[(firstX,firstY), (secondX,secondY)...] 
    return bestRoute
# =====================================================================================

# ====================================================================
def LatLongToXY(Lat,Long): 
	Xcoord = (Long-BASELONG) * 100.0
	Ycoord = (Lat-BASELAT) * 150.0
	return Xcoord,Ycoord

def XYToLatLong(Xvalue,Yvalue): 
    LongValue = Xvalue*0.01 + BASELONG
    LatValue = Yvalue*0.00666 + BASELAT
    return LatValue,LongValue
# ===================================================================
@app.route("/")
def hello():
    return "Hello: This the Mission Planning Server  !"
# ====================================================================
def RouteByTrackIdSequence(RawCoordinateSequence):
    # Rotate the Route Coordinats into a Track Id order

    TrackIDSequence = []
    # The GA Algorith Return is a List of TrackCoord Types
    for RouteCoordinateItem in RawCoordinateSequence:
        # Use each RouteCoordinateItem to find the Corresponding Id, and Hence Track Number
        TrackIndex = RouteCoordinateItem.TrackId
        TrackIDSequence.append(TrackIndex)
            
    # Now Roll the Sequence to start at Index 0 using Numpy
    NPSequence = np.array(TrackIDSequence)
    ZeroIndex =  np.where(NPSequence==0)[0]
    RolledNPSequence = np.roll(NPSequence,-ZeroIndex) 
    SortedTrackIDSequence = RolledNPSequence.tolist()
    return SortedTrackIDSequence
# ========================================================
def SortDistanceRoute(TrackIDSequence):
    global TrackList,TrackCoordinatesList
    RtnCoordinatesList = []
    #print("[INFO]: TrackIdSequence into SortDistanceRoute", TrackIDSequence)
    for aTrackID in TrackIDSequence:
        atrackitem =  TrackList[aTrackID]   
        NewCoordinate= TrackCoord(x=atrackitem.Xpos, y=atrackitem.Ypos,TheTrackId =atrackitem.OriginalTrackID)		    
        RtnCoordinatesList.append(NewCoordinate)
        #print("INFO] Track Ids By Distance order: ", atrackitem.OriginalTrackID)

    return RtnCoordinatesList
# ===============================================================================
def RouteToTNJsonSequence(RawCoordinateSequence):
    global TrackList
    TrackIDSequence = []
    TNJSonSequence = []
    for RouteCoordinateItem in RawCoordinateSequence:
        TrackIndex = RouteCoordinateItem.TrackId
        TrackIDSequence.append(TrackIndex)

    # Now Roll the Sequence to start at Index 0 using Numpy
    NPSequence = np.array(TrackIDSequence)
    ZeroIndex =  np.where(NPSequence==0)[0]
    RolledNPSequence = np.roll(NPSequence,-ZeroIndex) 
    SortedTrackIDSequence = RolledNPSequence.tolist()

    for TrackId in SortedTrackIDSequence:
        TNJSonSequence.append({"TN":TrackList[TrackId].TN})

    return TNJSonSequence
# ================================================================================
def BestRouteBySpeed():
    global TrackList,TrackCoordinatesList
    RtnCoordinatesList = []
    
    RtnCoordinatesList.append(TrackCoordinatesList[0])

    SortedTracks = sorted(TrackList, key=lambda atrack:atrack.Speed, reverse = True)

    for atrackitem in SortedTracks:
        if(atrackitem.OriginalTrackID >0):
            NewCoordinate = TrackCoord(x=atrackitem.Xpos, y=atrackitem.Ypos,TheTrackId =atrackitem.OriginalTrackID)		    
            RtnCoordinatesList.append(NewCoordinate)
            #print("INFO] Track Ids By Speed order: ", atrackitem.OriginalTrackID)

    return RtnCoordinatesList
# ===============================================================================
def BestRouteByCPA():
    global TrackList,TrackCoordinatesList
    RtnCoordinatesList = []
    RtnCoordinatesList.append(TrackCoordinatesList[0])

    SortedTracks = sorted(TrackList, key=lambda atrack:atrack.CPA)

    for atrackitem in SortedTracks:
        if(atrackitem.OriginalTrackID >0):
            NewCoordinate = TrackCoord(x=atrackitem.Xpos, y=atrackitem.Ypos,TheTrackId =atrackitem.OriginalTrackID)		    
            RtnCoordinatesList.append(NewCoordinate)
            #print("INFO] Track Ids By CPA order: ", atrackitem.OriginalTrackID)

    return RtnCoordinatesList
# ===============================================================================
def BestRouteBySuspicion():
    global TrackList,TrackCoordinatesList
    RtnCoordinatesList = []
    RtnCoordinatesList.append(TrackCoordinatesList[0])

    SortedTracks = sorted(TrackList, key=lambda atrack:atrack.Suspicion, reverse = True)

    for atrackitem in SortedTracks:
        if(atrackitem.OriginalTrackID >0):
            NewCoordinate = TrackCoord(x=atrackitem.Xpos, y=atrackitem.Ypos,TheTrackId =atrackitem.OriginalTrackID)		    
            RtnCoordinatesList.append(NewCoordinate)
            #print("INFO] Track Ids By Suspicion order: ", atrackitem.OriginalTrackID)

    return RtnCoordinatesList
# ===============================================================================
def CalculateAllScores(RouteToCalaculate):
    rtnOverallScore = 0
    rtnFuelScore = 0
    rtnCPAScore = 0
    rtnSpeedScore = 0
    rtnSuspicionScore = 0

    rtnFuelScore = 100.0* Fitness(RouteToCalaculate).AccInvRouteDistance()/ WeightDict["BestDistanceFitness"]
    rtnCPAScore = 100.0* Fitness(RouteToCalaculate).AccInvRouteCPA()/ WeightDict["BestCPAFitness"]
    rtnSpeedScore = 100.0* Fitness(RouteToCalaculate).AccRouteSpeed()/ WeightDict["BestSpeedFitness"]
    rtnSuspicionScore = 100.0* Fitness(RouteToCalaculate).AccRouteSuspicion()/ WeightDict["BestSuspicionFitness"]

    rtnOverallScore = WeightDict["FuelWeight"]*rtnFuelScore + WeightDict["CPAWeight"]*rtnCPAScore + WeightDict["SpeedWeight"]*rtnSpeedScore + WeightDict["SuspicionWeight"]*rtnSuspicionScore 

    return rtnOverallScore,rtnFuelScore, rtnCPAScore, rtnSpeedScore, rtnSuspicionScore
# ===============================================================================
# Web Service End Point Process : Update the Weights
@app.route("/UpdateWeights",methods=['POST'])
def Process_UpdateWeigths():   
    print()
    req_data = request.get_json()
    print(" [INFO]: User Update Weights : Req_data", req_data)

    JWeights = req_data['userweights']  
    WeightDict["FuelWeight"] = JWeights["fuelweight"]/100.0
    WeightDict["CPAWeight"] = JWeights["cpaweight"]/100.0
    WeightDict["SpeedWeight"] = JWeights["speedweight"]/100.0
    WeightDict["SuspicionWeight"] = JWeights["suspicionweight"]/100.0
    
    return jsonify({'result':'success'})
# ==============================================================================
# NEW  Web Service Process a Request Route Request 3 - Only Porcesses Nominated Tracks
@app.route("/RequestRoute3",methods=['POST'])
def Process_RequestRoute3():
    global TrackList, TrackCoordinatesList
    print()
    req_data = request.get_json()
    print(" [INFO]: Routes Requested: Req_data", req_data)

    # Capture and Update the User Weights:
    JWeights = req_data['userweights']  

    # Set insignificant weights to Zero to avoid any influence 
    if(JWeights["fuelweight"] < 2):
        JWeights["fuelweight"] = 0.0
    if(JWeights["cpaweight"] < 2):
        JWeights["cpaweight"] = 0.0
    if(JWeights["speedweight"] < 2):
        JWeights["speedweight"] = 0.0
    if(JWeights["suspicionweight"] < 2):
        JWeights["suspicionweight"] = 0.0

    WeightDict["FuelWeight"] = JWeights["fuelweight"]/100.0
    WeightDict["CPAWeight"] = JWeights["cpaweight"]/100.0
    WeightDict["SpeedWeight"] = JWeights["speedweight"]/100.0
    WeightDict["SuspicionWeight"] = JWeights["suspicionweight"]/100.0

    # Capture those Tracks in the AOI TN List from the Request
    TracksInAOI = req_data['tracksinaoi']

    # QUERY Tactical Picture: Tracks GET Web Service  
    TPurl = 'http://127.0.0.1:8080/TracksXY'    # Tactical Picture
    Response = requests.get(TPurl)			# Feed json web request with top level JSON element : 'coordinates' 
        
    if Response.status_code != 200:
        print(" [ERROR] Track Request Error : " + str(Response.status_code))
        return jsonify({'result':'No Targets Exist', 'routelist':[]})
    else:
        # Have Got a Return - So now Process
        JsonResponse = Response.json()
        # Fill Out the TrackList  from the json 'tracks' list
        JTrackList = JsonResponse['tracks']
        TrackList = []
        TrackCoordinatesList = []
        JTrackIndex = 0

        for JTrackItem in JTrackList:
            #  Now Only Process those Track Numbers that are either in the received AOI Nominated list or are deemed Nominated and including Own Ship Track Index 0
            if((JTrackItem['TN'] in TracksInAOI) or (JTrackItem['Nominated']) or (JTrackIndex==0)):
                NewTrack = Track.Track(JTrackIndex,JTrackItem['TN'], JTrackItem['XPos'], JTrackItem['YPos'], JTrackItem['XVel'],JTrackItem['YVel'], JTrackItem['Suspicion'])
                TrackList.append(NewTrack)

                #print(" Check:", NewTrack.TN, " Suspicion: ",  NewTrack.Suspicion, " CPA: ", NewTrack.CPA, " ThreatDistance: ",NewTrack.Distance)
                NewCoordinate = TrackCoord(x=JTrackItem['XPos'], y=JTrackItem['YPos'],TheTrackId =JTrackIndex)		
                TrackCoordinatesList.append(NewCoordinate)
                JTrackIndex = JTrackIndex+1
        # ==========================================
        if(JTrackIndex<2):
            print("[ERROR] Not Enough Nominated Tracks for Route: ")
            return jsonify({'result':'ERROR No Nominated Tracks', 'routelist':[]})
        if(JTrackIndex>10):
            print("[ERROR] Excessive Number of Nominated Tracks: ",JTrackIndex)
            return jsonify({'result':'ERROR Excessive Number of Nominated Tracks', 'routelist':[]})
        # ========================================================
        # Main Route Generation Processing
        # Run GA Algorithm : Capture the Sole Best Distance Route
        BestDistanceRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTDISTANCE)
        ## Sort into Track id Sequence 
        SortedTrackIDBestDistanceRoute = RouteByTrackIdSequence(BestDistanceRoute)
        SortedDistanceRoute = SortDistanceRoute(SortedTrackIDBestDistanceRoute)

        # Capture the Best Distance Fitness
        WeightDict.update({"BestDistanceFitness": Fitness(SortedDistanceRoute).AccInvRouteDistance()})

        # Capture the Best Speed Route and Fitness
        BestSpeedRoute = BestRouteBySpeed() 
        WeightDict.update({"BestSpeedFitness": Fitness(BestSpeedRoute).AccRouteSpeed()})

        # Capture the Best CPA Route and Fitness
        BestCPARoute = BestRouteByCPA() 
        WeightDict.update({"BestCPAFitness": Fitness(BestCPARoute).AccInvRouteCPA()})

        # Capture the Best Suspicion Route and Fitness
        BestSuspicionRoute = BestRouteBySuspicion() 
        WeightDict.update({"BestSuspicionFitness": Fitness(BestSuspicionRoute).AccRouteSuspicion()})

        print()
        print("[INFO]: Revised WeightDict: ", WeightDict)
        # ========================================
        # Now Start Filling in a Route Table List   - Note this Rank HAS NOT yet been Sorted by OverallScore
        # Just the top 5: Balanced Route(user Preferences), Best Fuel, CPA, Speed and Suspicion for now  
        #
        RouteListResponse =[]
        #
        # First Item Route - will be a Balanced Route - Using Userr Weighted Preferences  
        BalancedRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTBALANCED)
        SortedTrackIDBalancedRoute = RouteByTrackIdSequence(BalancedRoute)
        SortedBalancedRoute = SortDistanceRoute(SortedTrackIDBalancedRoute)

        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedBalancedRoute)
        RouteItem = {'rank': 1, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedBalancedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Second Route Row: Best Distance Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedDistanceRoute)
        RouteItem = {'rank': 2, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedDistanceRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Third Route Row: Best CPA Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestCPARoute)
        RouteItem = {'rank': 3, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestCPARoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fourth Route Row: Best Speed Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSpeedRoute)
        RouteItem = {'rank': 4, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSpeedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fith Route Row: Best Suspicion Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSuspicionRoute)
        RouteItem = {'rank': 5, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSuspicionRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        '''
        # There Seems to be a Problem with the Balanced CPA - So Lets just check GA calculated CPA as a 6th Ranke Item Route
        BalancedCPARoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTCPA)
        SortedCPARouteID = RouteByTrackIdSequence(BalancedCPARoute)
        SortedCPARoute = SortDistanceRoute(SortedCPARouteID)

        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedCPARoute)
        RouteItem = {'rank': 6, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedCPARoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)
        '''
        # ===========================================================
        #  Now Send the Json Fied Route Table Response
        print()
        print("[INFO]:  The Route Table Response: ")
        print(RouteListResponse)

        return jsonify({'result':'Success','routetable':RouteListResponse})
# ======================================================================
# DEPRECIATED Route Request Web Service (v2 Includes User Weights)
@app.route("/RequestRoute2",methods=['POST'])
def Process_RequestRoute2():
    global TrackList, TrackCoordinatesList
    print()
    req_data = request.get_json()
    print(" [INFO]: Routes Requested: Req_data", req_data)

    # Capture and Update the User Weights:
    JWeights = req_data['userweights']  
    WeightDict["FuelWeight"] = JWeights["fuelweight"]/100.0
    WeightDict["CPAWeight"] = JWeights["cpaweight"]/100.0
    WeightDict["SpeedWeight"] = JWeights["speedweight"]/100.0
    WeightDict["SuspicionWeight"] = JWeights["suspicionweight"]/100.0

    # QUERY Tactical Picture: Tracks GET Web Service  
    TPurl = 'http://127.0.0.1:8080/TracksXY'    # Tactical Picture
    Response = requests.get(TPurl)			# Feed json web request with top level JSON element : 'coordinates' 
        
    if Response.status_code != 200:
        print(" [ERROR] Track Request Error : " + str(Response.status_code))
        return jsonify({'result':'No Targets Exist', 'routelist':[]})
    else:
        # Have Got a Return - So now Process
        JsonResponse = Response.json()
        # Fill Out the TrackList  from the json 'tracks' list
        JTrackList = JsonResponse['tracks']
        TrackList = []
        TrackCoordinatesList = []
        JTrackIndex = 0

        for JTrackItem in JTrackList:
        
            NewTrack = Track.Track(JTrackIndex,JTrackItem['TN'], JTrackItem['XPos'], JTrackItem['YPos'], JTrackItem['XVel'],JTrackItem['YVel'], JTrackItem['Suspicion'],JTrackItem['Identity'])
            TrackList.append(NewTrack)

            #print(" Check:", NewTrack.TN, " Suspicion: ",  NewTrack.Suspicion, " CPA: ", NewTrack.CPA, " ThreatDistance: ",NewTrack.Distance)
            NewCoordinate = TrackCoord(x=JTrackItem['XPos'], y=JTrackItem['YPos'],TheTrackId =JTrackIndex)		
            TrackCoordinatesList.append(NewCoordinate)
            JTrackIndex = JTrackIndex+1
        # ==========================================
        # TO DO Read User Criteria for Score Weightings

        # Run GA Algorithm : Capture the Sole Best Distance Route
        BestDistanceRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTDISTANCE)
        ## Sort into Track id Sequence 
        SortedTrackIDBestDistanceRoute = RouteByTrackIdSequence(BestDistanceRoute)
        SortedDistanceRoute = SortDistanceRoute(SortedTrackIDBestDistanceRoute)

        # Capture the Best Distance Fitness
        WeightDict.update({"BestDistanceFitness": Fitness(SortedDistanceRoute).AccInvRouteDistance()})

        # Capture the Best Speed Route and Fitness
        BestSpeedRoute = BestRouteBySpeed() 
        WeightDict.update({"BestSpeedFitness": Fitness(BestSpeedRoute).AccRouteSpeed()})

        # Capture the Best CPA Route and Fitness
        BestCPARoute = BestRouteByCPA() 
        WeightDict.update({"BestCPAFitness": Fitness(BestCPARoute).AccInvRouteCPA()})

        # Capture the Best Suspicion Route and Fitness
        BestSuspicionRoute = BestRouteBySuspicion() 
        WeightDict.update({"BestSuspicionFitness": Fitness(BestSuspicionRoute).AccRouteSuspicion()})

        print()
        print("[INFO]: WeightDict: ", WeightDict)
        # ========================================
        # Now Start Filling in a Route Table List   - Note Rank is Not Sorted by OverallScore
        #  
        # Perhaps Rank Order No Overall by a Default User Criteria Weights [1.0,0.0,0.0,0.0] i.e. Distance
        # Just the top 4: Best Fuel, CPA, Speed and Suspicion  for now   - The Add User Weighted later
        #
        RouteListResponse =[]
        #

        # First Item Route - will be a Balanced Route - Using Weighted Preferences  
        BalancedRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTBALANCED)
        SortedTrackIDBalancedRoute = RouteByTrackIdSequence(BalancedRoute)
        SortedBalancedRoute = SortDistanceRoute(SortedTrackIDBalancedRoute)

        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedBalancedRoute)
        RouteItem = {'rank': 1, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedBalancedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Second Route Row: Best Distance Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedDistanceRoute)
        RouteItem = {'rank': 2, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedDistanceRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Third Route Row: Best CPA Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestCPARoute)
        RouteItem = {'rank': 3, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestCPARoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fourth Route Row: Best Speed Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSpeedRoute)
        RouteItem = {'rank': 4, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSpeedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fith Route Row: Best Suspicion Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSuspicionRoute)
        RouteItem = {'rank': 5, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSuspicionRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # ===========================================================
        #  Now Send the Json Fied Route Table Response
        print()
        print("[INFO]:  The Route Table Response: ")
        print(RouteListResponse)

        return jsonify({'result':'Success','routetable':RouteListResponse})
# ======================================================================
# DEPRECIATED Route Request Web Service
@app.route("/RequestRoute",methods=['POST'])
def Process_RequestRoute():
    global TrackList, TrackCoordinatesList
    print()
    req_data = request.get_json()
    print(" [INFO]: Routes Requested: Req_data", req_data)

    # QUERY Tactical Picture: Tracks GET Web Service  
    TPurl = 'http://127.0.0.1:8080/TracksXY'    # Tactical Picture
    Response = requests.get(TPurl)			# Feed json web request with top level JSON element : 'coordinates' 
        
    if Response.status_code != 200:
        print(" [ERROR] Track Request Error : " + str(Response.status_code))
        return jsonify({'result':'No Targets Exist', 'routelist':[]})
    else:
        # Have Got a Return - So now Process
        JsonResponse = Response.json()

        # Fill Out the TrackList  from the json 'tracks' list
        JTrackList = JsonResponse['tracks']
        TrackList = []
        TrackCoordinatesList = []
        JTrackIndex = 0

        for JTrackItem in JTrackList:
            NewTrack = Track.Track(JTrackIndex,JTrackItem['TN'], JTrackItem['XPos'], JTrackItem['YPos'], JTrackItem['XVel'],JTrackItem['YVel'], JTrackItem['Suspicion'])
            TrackList.append(NewTrack)

            #print(" Check:", NewTrack.TN, " Suspicion: ",  NewTrack.Suspicion, " CPA: ", NewTrack.CPA, " ThreatDistance: ",NewTrack.Distance)
            NewCoordinate = TrackCoord(x=JTrackItem['XPos'], y=JTrackItem['YPos'],TheTrackId =JTrackIndex)		
            TrackCoordinatesList.append(NewCoordinate)
            JTrackIndex = JTrackIndex+1
        # ==========================================
        # TO DO Read User Criteria for Score Weightings

        # Run GA Algorithm : Capture the Sole Best Distance Route
        BestDistanceRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTDISTANCE)
        ## Sort into Track id Sequence 
        SortedTrackIDBestDistanceRoute = RouteByTrackIdSequence(BestDistanceRoute)
        SortedDistanceRoute = SortDistanceRoute(SortedTrackIDBestDistanceRoute)

        # Capture the Best Distance Fitness
        WeightDict.update({"BestDistanceFitness": Fitness(SortedDistanceRoute).AccInvRouteDistance()})

        # Capture the Best Speed Route and Fitness
        BestSpeedRoute = BestRouteBySpeed() 
        WeightDict.update({"BestSpeedFitness": Fitness(BestSpeedRoute).AccRouteSpeed()})

        # Capture the Best CPA Route and Fitness
        BestCPARoute = BestRouteByCPA() 
        WeightDict.update({"BestCPAFitness": Fitness(BestCPARoute).AccInvRouteCPA()})

        # Capture the Best Suspicion Route and Fitness
        BestSuspicionRoute = BestRouteBySuspicion() 
        WeightDict.update({"BestSuspicionFitness": Fitness(BestSuspicionRoute).AccRouteSuspicion()})

        print()
        print("[INFO]: WeightDict: ", WeightDict)
        # ========================================
        # Now Start Filling in a Route Table List   - Note Rank is Not Sorted by OverallScore
        #  
        # Perhaps Rank Order No Overall by a Default User Criteria Weights [1.0,0.0,0.0,0.0] i.e. Distance
        # Just the top 4: Best Fuel, CPA, Speed and Suspicion  for now   - The Add User Weighted later
        #
        RouteListResponse =[]
        #

        # First Item Route - will be a Balanced Route - Using Weighted Preferences  
        BalancedRoute = geneticAlgorithm(population=TrackCoordinatesList, popSize=50, eliteSize=15, mutationRate=0.01, generations=100,CurrentOptimiser=BESTBALANCED)
        SortedTrackIDBalancedRoute = RouteByTrackIdSequence(BalancedRoute)
        SortedBalancedRoute = SortDistanceRoute(SortedTrackIDBalancedRoute)

        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedBalancedRoute)
        RouteItem = {'rank': 1, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedBalancedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Second Route Row: Best Distance Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(SortedDistanceRoute)
        RouteItem = {'rank': 2, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(SortedDistanceRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Third Route Row: Best CPA Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestCPARoute)
        RouteItem = {'rank': 3, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestCPARoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fourth Route Row: Best Speed Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSpeedRoute)
        RouteItem = {'rank': 4, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSpeedRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # Fith Route Row: Best Suspicion Route
        OverallScore,FuelScore,CPAScore,SpeedScore, SuspicionScore = CalculateAllScores(BestSuspicionRoute)
        RouteItem = {'rank': 5, 'overallscore':OverallScore,'route': RouteToTNJsonSequence(BestSuspicionRoute), 'fuelscore':FuelScore, 'CPAscore':CPAScore, 'speedscore':SpeedScore, 'suspicionscore':SuspicionScore}
        RouteListResponse.append(RouteItem)

        # ===========================================================
        #  Now Send the Json Fied Route Table Response
        print()
        print("[INFO]:  The Route Table Response: ")
        print(RouteListResponse)

        return jsonify({'result':'Success','routetable':RouteListResponse})
# ======================================================================
# Main method to Start the Web Server - avoids setting up Environment variables
if __name__ == "__main__":
	print(" [INFO]: ==================================== ")
	print(" [INFO]: Running the Mission Planning Web Server ")
	app.run(debug=True,port = 7070)			# Note set to Debug to avoid having to restart the python Web App Server upon changs