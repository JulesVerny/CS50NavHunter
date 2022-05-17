//  =============================================================================
// Some very messy JavaScript Client siede code to exercise the SHARD Route Planning Demonstrator
//
// The Map display is based upon Google Maps, with many constructs and icons being palced upon the Google maps
// When the Scenario has been started, thsi will be populatd by Unonkwon Surgace Tracks, periodically queried from the Tactical Picture Server 
// Some Track Nomination controls to create an Area of Interest and or Nominate specific Tracks
// There are scenario Controls to Drive the Main Tactical Picteur processing, to Satrt, Pause, Resume amd Stop the Tactical Picture Updates
// An Set of Balanced Slider Controls, which enbales the User to Change route Preference. Weights. These are Balanced so the overall sum still to 100
// Then the Routes Request Controls.  These will formulate a Web Service call to the Mission Planning Server
// 
// A Route Table filled out, with 
// Rank 1: - This is the Balanced Route, with the User Preferences 
// Rank 2: - This is the route solely upon shortest distance/ Fuel
// Rank 3: - This is the route ordered solely upon closest CPA
// Rank 4: - This is the route ordered solely upon Fastest Tracks first
// Rank 5: - This is the route ordered solely upon most suspucious Tracks first
//
// There are controls to display teh Route on the Map, and then to Execute the Route. 
// Executing the Route, will issue a request to the Tactical Picture to emulate a Surveillance drone to inspect each Track along the route
// =================================================================================
var map;

var CTGAreaMapRegion;
var QNLZDisplay; 
var QNLZLat;
var QNLZLong;
var CTGLabelDisplay; 
var CTGDisplayed;

var BaseLat;
var BaseLong; 

var SimulationTime;

var AOIEditingInProgress;
var NominationsInProgress;
var AOIMapRegion;
var AOIWaypointsList; 
var AOIDisplayed; 

var TheDisplayUpdateTimer; 
var ScenarioStatus; 
const WAITING = 0
const RUNNING = 1
const PAUSED = 2
var TheSelectedScenarioID=0; 

var FuelSlider; 
var FuelSValueField; 
var CPASlider;
var CPASValueField;
var SpeedSlider;
var SpeedSValueField;
var SuspicionSlider;
var SuspicionSValueField;

var TrackIcons;
var TrackNumberLables;
var SuspectLables; 
var VelocityLeaders;
var TracksDisplayed;
var TrackList;
var NominationCircles; 

var RoutesTable; 
var NumberofRoutes;
var NumberofDisplayedRoutes; 
var RoutesWayPointTable;
var RouteTNSequenceTable; 
var RouteIndexBeingDisplayed;
var RouteDisplayed;
var DisplayedRoute;
var RouteInExecution; 

var HeloIcon;
var HeloLocation;
var HeloDisplayed; 
var HeloRoutePlan; 

/*  ============================================================================= */
/*  Note Have to use Ctrl F5  in Browser to force reload changes updated Java Script */
/* ========================================================================================== */
function initMap() 
{
  BaseLat = 50.0;
  BaseLong = -6.0; 
  SimulationTime = 0; 

  map = new google.maps.Map(document.getElementById("map"), 
  {
    center: { lat: BaseLat, lng: BaseLong },
    zoom: 8,
    mapTypeId: 'satellite'
  });
   
  ScenarioStatus = WAITING;
  RoutesTable = document.getElementById("routestable");
  NumberofRoutes = 0;
  NumberofDisplayedRoutes = 0;
  HeloDisplayed = false;
  RouteIndexBeingDisplayed = -1;
  AOIDisplayed = false; 

  AOIEditingInProgress = false;
  NominationsInProgress = false;
  NominationCircles = []; 
  // Add a Mouse Movement Lat Long Display
  google.maps.event.addListener(map, 'mousemove', function(event) {
    displayMapCoordinates(event.latLng)
  });

  google.maps.event.addListener(map, 'click', function(event) {
    mouseclickonmap(event.latLng)
  });

  // Set Up Slider Callbacks
  FuelSlider = document.getElementById("FuelSlider");
  FuelSValueField = document.getElementById("FuelSValue");
  FuelSValueField.innerHTML = FuelSlider.value; 
  FuelSlider.oninput = function() 
  {
    FuelSValueField.innerHTML = this.value;
    FuelValue = this.value;
    FuelValue = parseInt(FuelValue);
    CPAValue = CPASlider.value;
    CPAValue = parseInt(CPAValue);
    SpeedValue = SpeedSlider.value;
    SpeedValue = parseInt(SpeedValue);
    SuspicionValue = SuspicionSlider.value;
    SuspicionValue= parseInt(SuspicionValue);

    // Balance the others
    Remainder = 100-FuelValue; 
    SumOthers =  CPAValue + SpeedValue + SuspicionValue;
    
    CPASlider.value = CPAValue*Remainder/SumOthers;
    CPASValueField.innerHTML = CPASlider.value; 
    SpeedSlider.value =SpeedValue*Remainder/SumOthers;
    SpeedSValueField.innerHTML = SpeedSlider.value; 
    SuspicionSlider.value = SuspicionValue*Remainder/SumOthers;
    SuspicionSValueField.innerHTML = SuspicionSlider.value; 
  }  // Fuel Weight Change
  // ============================================
  CPASlider = document.getElementById("CPASlider");
  CPASValueField = document.getElementById("CPASValue");
  CPASValueField.innerHTML = CPASlider.value;  
  CPASlider.oninput = function() 
  {
    CPASValueField.innerHTML = this.value;
    CPAValue = this.value;
    CPAValue = parseInt(CPAValue);
    FuelValue = FuelSlider.value
    FuelValue = parseInt(FuelValue);
    SpeedValue = SpeedSlider.value;
    SpeedValue = parseInt(SpeedValue);
    SuspicionValue = SuspicionSlider.value;
    SuspicionValue= parseInt(SuspicionValue);

    // Balance the others
    Remainder = 100-CPAValue; 
    SumOthers =  FuelValue + SpeedValue + SuspicionValue;
    
    FuelSlider.value = FuelValue*Remainder/SumOthers;
    FuelSValueField.innerHTML = FuelSlider.value; 
    SpeedSlider.value =SpeedValue*Remainder/SumOthers;
    SpeedSValueField.innerHTML = SpeedSlider.value; 
    SuspicionSlider.value = SuspicionValue*Remainder/SumOthers;
    SuspicionSValueField.innerHTML = SuspicionSlider.value; 

  } // CPA Weight Change
  // ============================================
  SpeedSlider = document.getElementById("SpeedSlider");
  SpeedSValueField = document.getElementById("SpeedSValue");
  SpeedSValueField.innerHTML = SpeedSlider.value;  
  SpeedSlider.oninput = function() 
  {
    SpeedSValueField.innerHTML = this.value;
    SpeedValue = this.value;
    SpeedValue = parseInt(SpeedValue);
    FuelValue = FuelSlider.value
    FuelValue = parseInt(FuelValue);
    CPAValue = CPASlider.value;
    CPAValue = parseInt(CPAValue);
    SuspicionValue = SuspicionSlider.value;
    SuspicionValue= parseInt(SuspicionValue);

     // Balance the others
     Remainder = 100-SpeedValue; 
     SumOthers =  FuelValue + CPAValue + SuspicionValue;
    
     FuelSlider.value = FuelValue*Remainder/SumOthers;
     FuelSValueField.innerHTML = FuelSlider.value; 
     CPASlider.value = CPAValue*Remainder/SumOthers; 
     CPASValueField.innerHTML = CPASlider.value; 
     SuspicionSlider.value = SuspicionValue*Remainder/SumOthers;
     SuspicionSValueField.innerHTML = SuspicionSlider.value; 
  }  // Speed Weight Change
  // ============================================
  SuspicionSlider = document.getElementById("SuspicionSlider");
  SuspicionSValueField = document.getElementById("SuspicionSValue");
  SuspicionSValueField.innerHTML = SuspicionSlider.value; 
  SuspicionSlider.oninput = function() 
  {
    SuspicionSValueField.innerHTML = this.value;
    SuspicionValue = this.value;
    SuspicionValue = parseInt(SuspicionValue);
    FuelValue = FuelSlider.value
    FuelValue = parseInt(FuelValue);
    CPAValue = CPASlider.value;
    CPAValue = parseInt(CPAValue);
    SpeedValue = SpeedSlider.value;
    SpeedValue = parseInt(SpeedValue);
    
    // Balance the others
    Remainder = 100-SuspicionValue; 
    SumOthers =  FuelValue + CPAValue + SpeedValue;
    
    FuelSlider.value = FuelValue*Remainder/SumOthers;
    FuelSValueField.innerHTML = FuelSlider.value;
    CPASlider.value = CPAValue*Remainder/SumOthers; 
    CPASValueField.innerHTML = CPASlider.value; 
    SpeedSlider.value = SpeedValue*Remainder/SumOthers;
    SpeedSValueField.innerHTML = SpeedSlider.value; 
  } // Behaviour Weight Change
  // =====================================================

  // Now Go to the Tactical Server and Request the Current Scenario
  GetTheCurrentScenarioID() 

} // initmap
// ===============================================================================
function DisplayAboutPage()
{
  // Direct to the About page
  window.location.href ='/about'
}
function ReviewDBScenarios()
{
  // Direct to the About page
  window.location.href ='/scenarios'
}
// ================================================================================
function displayMapCoordinates(pnt) 
{
  var lat = pnt.lat();
  lat = lat.toFixed(3);
  var lng = pnt.lng();
  lng = lng.toFixed(3);

  document.getElementById("mapdisplaylatlong").innerHTML = "Latitude: " + lat + "  Longitude: " + lng;
}  // display Map Coordinates
// =================================================================================
function RedisplaySelectedScenarioID()
{
  document.getElementById("SelectedScenarioText").innerHTML = "Selected Scenario: " + TheSelectedScenarioID;
  document.getElementById("BaseLatLongText").innerHTML = "Base Lat: " + BaseLat + "  Base Long: "+ BaseLong;
  
}
// =====================================================================================================
// Local lat Long to X, Y Coordinated conversion Funcitons 
function LatLongToXY(Lat,Long) 
{
// Base around 
  Xcoord = (Long-BaseLong) * 100.0;
  Ycoord = (Lat-BaseLat) * 150.0;
  return {X:Xcoord,Y:Ycoord};
}
// ========================
function XYToLatLong(Xvalue,Yvalue) 
{
    // Base around [lat:49.0, Long: -5.5] 
    LongValue = Xvalue/100.0 + BaseLong;
    LatValue = Yvalue/150.0 + BaseLat;
    return {lat:LatValue,lng:LongValue};
}
// ========================================================================================== 
function PlotImageOnMap(Reference, ImageFileName, Lat, Long, Scale)
{
  FullImagePath = "http://127.0.0.1:5000/static/images/" + ImageFileName

  ImageBounds = {
    north:Lat+0.05*Scale,
    south:Lat-0.05*Scale,
    east:Long+0.075*Scale,
    west:Long-0.075*Scale,
  }
  Reference = new google.maps.GroundOverlay(FullImagePath, ImageBounds, {clickable:false});
  Reference.setMap(map);
  return Reference
} // PlotImageOnMap
// ========================================================================================== //
function ClearRoutesTable()
{
  for (var i =1; i<NumberofDisplayedRoutes+1; i++)
  {
    RoutesTable.deleteRow(1);
  }
  NumberofDisplayedRoutes = 0
} // ClearRoutesTable
// ==========================================================================================
function InsertRouteDisplay(Rank,Score,Route,FuelScore,CPAScore,SpeedScore,SuspicionScore)
{
  // Fill out and Display a Route Table Row Item

  DisplayRow = RoutesTable.insertRow(Rank);        // Note that Row Zero is the Header Row
  var RankCell = DisplayRow.insertCell(0);
  var ScoreCell = DisplayRow.insertCell(1);
  var RouteCell = DisplayRow.insertCell(2);
  var FuelCell = DisplayRow.insertCell(3);
  var CPACell = DisplayRow.insertCell(4);
  var SpeedCell = DisplayRow.insertCell(5);
  var SuspicionCell = DisplayRow.insertCell(6);
  var DisplayButtonCell = DisplayRow.insertCell(7);
  RankCell.innerHTML = Rank.toString()

  // Score Cell RAG Bar Graph
  ScoreCanvasID = "SCanvas" + Rank.toString()
  CanvasHTML = '<canvas width="100" height="25" id="' + ScoreCanvasID + '" ></canvas>';
  ScoreCell.insertAdjacentHTML('afterbegin',CanvasHTML);
  var c = document.getElementById(ScoreCanvasID);
  var ctx = c.getContext("2d");
  ctx.fillStyle = "#00FF00";
  if(Score<75) ctx.fillStyle = "#FFB000";
  if(Score<40) ctx.fillStyle = "#FF0000";
  ctx.fillRect(5, 5, Score, 20);

  // Display the Route Sequence
  RouteCell.innerHTML = Route;

  // Fuel cell RAG 
  //FuelCell.innerHTML = FuelScore;
  FuelCanvasID = "FCanvas" + Rank.toString()
  CanvasHTML = '<canvas width="100" height="25" id="' + FuelCanvasID + '" ></canvas>';
  FuelCell.insertAdjacentHTML('afterbegin',CanvasHTML);
  var c = document.getElementById(FuelCanvasID);
  var ctx = c.getContext("2d");
  ctx.fillStyle = "#00FF00";
  if(FuelScore<75) ctx.fillStyle = "#FFB000";
  if(FuelScore<40) ctx.fillStyle = "#FF0000";
  ctx.fillRect(5, 5, FuelScore, 20);

  // CPA Cell RAG
  //CPACell.innerHTML = CPAScore;
  CPACanvasID = "CPACanvas" + Rank.toString()
  CanvasHTML = '<canvas width="100" height="25" id="' + CPACanvasID + '" ></canvas>';
  CPACell.insertAdjacentHTML('afterbegin',CanvasHTML);
  var c = document.getElementById(CPACanvasID);
  var ctx = c.getContext("2d");
  ctx.fillStyle = "#00FF00";
  if(CPAScore<75) ctx.fillStyle = "#FFB000";
  if(CPAScore<40) ctx.fillStyle = "#FF0000";
  ctx.fillRect(5, 5, CPAScore, 20);

  // Speed cell RAG
  //SpeedCell.innerHTML = SpeedScore;
  SpeedCanvasID = "SpeedCanvas" + Rank.toString()
  CanvasHTML = '<canvas width="100" height="25" id="' + SpeedCanvasID + '" ></canvas>';
  SpeedCell.insertAdjacentHTML('afterbegin',CanvasHTML);
  var c = document.getElementById(SpeedCanvasID);
  var ctx = c.getContext("2d");
  ctx.fillStyle = "#00FF00";
  if(SpeedScore<75) ctx.fillStyle = "#FFB000";
  if(SpeedScore<40) ctx.fillStyle = "#FF0000";
  ctx.fillRect(5, 5, SpeedScore, 20);

  // Suspicsion Cell RAG
  //SuspicionCell.innerHTML = SuspicionScore;
  SuspicionCanvasID = "SuspicionCanvas" + Rank.toString()
  CanvasHTML = '<canvas width="100" height="25" id="' + SuspicionCanvasID + '" ></canvas>';
  SuspicionCell.insertAdjacentHTML('afterbegin',CanvasHTML);
  var c = document.getElementById(SuspicionCanvasID);
  var ctx = c.getContext("2d");
  ctx.fillStyle = "#00FF00";
  if(SuspicionScore<75) ctx.fillStyle = "#FFB000";
  if(SuspicionScore<40) ctx.fillStyle = "#FF0000";
  ctx.fillRect(5, 5, SuspicionScore, 20);

  // Display Button
  var displaybtn = document.createElement('button'); 
  displaybtn.type= "button";
  displaybtn.className= "editbtn";
  displaybtn.id= "dispbutton-"+(Rank);
  displaybtn.value= "Display";
  displaybtn.innerHTML = "DISPLAY";
  displaybtn.onclick = (function(Rank){ return function(){ DispayRouteRow(Rank)}})(Rank);
  DisplayButtonCell.appendChild(displaybtn); 

  NumberofDisplayedRoutes = NumberofDisplayedRoutes+1;

}  // InsertRouteDisplay
// ============================================================================================
// User Has pressed on a Route Button Function - Process according to Button Mode
function DispayRouteRow(rowindex)
{
  dispbuttonId =  "dispbutton-"+rowindex.toString();
  dispbuttonpressed = document.getElementById(dispbuttonId);

  if(dispbuttonpressed.value == "Display")
  {
    dispbuttonpressed.value = "Execute";
    dispbuttonpressed.innerHTML = "EXECUTE";

    RouteForDisplay =  RoutesWayPointTable[rowindex-1];
    document.getElementById("routestatusstatement").innerHTML = " Displaying Route Ranked: " + rowindex.toString();
    DisplayRoute(RouteForDisplay);
    RouteIndexBeingDisplayed = rowindex-1;
  }   
  else if (dispbuttonpressed.value == "Execute")
  {

    dispbuttonpressed.value = "Running";
    dispbuttonpressed.innerHTML = "RUNNING"; 

    //  Now Need to Set That Misison Going
    StartHeloMission(rowindex-1);
    RouteIndexBeingDisplayed = rowindex-1;
    document.getElementById("routestatusstatement").innerHTML = " Now Executing Route Ranked: " + rowindex.toString();
  }
 
  // Reset all the other buttons to Display default  - Assume just buttons ** need to chnage *to number of routes
  for (var btnindex =1; btnindex<=RoutesWayPointTable.length; btnindex++)
  {
    if(btnindex != rowindex)
    {
      // Reset the other Button Back to Display
      thebuttonId =  "dispbutton-"+btnindex.toString();
      thebutton = document.getElementById(thebuttonId);
      thebutton.value = "Display";
      thebutton.innerHTML = "DISPLAY"
    }
  } // reset all other buttons


} // DispayRouteRow Button pressed
// ============================================================================================
function DisplayTN(Reference,Lat,Long,TN)
{
  // Display a TN text on the Display
  Reference = new google.maps.Marker({
    position: { lat: (Lat+0.05), lng: (Long+0.075)},
    map: map,
    icon: 'http://127.0.0.1:5000/static/images/empty.png',
    label: {
        color: '#FFFF00',
        fontWeight: 'bold',
        text: TN.toString(),
        fontSize: '15px',
    },
  });
  return Reference
}  // DisplayTN
// ========================================================================================== //
function DisplaySuspectLabel(Reference,Lat,Long,SuspicionLevel,Index)
{
  // Display Suspect Lable Text on the Display
  SuspectText = " [" + SuspicionLevel.toString() + "]"
  if(Index == 0)
  {
    // Own Ship is NOT Suspect !
    SuspectText = " "
  }
  Reference = new google.maps.Marker({
    position: { lat: (Lat-0.001), lng: (Long+0.15)},
    map: map,
    icon: 'http://127.0.0.1:5000/static/images/empty.png',
    label: {
        color: '#FF0000',
        text: SuspectText,
        fontSize: '12px',
    },
  });
  return Reference
}  // DisplaySuspectLabel
// ================================================================================================
function DisplayVelocityLeader(Reference,Lat,Long,XVel,YVel)
{
  // Display a Velocity Leader 
  var LineCoords =
  [
    {lat:Lat, lng:Long},
    {lat:(Lat+YVel*0.00666), lng:(Long+XVel*0.01)},
  ]
  var Reference = new google.maps.Polyline({
    path: LineCoords,
    strokeColor: "#FFFF00",
    geodesic: true,
    strokeWeight: 2
  });
  Reference.setMap(map);
  return Reference
}  // DisplayVelocityLeader
// ==================================================================================
function DisplayNominationCircle(CLat,CLong)
{
  var CircleCentre = new google.maps.LatLng(CLat,CLong);

  var Reference = new google.maps.Circle({
    strokeColor: "#FF0000",
    strokeOpacity: 0.25,
    strokeWeight: 1,
    fillColor: "#FF0000",
    fillOpacity: 0.25,
    map: map,
    center: CircleCentre,
    radius: 5000,
    clickable:false,
  });
  NominationCircles.push(Reference); 

} // DisplayNominationCircle
// ==================================================================================
function DisplayRoute(RouteLatLongList)
{
  // Display the route 
  // Assumes RouteLatLongList is an array of [{lat:LatValue,lng:LongValue}]
  if(RouteDisplayed) 
  {
    DisplayedRoute.setMap(null)
  }

  DisplayedRoute = new google.maps.Polyline({
    path: RouteLatLongList,
    strokeColor: "#00FF00",
    geodesic: true,
    strokeOpacity: 0.75,
    strokeWeight: 3
  });
  DisplayedRoute.setMap(map);
  RouteDisplayed = true;

}  // DisplayRoute
// ==================================================================================
function mouseclickonmap(clickpnt)
{
  var MouseLat = clickpnt.lat();
  var MouseLong = clickpnt.lng();
  
  // ===============================
  if(AOIEditingInProgress)
  {
    // Just Clear the AOI as is
    if(AOIDisplayed)
    {
      AOIMapRegion.setMap(null);
    }

    // Simply Add the Mouse latLong: Clickpoint 
    AOIWaypointsList.push(clickpnt)

    AOIMapRegion = new google.maps.Polygon({
      paths: AOIWaypointsList,
      strokeColor: "#FF0000",
      strokeOpacity: 0.2,
      strokeWeight: 1,
      fillColor: "#FF0000",
      fillOpacity: 0.2,
      clickable: false,
    });
      
    AOIMapRegion.setMap(map);
    AOIDisplayed = true;

  }  // AOI Editing
  // =============================
  if(NominationsInProgress)
  {
    // Check if any Tracks close to the Mouse Lat/Long Click Point
    for (var i =1; i<TrackList.tracks.length; i++)
    {
      DeltaLat = MouseLat - TrackList.tracks[i].Lat;
      DelatLong = MouseLong - TrackList.tracks[i].Long;
      DistLatLongSqr = DeltaLat*DeltaLat + DelatLong*DelatLong;
      if(DistLatLongSqr<0.01)
      {
        // Have Found a Track - So Nominate it  and Display a Nomination Circle
        if(!TrackList.tracks[i].Nominated)
        {
          SendTrackNomination(TrackList.tracks[i].TN, true);
          DisplayNominationCircle(TrackList.tracks[i].Lat,TrackList.tracks[i].Long); 
        }
        else
        {
          SendTrackNomination(TrackList.tracks[i].TN, false);
        }
      }
    } // for each track in Tracklist
  }  // NominationsInProgress
} // mouseclickonmap
// =====================================================================================
function CreateAOI()
{
  // Start an AOI Editing Process - Polygon from Click on Map
  AOIEditingInProgress = true;
  NominationsInProgress = false;

  AOIWaypointsList = [] 
  if(AOIDisplayed)
  {
    AOIMapRegion.setMap(null);
  }

} // CreateAOI
// =====================================================================================
function CompleteAOI()
{
  // Complete the AOI Editing Porcess
  AOIEditingInProgress = false;
} // CompleteAOI
// =====================================================================================
function StartNominations()
{
  // Start Track Nominations process - Nominate Tracks from Clicks on Map
  NominationsInProgress = true;
  AOIEditingInProgress = false;
} // StartNominations
// =====================================================================================
function CompleteNominations()
{
  // Complete the Track Nominations
  NominationsInProgress = false;
} // CompleteNominations
// =====================================================================================
function GetTheCurrentScenarioID() 
{
  // Clear the Tracks from Display
  // Set Up a Web Service call into the local Tactical Web Server at http://127.0.0.1:8080/GetCurrentScenarioID 
  var HttpReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/GetCurrentScenarioID';
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  // Set Up the Response processing Event Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeated Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {
      console.log("Scenario ID: Response: ", HttpReq.responseText);
      var SelectedScenarioIDResponse = JSON.parse(HttpReq.responseText);
      TheSelectedScenarioID = SelectedScenarioIDResponse.currentscenarioid;
      BaseLat = SelectedScenarioIDResponse.base_lat;
      BaseLong = SelectedScenarioIDResponse.base_long; 

      // Reset the Map Location
      map.setOptions ( { center:{ lat: BaseLat, lng: BaseLong }, zoom: 8 });

      RedisplaySelectedScenarioID();
    }
  }  // onreadystatechange
  // Now invoke the GET http Request
  HttpReq.send();
  // ================================
  
}  // GetTheCurrentScenarioID
// =====================================================================================
function LoadScenario() 
{
  // Clear Down any Existing CTG Display
  if(CTGDisplayed)
  {
    // Clear Existing Display
    QNLZDisplay.setMap(null);
    CTGLabelDisplay.setMap(null);
    CTGAreaMapRegion.setMap(null);
  }

  // Clear Down Any Existing AOI
  AOIWaypointsList = [] 
  if(AOIDisplayed)
  {
    AOIMapRegion.setMap(null);
  }

  // =======================
  // Set Up a Query for the Scenarios CTG Waypoints
  HttpTrackReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/LoadTaskGroupScenario';
  HttpTrackReq.open("GET", TacticalPictureServerURL);
  // Set Up the Response processing Event Handler
  HttpTrackReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpTrackReq.readyState === XMLHttpRequest.DONE)
    {
      WayPointList = JSON.parse(HttpTrackReq.responseText);
      //console.log("The CTG WayPoints List: ", WayPointList.ctwaypointslist); 
      
      CTGAreaMapRegion = new google.maps.Polygon({
        paths: WayPointList.ctwaypointslist,
        strokeColor: "#00FF00",
        strokeOpacity: 0.4,
        strokeWeight: 1,
        fillColor: "#33FF33",
        fillOpacity: 0.3,
        clickable: false,
      });
        
      CTGAreaMapRegion.setMap(map);
      CTGDisplayed = true;

      // Now Calculate the centroid of the Task Group Region and set QNLZ There
      CTGCentroid = CalculateCTGCentroid(WayPointList.ctwaypointslist); 
      //  Plot HMS QNLZ Icon  at the Centrold
      QNLZDisplay = PlotImageOnMap(QNLZDisplay, "QNLZ.png",CTGCentroid['CentreLat'],CTGCentroid['CentreLong'], 2.0);
      // Add TG Label Below the Centroid
      CTGLabelDisplay =  PlotImageOnMap(CTGLabelDisplay, "CTGLabel.png",CTGCentroid['CentreLat']-0.2, CTGCentroid['CentreLong'], 1.5);

    } // DONE
  }  // onreadystatechange
  // Now invoke the GET http Request
  HttpTrackReq.send();
  
}  // LoadScenario
//  ======================================================================================= 
function CalculateCTGCentroid(CTGList)
{
  // Calculate the Centrolid Lat Long from the Dict list

    NumberCoordinates = CTGList.length;
    SumLat = 0.0;
    SumLong = 0.0;
    AVGLat = 50.0;
    AVGLong = 0.0;
    for(var i =0; i<CTGList.length; i++)
    {
      SumLat = SumLat + CTGList[i]['lat'];
      SumLong = SumLong + CTGList[i]['lng'];
    }
    if(NumberCoordinates>0)
    {
      AVGLat = SumLat/NumberCoordinates;
      AVGLong = SumLong/NumberCoordinates;
    }

  return { CentreLat:AVGLat,CentreLong:AVGLong };
} // CalculateCTGCentroid
//  ======================================================================================= 
function StartScenarioFunction() 
{
  // Clear the Tracks from Display
  ClearDisplayedTracks();
  TracksDisplayed = false;
  RouteDisplayed = false;
  
  LoadScenario;

  SimulationTime = 0; 

  // Set Up a Web Service call into the local Tactica Web Server at http://127.0.0.1:8080/StartScenario 
  var HttpReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/StartScenario';
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  // Set Up the Response processing Event Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeated Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {
      //console.log("Scenario Start: Response: ", HttpReq.responseText);
      document.getElementById("statusstatement").innerHTML = " Scenario Running";
    }
  }  // onreadystatechange
  // Now invoke the GET http Request
  HttpReq.send();
  // ================================
  // Start a Periodic Display Timer every 1 seconds
  ScenarioStatus = RUNNING;
  document.getElementById("statusstatement").innerHTML = " Scenario Running ";
  TheDisplayUpdateTimer = setInterval(UpdateDisplay, 2000);
}  // StartScenario
//  ======================================================================================= 
function PauseButtonFunction() 
{
  if(ScenarioStatus == RUNNING)
  {
    document.getElementById("statusstatement").innerHTML = " Scenario Paused ";
    clearInterval(TheDisplayUpdateTimer);
    SendScenarioInstruction('pause'); 
    ScenarioStatus = PAUSED;
    var ButtonImage = document.getElementById("PauseButtonImage");
    ButtonImage.src= "http://127.0.0.1:5000/static/images/Restart.png";
  
  }
  else
  {
    document.getElementById("statusstatement").innerHTML = " Scenario Running ";
    TheDisplayUpdateTimer = setInterval(UpdateDisplay, 2000);
    SendScenarioInstruction('restart'); 
    ScenarioStatus = RUNNING;
    var ButtonImage = document.getElementById("PauseButtonImage");
    ButtonImage.src= "http://127.0.0.1:5000/static/images/Pause.png";
  }

} // PauseButtonFunction
//  ============================================================================= 
function StopButtonFunction() 
{
  document.getElementById("statusstatement").innerHTML = " Scenario Stopped";
  clearInterval(TheDisplayUpdateTimer);
  SendScenarioInstruction('stop');
  ScenarioStatus = WAITING;
  document.getElementById("SimTimeDisplay").innerHTML = " ";

  ClearDisplayedTracks();
  // Clear the CTG Display
  if(CTGDisplayed)
  {
    // Clear Exisiting Display
    QNLZDisplay.setMap(null);
    CTGLabelDisplay.setMap(null);
    CTGAreaMapRegion.setMap(null);
  }

  // Clear the Displayed Route
  if(RouteDisplayed) 
  {
    DisplayedRoute.setMap(null)
  }

  if(HeloDisplayed)
  {
    HeloIcon.setMap(null);
  }
  if(AOIDisplayed)
  {
    AOIMapRegion.setMap(null);
  }

} // StopButtonFunction
// ===========================================================================
function ClearDisplayedTracks()
{
  if((TracksDisplayed=true) && ( TrackIcons != null ))
  {
    // Clear existing Target icons
    for (var i =0; i<TrackIcons.length; i++)
    {
      TrackIcons[i].setMap(null);
      TrackNumberLables[i].setMap(null);
      VelocityLeaders[i].setMap(null);
      SuspectLables[i].setMap(null);
    }
    for(var i =0; i<NominationCircles.length; i++)
    {
      NominationCircles[i].setMap(null);
    }

  }
}  // ClearDisplayedTracks
// ===========================================================================
function StartHeloMission(routeID) 
{
  // Sent Up a HeloMission Request againt Route
  RouteTNSequence =  RouteTNSequenceTable[routeID];
  console.log(" Starting a Helo Mission: ", routeID, " sequecne: ", RouteTNSequence)

  // ===============================
  // Now Set up tje  POST to  Request 
  var HttpReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/StartHeloMission';
 
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  
  // Set Up the Response Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {  
      var MissionInstructionResponse = JSON.parse(HttpReq.responseText)
      if(MissionInstructionResponse.result != 'success')
      {
        document.getElementById("statusstatement").innerHTML = " Mission Request Failed"
      }
    }  // XMLHttpRequest.DONE
  } // onreadystatechange
  // ==================================
  // Now Invoke the POST Send
  var MissionReq = JSON.stringify({"routetnsequence": RouteTNSequence});
  HttpReq.send(MissionReq);

} // StartHeloMission
// ==============================================================================
// Periodic Display Update Call 
function UpdateDisplay() 
{

  QueryandUpdateTracksDisplay()

  QueryandUpdateHeloDisplay()

  if(RouteIndexBeingDisplayed>-1)
  {
    // Route has been selected for display
    // Recheck the Waypoint list, from the TN Sequence
    ThePlannedTNSequence= RouteTNSequenceTable[RouteIndexBeingDisplayed];
    UpdatedRouteWaypointlist= GetTheLatLongRouteSequence(ThePlannedTNSequence);
    DisplayRoute(UpdatedRouteWaypointlist);
    //console.log(UpdatedRouteWaypointlist)
  }

} // UpdateDisplay
// ==============================================================================================
function QueryandUpdateTracksDisplay() 
{
  // Call into Web Service to get Current Tracks from Tacrtical Picture Web Server at http://127.0.0.1:8080/Tracks 
  var HttpTrackReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/Tracks';
  HttpTrackReq.open("GET", TacticalPictureServerURL);
  // Set Up the Response processing Event Handler
  HttpTrackReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpTrackReq.readyState === XMLHttpRequest.DONE)
    {
      TrackList = JSON.parse(HttpTrackReq.responseText);

      // Clear displayed Tracks
      ClearDisplayedTracks()

      // Retrieve the Simulaton Time
      SimulationTime = TrackList.simtime; 
      document.getElementById("SimTimeDisplay").innerHTML = "Sim Time: "+ SimulationTime.toString();
      
      // Now process the Tracks List
      TrackIcons = new Array(TrackList.tracks.length); 
      TrackNumberLables = new Array(TrackList.tracks.length); 
      VelocityLeaders =  new Array(TrackList.tracks.length); 
      SuspectLables = new Array(TrackList.tracks.length);

      // Now ReDisplay Tracks
      for (var i =0; i<TrackList.tracks.length; i++)
      {
        //console.log("Plotting Track: ", i, "at: Lat:", TrackList.tracks[i].Lat," Long: ",TrackList.tracks[i].Long);
        if(i==0)
        {
          // Own Track Instance
          TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"Frigate.PNG", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 2.0)
        }
        else
        {
          // Other Track Types
          if(TrackList.tracks[i].Identity=="UNKNOWN")
          {
            TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"Unknown.png", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 1.0)
          }
          if(TrackList.tracks[i].Identity=="NSail")
          {
            TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"NSail.png", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 1.5)
          }
          if(TrackList.tracks[i].Identity=="HSub")
          {
            TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"HSub.png", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 1.5)
          }
          if(TrackList.tracks[i].Identity=="NShip")
          {
            TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"NShip.png", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 1.5)
          }
          if(TrackList.tracks[i].Identity=="HFrigate")
          {
            TrackIcons[i] = PlotImageOnMap(TrackIcons[i],"HFrigate.png", TrackList.tracks[i].Lat, TrackList.tracks[i].Long, 1.5)
          }

          // Show a Nomination Circle if Track is Nominated
          if(TrackList.tracks[i].Nominated)
          {
            DisplayNominationCircle(TrackList.tracks[i].Lat,TrackList.tracks[i].Long);
          }
          
        } // Display of Track Icons
        
        TrackNumberLables[i] = DisplayTN(TrackNumberLables[i],TrackList.tracks[i].Lat, TrackList.tracks[i].Long,TrackList.tracks[i].TN)
        VelocityLeaders[i] = DisplayVelocityLeader(VelocityLeaders[i],TrackList.tracks[i].Lat, TrackList.tracks[i].Long,TrackList.tracks[i].XVel,TrackList.tracks[i].YVel)
        SuspectLables[i] = DisplaySuspectLabel(SuspectLables[i],TrackList.tracks[i].Lat, TrackList.tracks[i].Long,TrackList.tracks[i].Suspicion, i)

        TracksDisplayed = true;
      }
      
    } // DONE
  }  // onreadystatechange
  // Now invoke the GET http Request
  HttpTrackReq.send();

} // QueryandUpdateTracksDisplay
// =====================================================================================
function QueryandUpdateHeloDisplay() 
{
  // Call into Web Service to get Current Helo from Tactical Picture Web Server at http://127.0.0.1:8080/Helo 
  var HttpHeloReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/Helo';
  HttpHeloReq.open("GET", TacticalPictureServerURL);
  // Set Up the Response processing Event Handler
  HttpHeloReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpHeloReq.readyState === XMLHttpRequest.DONE)
    {
      // Clear the Helo Icon
      if(HeloDisplayed)
      {
        HeloIcon.setMap(null);
      }
      var HeloResponse = JSON.parse(HttpHeloReq.responseText)
      //console.log("Helo Query Response: ", HeloResponse)

      if(HeloResponse.helostatus==1)
      {
        // Helo is Traversing
        HeloIcon = PlotImageOnMap(HeloIcon,"Helo.PNG", HeloResponse.helolat, HeloResponse.helolng, 2.0);
        HeloDisplayed = true;
      }
      if(HeloResponse.helostatus==2)
      {
        // Helo is Sensing
        HeloIcon = PlotImageOnMap(HeloIcon,"HeloObserve.PNG", HeloResponse.helolat, HeloResponse.helolng, 2.0);
        HeloDisplayed = true;
      }
    } // DONE
  }  // onreadystatechange
  // Now invoke the GET http Request
  HttpHeloReq.send();

} // QueryandUpdateHeloDisplay
// ======================================================================================
function GetTrackIdFromTN(TrackNumber) 
{
    RtnTrackId = -1
    for (var i =0; i<TrackList.tracks.length; i++)
    {
      if(TrackList.tracks[i].TN==TrackNumber)
      {
        RtnTrackId = i;
      }
    }
    return RtnTrackId   
} // GetTrackIdFromTN
//  =======================================================================================
function GetDisplayedRouteString(TNSequence)
{
  var RouteString = "["
  for (var i =0; i<TNSequence.length; i++)
  {
   var TrackId = GetTrackIdFromTN(TNSequence[i].TN)  // Hope to get TrackId from the TN
   if(TrackId>-1)
   {
     RouteString = RouteString.concat(TNSequence[i].TN.toString(),", ")
   }
   else
   {
     console.log(" Note: Route TN is no Longer in Track Table"); 
   }
  } 
  RouteString = RouteString.concat("]");
  return RouteString
} // GetDisplayedRouteString
// =======================================================================================
function GetTheLatLongRouteSequence(TNSequence)
{
  var MTracks = new Array(TNSequence.length);
  TrackIndex = 0
  for (var i =0; i<TNSequence.length; i++)
  {
    var TrackId = GetTrackIdFromTN(TNSequence[i].TN)  // Hope to get TrackId from the TN
    if(TrackId>-1)
    {
      MTracks[TrackIndex] = TrackId;
      TrackIndex = TrackIndex+1
    }
  }  // First Pass to get List of Track Ids
  
  // Now Fill out Mission Route List
  var MissionRoute = new Array(TrackIndex);
  for (var i =0; i<TrackIndex; i++)
  {
    MissionLatLongCoord = {lat:TrackList.tracks[MTracks[i]].Lat,lng:TrackList.tracks[MTracks[i]].Long};
    MissionRoute[i] = MissionLatLongCoord
  }

  return MissionRoute
}  // GetTheLatLongRouteSequence
// ========================================================================================
function SendScenarioInstruction(SInstruction)
{
  var HttpReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:8080/ScenarioInstruction';
 
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  
  // Set Up the Response Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {  
      var MissionInstructionResponse = JSON.parse(HttpReq.responseText)
      if(MissionInstructionResponse.result != 'success')
      {
        document.getElementById("statusstatement").innerHTML = " Scenario Request Failed"
      }

    }  // XMLHttpRequest.DONE
  } // onreadystatechange

  // Now Invoke the POST Send
  var PostedData = JSON.stringify({"sinstruction": SInstruction});
  HttpReq.send(PostedData);

} // SendScenarioInstruction
// ========================================================
function SendTrackNomination(TrackNumber, Directive)
{
  var HttpReq = new XMLHttpRequest();
  var TacticalPictureServerURL='http://127.0.0.1:8080/NominateTrack';
  if(!Directive)
  {
    TacticalPictureServerURL='http://127.0.0.1:8080/UnNominateTrack';
  }
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  // Set Up the Response Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {  
      var MissionInstructionResponse = JSON.parse(HttpReq.responseText)
      if(MissionInstructionResponse.result != 'success')
      {
        document.getElementById("statusstatement").innerHTML = "Track Nomination Failed"
      }
    }  // XMLHttpRequest.DONE
  } // onreadystatechange
  // Now Invoke the POST Send
  var PostedData = JSON.stringify({"tracknumber": TrackNumber});
  HttpReq.send(PostedData);
} // SendTrackNomination
// ========================================================
function CaptureWeights()
{
  var HttpReq = new XMLHttpRequest();
  const TacticalPictureServerURL='http://127.0.0.1:7070/UpdateWeights';
 
  HttpReq.open("POST", TacticalPictureServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");
  
  // Set Up the Response Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {  
      var MissionInstructionResponse = JSON.parse(HttpReq.responseText)
      if(MissionInstructionResponse.result != 'success')
      {
        document.getElementById("statusstatement").innerHTML = " Weight Updates Failed"
      }
    }  // XMLHttpRequest.DONE
  } // onreadystatechange
  // =================
  // Read the User selected weights and set up the json dict of weights

  FuelValue = FuelSlider.value;
  FuelValue = parseInt(FuelValue);
  CPAValue = CPASlider.value;
  CPAValue = parseInt(CPAValue);
  SpeedValue = SpeedSlider.value;
  SpeedValue = parseInt(SpeedValue);
  BehaviourValue = SuspicionSlider.value;
  BehaviourValue= parseInt(BehaviourValue);

  JWeights = 
  {
    "fuelweight": FuelValue,
    "cpaweight":CPAValue,
    "speedweight":SpeedValue,
    "suspicionweight":BehaviourValue
  }

  // Now Invoke the POST Send
  var PostedData = JSON.stringify({"userweights": JWeights});
  HttpReq.send(PostedData);

}  // CaptureWeights
// ========================================================
function ResetWeights()
{
  // Reset the User Weights to [ 25,25,25,25]
  FuelSValueField.innerHTML = 25; 
  FuelSlider.value = 25;
  CPASlider.value = 25;
  CPASValueField.innerHTML = 25;  
  SpeedSlider.value = 25;
  SpeedSValueField.innerHTML =25;  
  SuspicionSlider.value = 25;
  SuspicionSValueField.innerHTML = 25; 
  
} // ResetWeights

// ===============================================================
function CreateRoutes()
{
  document.getElementById("routestatusstatement").innerHTML = " Creating the Route.  Please wait .......";

  // Call into the Mission Planning Server to Create Routes at http://127.0.0.1:7070/RequestRoute
  var HttpReq = new XMLHttpRequest();
  const MissionPlannerServerURL='http://127.0.0.1:7070/RequestRoute3';

  HttpReq.open("POST", MissionPlannerServerURL);
  HttpReq.setRequestHeader("Content-Type", "application/json");

  // Set Up the Response Handler
  HttpReq.onreadystatechange = (e) => 
  {
    // Need to wait until fully complete as will get repeatd Responses 
    if(HttpReq.readyState === XMLHttpRequest.DONE)
    {  
      var RequestRouteResponse = JSON.parse(HttpReq.responseText)
      console.log("Request Route Response: ", RequestRouteResponse)
      ClearRoutesTable();
      if(RequestRouteResponse.result == 'Success')
      {
        RoutesList = RequestRouteResponse.routetable
        //console.log(" Route List Response: ", RoutesList);

        RoutesWayPointTable = new Array(RoutesList.length);
        RouteTNSequenceTable = new Array(RoutesList.length);
        for (var RouteIndex=0; RouteIndex<RoutesList.length; RouteIndex++)
        {
          // Extract each RouteItem
          RankValue = RoutesList[RouteIndex].rank;
          OverallScore = RoutesList[RouteIndex].overallscore;
          TheRouteSequence = RoutesList[RouteIndex].route;
          // Take this opportuntiy to Add Track [0] To end of the generated Routes  to Rtn to Ship
          TheRouteSequence.push({"TN":0});

          FuelScore = RoutesList[RouteIndex].fuelscore;
          CPAScore = RoutesList[RouteIndex].CPAscore;
          SpeedScore = RoutesList[RouteIndex].speedscore;
          SuspicionScore = RoutesList[RouteIndex].suspicionscore;
          RouteString = GetDisplayedRouteString(TheRouteSequence);
          InsertRouteDisplay(RankValue,OverallScore,RouteString,FuelScore,CPAScore,SpeedScore,SuspicionScore);

          // Get the Route TrackId Sequence
          TheLatLogRoute = GetTheLatLongRouteSequence(TheRouteSequence);
          RoutesWayPointTable[RouteIndex] = TheLatLogRoute;               // Note the Lat Log Sequence is an Arrary may get overwritten by Reference USE
          RouteTNSequenceTable[RouteIndex] = TheRouteSequence;

        }  // for each Route in returned response
        RouteInExecution = 0;
        document.getElementById("routestatusstatement").innerHTML = " Route List Received ";
      }
      else
      {
        console.log("Error Unable to process Route Request: ");
        document.getElementById("routestatusstatement").innerHTML = RequestRouteResponse.result;
      }
  } // Http Route Request Processing Done
} // ===========================================
// Now Set Up the POST Send 
// Need to Capture the Current User Weights as this is Now Passed into RequestRoute2 Web Service
  FuelValue = FuelSlider.value;
  FuelValue = parseInt(FuelValue);
  CPAValue = CPASlider.value;
  CPAValue = parseInt(CPAValue);
  SpeedValue = SpeedSlider.value;
  SpeedValue = parseInt(SpeedValue);
  BehaviourValue = SuspicionSlider.value;
  BehaviourValue= parseInt(BehaviourValue);
  JWeights = 
  {
    "fuelweight": FuelValue,
    "cpaweight":CPAValue,
    "speedweight":SpeedValue,
    "suspicionweight":BehaviourValue
  }
  // ============================
  // Now need to review and capture those Tracks in Area of Interest
  var NominatedTNList = [];
  if(AOIDisplayed)
  {
    for (var i =1; i<TrackList.tracks.length; i++)
    {
      var TrackPoint = new google.maps.LatLng(TrackList.tracks[i].Lat, TrackList.tracks[i].Long);
      // Check Whether the Track is inside the AOIWaypointsList polygon
      if(google.maps.geometry.poly.containsLocation(TrackPoint,AOIMapRegion))
      {
        NominatedTNList.push(TrackList.tracks[i].TN);
      } 
    } // for each track in Tracklist
  }
  // Now Issue the POST RequestsRoutes2 Requests, including User Weights
  var PostedData = JSON.stringify({"userweights": JWeights, "tracksinaoi":NominatedTNList});
  HttpReq.send(PostedData);

} // CreateRoutes Processing
// ========================================================

// ===================================================================================
function ClearRoutes()
{
  document.getElementById("routestatusstatement").innerHTML = " Clearing Routes.";
  ClearRoutesTable();
  RouteIndexBeingDisplayed = -1;

  if(RouteDisplayed) 
  {
    DisplayedRoute.setMap(null)
  }
  if(HeloDisplayed)
  {
        HeloIcon.setMap(null);
  }

}  // ClearRoutes()
// ================================================= 
function TestButton1()
{
  document.getElementById("routestatusstatement").innerHTML = " TEST BUTTON Pressed";
} //TestButton1
// =============================================================
