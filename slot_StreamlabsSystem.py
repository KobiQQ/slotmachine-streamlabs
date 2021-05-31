#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import json
import os
import codecs
import datetime
import operator
import clr

clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

sys.path.append(os.path.join(os.path.dirname(__file__), "../globalFiles/Moduls/pythonClasses"))
import streamlabsSettingClass

import sqlite3
#---------------------------------------
#   [Required] Script Information
#---------------------------------------
ScriptName = "Slotmachine"
Website = "twitch.tv/kobiqq"
Description = "Slotmachine minigame with overlay"
Creator = "Global | KobiQQ"
Version = "1.22"

"""
1.22 Added Setting and Viewer Classes
1.21 A lot of code improvements - db decorators
1.2 Added new Statistics 
1.1 Visual Update
1.0 First official release 
"""

clr.AddReferenceToFileAndPath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../globalFiles/Moduls/personalDll/basicBotFunctionality/bin/Debug/netstandard2.0/coreFunctions.dll"))
from cBotDll import *


SettingsFile = os.path.join(os.path.dirname(__file__), "Settings/settings.json")

#Test this class
class viewerData:

    __pointsNeededToRankUp = 10000

    def __init__(self,data):
        self.__name = Parent.GetDisplayName(data.User) 
        self.__ID = data.User

        self.__rank = str(Parent.GetRank(data.User))
        self.__totalPoints = Parent.GetPoints(data.User)
        self.__rankLevel = self.__totalPoints/viewerData.__pointsNeededToRankUp


    def getPoints(self):
        if self.__rankLevel == 0:
            rightUserPoints = self.__totalPoints

        else:            
            rightUserPoints = self.__totalPoints - (self.__rankLevel * viewerData.__pointsNeededToRankUp)

        return rightUserPoints

    def getUserRank(self):
        return self.__rank

    def getUsername(self):
        return self.__name

    def getUserID(self):
        return self.__ID

    def getUserRankLevel(self):
        return self.__rankLevel

    def getTotalPoints(self):
        return self.__totalPoints

    def updatePointsNeededToRankUp(self,newValue):
        self.__pointsNeededToRankUp = newValue

class thisScriptSettings(streamlabsSettingClass.scriptSettings):

    def __init__(self, settingsfile=None):
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
            Parent.Log(ScriptName, "Couldnt find Settingsfile loading default values")
            self.Enabled = True
            self.Command = "!slot"
            self.Permission = "Everyone"
            self.PermissionInfo = ""
            self.Cost =  100
            self.UseCD = True
            self.Cooldown = 20
            self.OnCooldown = "{0} The command is still on cooldown for {1} seconds!"
            self.UserCooldown =  20
            self.OnUserCooldown = "{0} The command is still on cooldown for {1} seconds!"
            self.forceGameStyle = True,
            self.gameDesign = "Oot"


def Init():

    global ScriptSettings
    ScriptSettings = thisScriptSettings(SettingsFile)

    global core
    core = cBotFunctions()

    return

def Execute(data):

    if data.IsChatMessage() and ScriptSettings.Enabled and data.GetParam(0).lower() == ScriptSettings.Command:
        
        if Parent.HasPermission(data.User, ScriptSettings.Permission, ScriptSettings.PermissionInfo):
        
            viewer = viewerData(data)
            rightUserPoints = viewer.getPoints()

            #check if command is on cooldown
            if IsOnGlobalOrUserCooldown(data,viewer.getUsername()):
                return

            if rightUserPoints >= ScriptSettings.Cost:

                slotRoll = int(Parent.GetRandom(1,1001))
                #Parent.Log(ScriptName,str(slotRoll))
                
                if viewer.getUsername() == 'KobiQQ':
                    
                    kobiPersonalSlotRutine(data.GetParam(1).lower(),viewer.getUsername(),slotRoll)

                else:
                    viewerSlotRutine(viewer,slotRoll)

            else:
                #send not enough currency response
                Parent.SendTwitchWhisper(data.User,"You got " + str(rightUserPoints) + " Points, but you need 100 to use this command")


    return

def Tick():
    return

def dbConnection(dbName):

    """Decorater (Generic template function)
        use DB name as argument in the decorator to select the correct Database"""
    
    if dbName == "streamUserData":

        conn = sqlite3.connect(os.path.dirname(__file__) + "/../globalFiles/Datenbanken/streamUserData.db", check_same_thread=False)
        c = conn.cursor()

    def dbConnector(fn):
      
        def invokeSQLQuerry(*args):

            try:
                result = fn(c,*args)

            except Exception as err:
                Parent.Log(ScriptName,"Query Failed in: " + str(fn) + " with the Error " + str(err))
            else: 
                conn.commit()
                return result          
            finally:
                conn.close()

        return invokeSQLQuerry

    return dbConnector

@dbConnection("streamUserData")
def removeFromWhisperDB(c,username):

    """Once a User used the !slot command remove him from the whisper notification table"""

    c.execute("SELECT id FROM whisperuser WHERE name=?",(username.lower(),))
    row = c.fetchone()

    c.execute("DELETE FROM whisperuser WHERE id=?",(row[0],))

    return

@dbConnection("streamUserData")
def updateSlotStatistics(c,username,statisticType):

    """User Statistics. Keeps track how many times a User used the Slotmachine"""

    try:
        c.execute("SELECT timesUsed,timesWon FROM slotStatistics WHERE username=?",(username,))
        row = c.fetchone()

        increaseSlotCounter   = row[0] + 1;
        increaseTimesWon      = row[1] + 1;

        if statisticType == "IncreaseGamesPlayed":

            c.execute("UPDATE slotStatistics SET timesUsed =? WHERE username=?",(increaseSlotCounter,username,))

        if statisticType == "IncreaseGamesWon":

            c.execute("UPDATE slotStatistics SET timesWon =? WHERE username=?", (increaseTimesWon, username,))

        Parent.Log(ScriptName,"username found - Slot uses increased")

    except:

        c.execute("INSERT INTO slotStatistics ('timesUsed','username') values (?,?)", (1, username,))
        Parent.Log(ScriptName,"New user Inserted into Slot Statistics")

    return

def viewerSlotRutine(viewer,slotRoll):

    username = viewer.getUsername()
    userID = viewer.getUserID()

    Parent.RemovePoints(userID,username, ScriptSettings.Cost)

    #Add user cooldowns
    Parent.AddCooldown(ScriptName, "!slot", ScriptSettings.UserCooldown)
    Parent.AddUserCooldown(ScriptName, ScriptSettings.Command, userID, ScriptSettings.UserCooldown)

    responsesList = ["Good luck @" + username  + "!!",
                    "Toi Toi @" + username  + "!!",
                    "Sometimes you win, sometimes you loose @" + username  + "!!",
                    "Do we see the next winner?? @" + username  + "!!"]
    responseChoice = int(Parent.GetRandom(1,len(responsesList)))
    
    Parent.SendStreamMessage ("/me " + responsesList[responseChoice])
                
    newPoints = (viewer.getUserRankLevel()*10000) + 10000
        
    removeFromWhisperDB(username)

    #A [list with dictonaries{key=rankNames:[ranks], key=design:slotdesigns, key=resetPoints:amount, key=slotWinningNumber}]
    slotInformationDict = [{"rankNames":['Unranked','Bronze V','Bronze IV','Bronze III','Bronze II','Bronze I'],
                            "design":"Bronze",
                            "resetPoints":75,
                            "slotWinningNumber":750},

                            {"rankNames":['Silver V','Silver IV','Silver III','Silver II','Silver I'],
                            "design":"Silver",
                            "resetPoints":66,
                            "slotWinningNumber":666},

                            {"Gold":['Gold V','Gold IV','Gold III','Gold II','Gold I'],
                            "design":"Gold",
                            "resetPoints":55,
                            "slotWinningNumber":550},

                            {"Platinum":['Platinum V','Platinum IV','Platinum III','Platinum II','Platinum I'],
                            "design":"Platin",
                            "resetPoints":45,
                            "slotWinningNumber":450},

                            {"Diamond":['Diamond V','Diamond IV','Diamond III','Diamond II','Diamond I'],
                            "design":"Diamond",
                            "resetPoints":35,
                            "slotWinningNumber":350},

                            {"Master":['Master V','Master IV','Master III','Master II','Master I'],
                            "design":"Diamond",
                            "resetPoints":25,
                            "slotWinningNumber":250},

                            {"Grand Master":['Grand Master V','Grand Master IV','Grand Master III','Grand Master II','Grand Master I'],
                            "design":"Diamond",
                            "resetPoints":15,
                            "slotWinningNumber":150}]

    for divisionInformationDict in slotInformationDict:
        #I cant Acces eachRankDict.values() because this would return a VIEW and not a list
        #So we have to transform it into a list first 
        rankNames = list(divisionInformationDict.values())
        userRank = viewer.getUserRank()

        if userRank in rankNames[0]:

            design = rankNames[1]

            resultSlot(userID,username,viewer.getTotalPoints(),newPoints,
            {"slotRoll":slotRoll,"slotWinningNumber":rankNames[3],"resetPoints":rankNames[2]})

            updateSlotStatistics(username,"IncreaseGamesPlayed")
            

            selectedGameDesign = getSlotGameDesign()


            #Here could be the game style

            eventList = []
            eventList.append("playSlot")

            varList = []
            slotVariableDict = {"rang":userRank,"borderDesign":design,"number":slotRoll,"username":username,"selectedGameDesign":selectedGameDesign}
            varList.append(slotVariableDict)

            dict = {"eventList":eventList,"varList":varList} 

            Parent.BroadcastWsEvent("sendEvent", json.dumps(dict))  
            break 

    else:
        Parent.Log(ScriptName,"Couldnt find the specific rank inside the rank dict - 242")
    return

def resultSlot(userID,username,currentUserPoints,newPoints,slotGameDict):

    """ Adds/Removes the currency depending if the User won/lost @ the slotmachine
        Adds extra Points if the User won the Jackpot
    
        Input arguments:
        userID, username, currentUserPoints, newPoints
        slotGameDict : {"slotRoll,"slotWinningNumber","resetPoints"}
    """

    if slotGameDict['slotRoll'] <= slotGameDict['slotWinningNumber']:

        Parent.RemovePoints(userID,username, currentUserPoints)
        Parent.AddPoints(userID,username,newPoints)

        updateSlotStatistics(username,"IncreaseGamesWon")

        #Checks if user won the Jackpot
        if slotGameDict['slotRoll'] == 1:
            jackpotPoints = 100

        elif slotGameDict['slotRoll'] <= 5:
            jackpotPoints = 50
                    
        elif slotGameDict['slotRoll'] <= 10: 
            jackpotPoints = 25
        
        if slotGameDict['slotRoll'] < 11:
            Parent.AddPoints(userID,username,jackpotPoints)


        
    else:
        Parent.AddPoints(userID,username,slotGameDict['resetPoints'])


    return


#Not well implented yet
def getSlotGameDesign():

    """Returns the Selected game Design if any is inside the DB"""

    if ScriptSettings.forceGameStyle:

        selectedGameDesign = str(ScriptSettings.gameDesign)

    else:
        #look for the game on twitch
        selectedGameDesign = "Standart"

    return selectedGameDesign

def kobiPersonalSlotRutine(arg,username,slotRoll):

    """ KobiQQ testing grounds """
    selectionDictonary = {'hunt':["Hunt","Bronze"],
                            'troll':["Troll","Bronze"],
                            'vm2':["vm2","Bronze"]}

    if arg in selectionDictonary:
        slotChances = selectionDictonary[arg][0]
        design      = selectionDictonary[arg][1]

    else:
        slotChances = "Bronze"
        design = "Bronze"

    removeFromWhisperDB(username)
    
    selectedGameDesign = getSlotGameDesign()

    eventList = []
    eventList.append("playSlot")

    varList = []
    slotVariableDict = {"rang":slotChances,"borderDesign":design,"number":slotRoll,"username":username,"selectedGameDesign":selectedGameDesign}
    varList.append(slotVariableDict)

    dict = {"eventList":eventList,"varList":varList} 

    core.socketEvent(Parent,json.dumps(dict))
    #Parent.BroadcastWsEvent("sendEvent", json.dumps(dict))

    return

#region Everything related to the settingfile. Unload() and Scripttoggle are not included - they are still in the loadsave setting Demo
def ReloadSettings(jsondata):

	"""	ReloadSettings is an optional function that gets called once the user clicks on
		the Save Settings button of the corresponding script in the scripts tab if an
		user interface has been created for said script. The entire Json object will be
		passed to the function	so you can load that back	into your settings without
		having to read the newly saved settings file.
	"""

	global ScriptSettings
	ScriptSettings.Reload(jsondata)

	return

def SetDefaults():

	""" SetDefaults Custom User Interface Button """
	global ScriptSettings

	ScriptSettings = thisScriptSettings()
	ScriptSettings.Save(SettingsFile)

	return
#endregion

def IsOnGlobalOrUserCooldown(data,username):
    """Return true if command is on cooldown and send cooldown message if enabled"""
    cooldown = Parent.IsOnCooldown(ScriptName, ScriptSettings.Command)
    userCooldown = Parent.IsOnUserCooldown(ScriptName, ScriptSettings.Command, data.User)
    
    if cooldown or userCooldown:

        if ScriptSettings.UseCD:
            cooldownDuration = Parent.GetCooldownDuration(ScriptName, ScriptSettings.Command)
            userCDD = Parent.GetUserCooldownDuration(ScriptName, ScriptSettings.Command, username)

            if cooldownDuration > userCDD:
                m_CooldownRemaining = cooldownDuration

                Parent.SendStreamWhisper(str(username),"Still on cooldown")

            else:
                m_CooldownRemaining = userCDD

                Parent.SendStreamWhisper(str(username),"Still on cooldown")

        return True

    Parent.AddUserCooldown(ScriptName, ScriptSettings.Command, data.User, ScriptSettings.UserCooldown)
    Parent.AddCooldown(ScriptName, ScriptSettings.Command, ScriptSettings.Cooldown)

    return False
