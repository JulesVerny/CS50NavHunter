#  A Simple Route Itemclass
import numpy as np 
# =========================================================================

class RouteItem:
	def __init__(self,RankValue,OverallScoreValue, RouteSequence,FuelScore,CAPScore,SpeedScore, SuspicionScore):
		self.Rank = RankValue
		self.OverallScore = OverallScoreValue
		self.RouteSequence = RouteSequence
		self.FuelScore = FuelScore
		self.CAPScore = CAPScore	
		self.SpeedScore = SpeedScore
		self.SuspicionScore =SuspicionScore
		
    #  Rank Value
	def UpdateRank(self, NRankValue):
		self.Rank = RankValue
