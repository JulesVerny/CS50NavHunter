
# ===============================================================================================
#  A Simple Track Type class used in both the Tacatical Picture Server and the Mission Planning Server Processing
#  It includes some local CPA and Distance funcitons to aid the Mission Planning Genetic Algorithm Porcessing
#  The 'Suspicion' attribute is a pseudo represetnation of suspicious behvaiour from otehr analytics. 
# 
# ===============================================================================================
import numpy as np 
import math
# =========================================================================
def CalculateCPA(PointX,PointY,VelX,VelY):
	CPADistance =10000.0
	Angle = 0
	# Assume All CPA to Point [-100,0]
	BVectorX,BVectorY = -100-PointX,0-PointY
	# Angle = ArcCos (Dot Product (B.Vel) / (MagV x MagB) )
	DotBV=  BVectorX*VelX + BVectorY*VelY
	MagV = np.sqrt((VelX*VelX) + (VelY*VelY))
	MagB = np.sqrt((BVectorX*BVectorX) + (BVectorY*BVectorY))
	if(MagV>1.0):
		Angle = math.acos(DotBV/(MagV*MagB))
	if((Angle>-math.pi/2.0) and (Angle<math.pi/2.0) and (MagV>1.0)):
		CPADistance = MagB*math.sin(Angle)
		if(CPADistance<0.0):
			CPADistance = -CPADistance

	return CPADistance
# ===========================================================================
class Track:
	def __init__(self,TrackId, NewTN, InitialXpos, InitialYpos, InitialXVel,InitialYVel, Suspicion):
		self.OriginalTrackID = TrackId
		self.TN = NewTN
		self.Xpos = InitialXpos
		self.Ypos = InitialYpos
		self.Xvel = InitialXVel
		self.Yvel = InitialYVel		
		self.Suspicion = Suspicion 
		self.Identity = "UNKNOWN"
		self.Nominated = False
		self.Speed = np.sqrt((self.Xvel*self.Xvel) + (self.Yvel*self.Yvel))
		self.CPA = CalculateCPA(self.Xpos,self.Ypos,self.Xvel,self.Yvel)
		self.Distance = np.sqrt((-100.0 -self.Xpos)* (-100.0 -self.Xpos) + (0.0-self.Ypos)*(0.0-self.Ypos))
		
    #  Revise Track Velocity
	def UpdateTrack(self, NewXVel,NewYVel,NewSuspicion):
		self.Xvel = NewXVel
		self.Yvel = NewYVel	
		self.Suspicion = NewSuspicion
		self.Speed = np.sqrt((self.Xvel*self.Xvel) + (self.Yvel*self.Yvel))
		self.CPA = CalculateCPA(self.Xpos,self.Ypos,self.Xvel,self.Yvel)
		
	#  Update Track Position
	def UpdatePosition(self,):
		self.Xpos = self.Xpos + self.Xvel*0.01
		self.Ypos = self.Ypos + self.Yvel*0.01	

	def IdentifyTrack(self, ProposedIdentity):
		self.Identity = ProposedIdentity
	
	def SetNominated(self,):
		self.Nominated = True
	def SetUnNominated(self,):
		self.Nominated = False