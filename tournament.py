#heavily plagiarized from Hoogland's implementation
#sorry
import networkx as nx
import random
import csv
import os
import pprint
import operator

dbg = True
debuglevel = 1

class Tournament(object):
    def __init__( self, startingTable=1 ):
        #Will hold all player data
        self.playersDict = {}
        #Current round for the event
        self.currentRound = 0
        #The next table we are going to assign paired players to
        self.openTable = 0
        #The starting table number
        self.startingTable = startingTable
        #Pairings for the current round
        self.roundPairings = {}
        
        #this defines the max number of players in a network point range before we split it up. Lower the number, faster the calculations
        self.MaxGroup = 50 
        
        #Contains lists of players sorted by how many points they currently have
        self.pointLists = {}
        
        #Contains a list of points in the event from high to low
        self.pointTotals = []
        
        #Contains the list of tables that haven't reported for the current round
        self.tablesOut = []

    def addPlayer( self, IDNumber , playerName , runnerID, corpID ):
        self.playersDict[IDNumber] = {  "Name": playerName,
            "Opponents":[],
            "RunnerResults":[],
            "CorpResults":[],
            "Points":0,
            "OGW%": 0.0,
            "RunnerID":runnerID,
            "CorpID":corpID }

    def loadPlayersCSV( self, pathToLoad ):
        with open(pathToLoad) as csvfile:
            playerReader = csv.reader(csvfile, delimiter=',')
            for p in playerReader:
                #skip the row with headers
                if p[0] != 'ID:':
                    self.addPlayer( p[0] , p[1] ,  p[2] ,  p[3] )
                    
    def pairRound( self, forcePair=False ):
    # I haven't modified this at all
        """
        Process overview:
            1.) Create lists of players with each point value
            
            2.) Create a list of all current points and sort from highest to lowest
            
            3.) Loop through each list of points and assign players opponents based with same points
            
            4.) Check for left over players and assign a pair down
        """
        if not len(self.tablesOut) or forcePair:
            self.currentRound += 1
            
            #Clear old round pairings
            self.roundPairings = {}
            self.openTable = self.startingTable
            
            #Contains lists of players sorted by how many points they currently have
            self.pointLists = pointLists = {}
            
            #Contains a list of points in the event from high to low
            self.pointTotals = pointTotals = []
            
            #Counts our groupings for each point amount
            self.countPoints = {}
            
            #Add all players to pointLists
            for player in self.playersDict:
                info = self.playersDict[player]
                #If this point amount isn't in the list, add it
                if "%s_1"%info['Points'] not in pointLists:
                    pointLists["%s_1"%info['Points']] = []
                    self.countPoints[info['Points']] = 1
                
                #Breakers the players into groups of their current points up to the max group allowed.
                #Smaller groups mean faster calculations
                if len(pointLists["%s_%s"%(info['Points'], self.countPoints[info['Points']])]) > self.MaxGroup:
                    self.countPoints[info['Points']] += 1
                    pointLists["%s_%s"%(info['Points'], self.countPoints[info['Points']])] = []
                
                #Add our player to the correct group
                pointLists["%s_%s"%(info['Points'], self.countPoints[info['Points']])].append(player)
                
            #Add all points in use to pointTotals
            for points in pointLists:
                pointTotals.append(points)
                
            #Sort our point groups based on points
            pointTotals.sort(reverse=True, key=lambda s: int(s.split('_')[0]))
            
            printdbg( "Point totals after sorting high to low are: %s"%pointTotals, 3 )

            #Actually pair the players utilizing graph theory network
            for points in pointTotals:
                printdbg( points, 5 ) 
                
                #Create the graph object and add all players to it
                bracketGraph = nx.Graph()
                bracketGraph.add_nodes_from(pointLists[points])
                
                printdbg( pointLists[points], 5 )
                printdbg( bracketGraph.nodes(), 5 )
                
                #Create edges between all players in the graph who haven't already played
                for player in bracketGraph.nodes():
                    for opponent in bracketGraph.nodes():
                        if opponent not in self.playersDict[player]["Opponents"] and player != opponent:
                            #Weight edges randomly between 1 and 9 to ensure pairings are not always the same with the same list of players
                            wgt = random.randint(1, 9)
                            #If a player has more points, weigh them the highest so they get paired first
                            if self.playersDict[player]["Points"] > int(points.split('_')[0]) or self.playersDict[opponent]["Points"] > int(points.split('_')[0]):
                                wgt = 10
                            #Create edge
                            bracketGraph.add_edge(player, opponent, weight=wgt)
                
                #Generate pairings from the created graph
                pairings = nx.max_weight_matching(bracketGraph)
                
                printdbg( pairings, 3 )
                
                #Actually pair the players based on the matching we found
                for p in pairings:
                    if p in pointLists[points]:
                        self.pairPlayers(p, pairings[p])
                        pointLists[points].remove(p)
                        pointLists[points].remove(pairings[p])
                    
                #Check if we have an odd man out that we need to pair down
                if len(pointLists[points]) > 0:
                    #Check to make sure we aren't at the last player in the event
                    printdbg(  "Player %s left in %s. The index is %s and the length of totals is %s"%(pointLists[points][0], points, pointTotals.index(points), len(pointTotals)), 3)
                    if pointTotals.index(points) + 1 == len(pointTotals):
                        while len(pointLists[points]) > 0:
                            #If they are the last player give them a bye
                            self.assignBye(pointLists[points].pop(0))
                    else:
                        #Add our player to the next point group down
                        nextPoints = pointTotals[pointTotals.index(points) + 1]
                        
                        while len(pointLists[points]) > 0:
                            pointLists[nextPoints].append(pointLists[points].pop(0))
            
            #Return the pairings for this round
            return self.roundPairings
        else:
            #If there are still tables out and we haven't had a forced pairing, return the tables still "playing"
            return self.tablesOut
                
    def pairPlayers( self, p1, p2 ):
        print("Pairing players %s (%d) and %s (%d)"%(p1, to.playersDict[p1]["Points"], p2, to.playersDict[p2]["Points"]))
        
        self.playersDict[p1]["Opponents"].append(p2)
        self.playersDict[p2]["Opponents"].append(p1)
            
        self.roundPairings[self.openTable] = [p1, p2]
        self.tablesOut.append(self.openTable)
        
        self.openTable += 1

    def assignBye( self, p1, reason="bye" ):
        print( "%s got the bye"%p1)
        #this is changed from Hoogland - first digit is points from runner game
        #second digit is points from corp game
        
        self.playersDict[p1]["Opponents"].append("bye")
        
        #Add points for "winning"
        self.playersDict[p1]["Points"] += 4
        self.playersDict[p1]["RunnerResults"].append(2)
        self.playersDict[p1]["CorpResults"].append(2)        
    
    def reportMatch( self, table, result ):
        #table is an integer of the table number, result is a list
        p1 = self.roundPairings[table][0]
        p2 = self.roundPairings[table][1]
        
        #This is way easier to do with Netrunner actually
        #"result" format is
        # points for p1 from runner game (p2 corp game),
        # points for p1 from corp game (p2 runner game),
        # points for p2 from runner game
        # points for p2 from corp game
        self.playersDict[p1]["Points"] += result[0] + result[1]
        self.playersDict[p2]["Points"] += result[2] + result[3]
        
        self.playersDict[p1]["RunnerResults"].append(result[0])
        self.playersDict[p1]["CorpResults"].append(result[1])
               
        self.playersDict[p2]["RunnerResults"].append(result[2])
        self.playersDict[p2]["CorpResults"].append(result[3])       
      
        #Remove table reported from open tables
        self.tablesOut.remove(table)
        
        #When the last table reports, update tie breakers automatically
        if not len(self.tablesOut):
            self.calculateTieBreakers()
        
    def calculateTieBreakers( self ):
        for p in self.playersDict:
            opponentWinPercents = []
            #Loop through all opponents
            for opponent in self.playersDict[p]["Opponents"]:
                #Make sure it isn't a bye
                if opponent != "bye":
                    #Calculate win percent out to five decimal places, minimum of .33 per person (here replaced by 0.0)
                    winPercent = max(self.playersDict[opponent]["Points"] / float((len(self.playersDict[opponent]["Opponents"])*4)), 0.0)
                    printdbg( "%s contributed %s breakers"%(opponent, winPercent), 3)
                    opponentWinPercents.append(winPercent)
            
            #Make sure we have opponents
            if len(opponentWinPercents):
                self.playersDict[p]["OGW%"] = "%.5f" %(sum(opponentWinPercents) / float(len(opponentWinPercents)))

def printdbg( msg, level=1 ):
    if dbg == True and level <= debuglevel:
        print(msg)


##That's the code
##Tests follow
        
## Test
# Let's see if this works               
        
to = Tournament()

to.loadPlayersCSV("playerlist.csv")
pairings1 = to.pairRound()
print(pairings1)
        
for table in pairings1:
    if not type(pairings1[table]) is str:
        per = random.randint(1, 64)
        if per < 25:
            to.reportMatch(table, [2,0,0,2])
        elif per < 47:
            to.reportMatch(table, [2,2,0,0])
        elif per < 60:
            to.reportMatch(table, [0,0,2,2])
        else:
            to.reportMatch(table, [2,1,0,1])

pairings2 = to.pairRound()
print(pairings2)

for table in pairings2:
    if not type(pairings2[table]) is str:
        per = random.randint(1, 64)
        if per < 25:
            to.reportMatch(table, [2,0,0,2])
        elif per < 47:
            to.reportMatch(table, [2,2,0,0])
        elif per < 60:
            to.reportMatch(table, [0,0,2,2])
        else:
            to.reportMatch(table, [2,1,0,1])

pairings3 = to.pairRound()
print(pairings3)

for table in pairings3:
    if not type(pairings3[table]) is str:
        per = random.randint(1, 64)
        if per < 25:
            to.reportMatch(table, [2,0,0,2])
        elif per < 47:
            to.reportMatch(table, [2,2,0,0])
        elif per < 60:
            to.reportMatch(table, [0,0,2,2])
        else:
            to.reportMatch(table, [2,1,0,1])

pairings4 = to.pairRound()
print(pairings4)

for table in pairings4:
    if not type(pairings4[table]) is str:
        per = random.randint(1, 61)
        if per < 25:
            to.reportMatch(table, [2,0,0,2])
        elif per < 47:
            to.reportMatch(table, [2,2,0,0])
        elif per < 60:
            to.reportMatch(table, [0,0,2,2])
        else:
            to.reportMatch(table, [2,1,0,1])


print("")
print(to.playersDict["Al"])
print("")           

scoreList = to.playersDict.items()
scoreList = sorted(scoreList, key=lambda x: (x[1]["Points"], x[1]["OGW%"]), reverse=True)

for elem in scoreList:
    print (elem[0]+" "+str(elem[1]["Points"])+" "+str(elem[1]["OGW%"]))
    
#now the interesting challenge
#finding how each runner did

print("")

##YOU CAN THELL THIS IS MY CODE BECAUSE IT'S WRITTEN TWICE LOL

runnerList = []
corpList = []

for elem in scoreList:
    if elem[1]["RunnerID"] in runnerList:
        pass
    else:
        runnerList.append(elem[1]["RunnerID"])
    if elem[1]["CorpID"] in corpList:
        pass
    else:
        corpList.append(elem[1]["CorpID"])

for elem in runnerList:
    runnerCheck = elem
    numUsed = 0
    runnerPoints = 0
    for elem2 in scoreList:
        if elem2[1]["RunnerID"]==runnerCheck:
            numUsed+=1
            runnerPoints += sum(elem2[1]["RunnerResults"])
    print("%s played: %s"%(elem, numUsed))
    print("%s average points: %s"%(elem, runnerPoints/float(numUsed)))
    
print("")
    
for elem in corpList:
    corpCheck = elem
    numUsed = 0
    corpPoints = 0
    for elem2 in scoreList:
        if elem2[1]["CorpID"]==corpCheck:
            numUsed+=1
            corpPoints += sum(elem2[1]["CorpResults"])
    print("%s played: %s"%(elem, numUsed))
    print("%s average points: %s"%(elem, corpPoints/float(numUsed)))
    
print("")
    
##NEXT CHALLENGE: MATCHUPS
# Even just Shaper vs Jinteki

#Find each player who played Shaper
# Find each player they played against who played Jinteki
# Find the results of those matchups

#BUT! We have runnerList and corpList so we can check against those

#to.playersDict.items()
for runnerType in runnerList:
    for corpType in corpList:
        gamesTally = 0
        scoreTally = 0
        #keep a running tally of score of the matchup
        #should be an array obv
        for elem in scoreList:
            if elem[1]["RunnerID"] == runnerType: #this should change - it's just finding one runner
                #find everyone that person played
                #and find how they did
                for elem2 in elem[1]["Opponents"]:
                    if elem2 != "bye":
                        if to.playersDict[elem2]["CorpID"] == corpType:
                            #print (elem[1]["Name"] + " (" + elem[1]["RunnerID"] + ") versus " + elem2)
                            gamesTally += 1
                            gscore = elem[1]["RunnerResults"][elem[1]["Opponents"].index(elem2)]
                            scoreTally += gscore
                            #print(gscore)
        if gamesTally > 0:
            print ("%s versus %s games played: %s"%(runnerType, corpType, gamesTally))
            print ("%s versus %s points: %s"%(runnerType, corpType, scoreTally))
            print ("%s versus %s game win percent: %s"%(runnerType, corpType, scoreTally/float(2* gamesTally)))
    print ""