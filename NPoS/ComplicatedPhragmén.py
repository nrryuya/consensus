#from itertools import count
class edge:
    def __init__(self,voterid,canid):
        self.voterid=voterid
        self.canid=canid
        #self.index
        #self.voterindex
        #self.canindex
        

class voter:
    def __init__(self,votetuple):
        self.voterid=votetuple[0]
        self.budget=votetuple[1]
        self.edges=[edge(self.voterid,canid) for canid in votetuple[2]]
        #self.index

class candidate:
    def __init__(self,canid,index):
        self.canid = canid
        self.index=index


import itertools
class assignment:
    def __init__(self,voterlist,candidates, copyassignment=None):
        self.voterlist=voterlist
        self.candidates=candidates
        if copyassignment is None:
            #create edgelist here at cost O(votes size)
            self.edgelist = list(itertools.chain.from_iterable((nom.edges for nom in voterlist)))
            numvoters = len(voterlist)
            numcandidates = len(candidates)
            numedges=len(self.edgelist)
            self.voterload=[0.0 for x in range(numvoters)]
            self.edgeload = [0.0 for x in range(numedges)]
            self.edgeweight = [0.0 for x in range(numedges)]
            self.cansupport=[0.0 for x in range(numcandidates)]
            self.canelected=[False for x in range(numcandidates)]
            self.electedcandidates=set()
            self.canapproval= [0.0 for x in range(numcandidates)]
            #calculate approval here at cost O(numedges)
            for voter in voterlist:
                for edge in voter.edges:
                    self.canapproval[edge.canindex] += voter.budget
            self.canscore = [0.0 for x in range(numcandidates)]
        else:
            self.edgelist = copyassignment.edgelist
            self.voterload=copyassignment.voterload.copy()
            self.edgeload = copyassignment.edgeload.copy()
            self.edgeweight-copyassignment.edgeweight.copy()
            self.cansupport=copyassignment.cansupport.copy()
            self.canelected=copyassignment.caneelected.copy()
            self.electedcandidates=copyassignment.electedcandidates.copy()
            self.canapproval=copyassignment.canapproval.copy()
            self.canscore=copyassignment.canscores.copy()
    def setload(self, edge,load):
        oldload=self.edgeload[edge.index]
        self.edgeload[edge.index]=load
        self.voterload[edge.voterindex] +=load-oldload
    def setweight(self,edge,weight):
        oldweight=self.edgeweight[edge.index]
        self.edgeweight[edge.index]=weight
        self.cansupport[edge.canindex] +=weight-oldweight
    def setscore(self,candidate,score):
        self.canscore[candidate.index] = score
    def loadstoweights(self):
        for voter in self.voterlist:
            for edge in voter.edges:
                if(self.voterload[voter.index] > 0.0):
                    self.setweight(edge, voter.budget * self.edgeload[edge.index] / self.voterload[voter.index])
    def weightstoloads(self):
        for edge in self.edgelist:
            self.setload(edge, self.edgeweight[edge.index]/self.cansupport[edge.canindex])
    def elect(self,candidate):
        self.canelected[candidate.index]=True
        self.electedcandidates.add(candidate)
    def unelect(self,candidate):
        self.canelected[candidate.index]=False
        self.electedcandidates.remove(candidate)
    
def setuplists(votelist):
    #Instead of Python's dict here, you can use anything with O(log n) addition and lookup.
    #We can also use a hashmap, by generating a random constant r and useing H(canid+r)
    #since the naive thing is obviously attackable.
    voterlist = [voter(votetuple) for votetuple in votelist]
    candidatedict=dict()
    candidatearray=list()
    numcandidates=0
    numvoters=0
    numedges=0
    
    #Get an array of candidates that we can reference these by index
    for nom in voterlist:
        nom.index=numvoters
        numvoters+= 1
        for edge in nom.edges:
            edge.index=numedges
            edge.voterindex=nom.index
            numedges += 1
            canid = edge.canid
            if canid in candidatedict:
                edge.candidate=candidatearray[candidatedict[canid]]
                edge.canindex=edge.candidate.index
            else:
                candidatedict[canid]=numcandidates
                newcandidate=candidate(canid,numcandidates)
                candidatearray.append(newcandidate)
                edge.candidate=newcandidate
                edge.canindex=numcandidates
                numcandidates += 1
    return(voterlist,candidatearray)
    

def seqPhragmén(votelist,numtoelect):
    nomlist,candidates=setuplists(votelist)
    #creating an assignment now also computes the total possible stake for each candidate
    a=assignment(nomlist,candidates)
    
    for round in range(numtoelect):
        for canindex in range(len(candidates)):
            if not a.canelected[canindex]:
                a.canscore[canindex]=1/a.canapproval[canindex]
        for nom in a.voterlist:
            for edge in nom.edges:
                if not a.canelected[edge.canindex]:
                    a.canscore[edge.canindex] += nom.budget * a.voterload[nom.index] / a.canapproval[edge.canindex]
        bestcandidate=0
        bestscore = 1000 #should be infinite but I'm lazy
        for canindex in range(len(candidates)):
            if not a.canelected[canindex] and a.canscore[canindex] < bestscore:
                bestscore=a.canscore[canindex]
                bestcandidate=canindex
        electedcandidate=candidates[bestcandidate]
        a.canelected[bestcandidate]=True
        #electedcandidate.electedpos=round
        a.elect(electedcandidate)
        for nom in a.voterlist:
            for edge in nom.edges:
                if edge.canindex == bestcandidate:
                    a.setload(edge,a.canscore[bestcandidate]-a.voterload[nom.index])
    a.loadstoweights()
    return a

def approvalvoting(votelist,numtoelect):
    nomlist,candidates=setuplists(votelist)
    #creating an assignment now also computes the total possible stake for each candidate
    a=assignment(nomlist,candidates)

    candidatessorted=sorted(candidates, key = lambda x : a.canapproval[x.index], reverse=True)
    for candidate in candidatessorted[0:numtoelect]:
        a.elect(candidate)
    for nom in a.voterlist:
        numbelected=len([edge for edge in nom.edges if a.canelected[edge.canindex]])
        if (numbelected > 0):
            for edge in nom.edges:
                a.setweight(edge,nom.budget/numbelected)
    return a

def printresult(a,listvoters=True):
    for candidate in a.electedcandidates:
        print(candidate.canid," is elected with stake ",a.cansupport[candidate.index], "and score ",a.canscore[candidate.index])
    print()
    if listvoters:
        for nom in a.voterlist:
            print(nom.voterid," has load ",a.voterload[nom.index], "and supported ")
            for edge in nom.edges:
                print(edge.canid," with stake ",a.edgeweight[edge.index], end=" ")
            print()
    print("Minimum support ",min([a.cansupport[candidate.index] for candidate in a.electedcandidates]))
    print()

def equalise(a, nom, tolerance):
    # Attempts to redistribute the nominators budget between elected validators
    # Assumes that all elected validators have backedstake set correctly
    # returns the max difference in stakes between sup
    
    electededges=[edge for edge in nom.edges if a.canelected[edge.canindex]]
    if len(electededges)==0:
        return 0.0
    stakeused = sum([a.edgeweight[edge.index] for edge in electededges])
    backedstakes=[a.cansupport[edge.canindex] for edge in electededges]
    backingbackedstakes=[a.cansupport[edge.canindex] for edge in electededges if a.edgeweight[edge.index] > 0.0]
    if len(backingbackedstakes) > 0:
        difference = max(backingbackedstakes)-min(backedstakes)
        difference += nom.budget-stakeused
        if difference < tolerance:
            return difference
    else:
        difference = nom.budget
    #remove all backing
    for edge in nom.edges:
        a.setweight(edge, 0.0)
    electededges.sort(key=lambda x: a.cansupport[x.canindex])
    cumulativebackedstake=0
    lastcandidateindex=len(electededges)-1
    for i in range(len(electededges)):
        backedstake=a.cansupport[electededges[i].canindex]
        #print(nom.nomid,electededges[i].valiid,backedstake,cumulativebackedstake,i)
        if backedstake * i - cumulativebackedstake > nom.budget:
            lastcandidateindex=i-1
            break
        cumulativebackedstake +=backedstake
    laststake=a.cansupport[electededges[lastcandidateindex].canindex]
    waystosplit=lastcandidateindex+1
    excess = nom.budget + cumulativebackedstake -  laststake*waystosplit
    for edge in electededges[0:waystosplit]:
        a.setweight(edge,excess / waystosplit + laststake - a.cansupport[edge.canindex])
    return difference

import random
def equaliseall(a,maxiterations,tolerance):
    for i in range(maxiterations):
        for j in range(len(a.voterlist)):
            nom=random.choice(a.voterlist)
            equalise(a,nom,tolerance/10)
        maxdifference=0
        for nom in a.voterlist:
            difference=equalise(a,nom,tolerance/10)
            maxdifference=max(difference,maxdifference)
        if maxdifference < tolerance:
            return

def seqPhragménwithpostprocessing(votelist,numtoelect):
    a = seqPhragmén(votelist,numtoelect)
    equaliseall(a,1,0.1)
    return a

def maybecandidate(a,newcandidate,shouldremoveworst, testonly, tolerance):
    assert(a.canelected[candidate.index]==False)
    currentvalue=min([a.cansupport[candidate.index] for candidate in a.electedcandidates])
    #To find a new assignment without losing our current one, we will need to copy the edges
    b=assignment(a)
    if shouldremoveworst:
        worstcanidate =min(electedcandidates, key = lambda x: b.cansupport[x.index])
        b.unelect[worstcandidate]
    b.elect[newcandidate]
    equaliseall(b,100000000,0.1)
    newvalue=currentvalue=min([b.cansupport[candidate.index] for candidate in electedcandidates])
    if not (testonly or (shouldremoveworst and newvalue < currentvalue)):
        return b,newvalue
    a = b
    return a, newvalue

    

import unittest
class electiontests(unittest.TestCase):
    def testexample1Phragmén(self):
        votelist=[("A",10.0,["X","Y"]),("B",20.0,["X","Z"]),("C",30.0,["Y","Z"])]
        a = seqPhragmén(votelist,2)
        self.assertEqual({can.canid for can in a.electedcandidates},{"Y","Z"})
        self.assertAlmostEqual(a.canscore[2],0.02)
        self.assertAlmostEqual(a.canscore[1],0.04)
    def testexample1approval(self):
        votelist=[("A",10.0,["X","Y"]),("B",20.0,["X","Z"]),("C",30.0,["Y","Z"])]
        a = approvalvoting(votelist,2)
        self.assertEqual({can.canid for can in a.electedcandidates},{"Y","Z"})
        self.assertAlmostEqual(a.canapproval[2],50.0)
        self.assertAlmostEqual(a.canapproval[1],40.0)
def dotests():
    unittest.main()

def example1():
    votelist=[("A",10.0,["X","Y"]),("B",20.0,["X","Z"]),("C",30.0,["Y","Z"])]
    print("Votes ",votelist)
    a = seqPhragmén(votelist,2)
    print("Sequential Phragmén gives")
    printresult(a)
    a = approvalvoting(votelist,2)
    print()
    print("Approval voting gives")
    printresult(a)
    a = seqPhragménwithpostprocessing(votelist,2)
    print("Sequential Phragmén with post processing gives")
    printresult(a)

def example2():
    # Approval voting does not do so well for this kind of thing.
    votelist=[("A",30.0,["T", "U","V","W"]),("B",20.0,["X"]),("C",20.0,["Y"]),("D",20.0,["Z"])]
    print("Votes ",votelist)
    a = seqPhragmén(votelist,4)
    print("Sequential Phragmén gives")
    printresult(a)
    a = approvalvoting(votelist,4)
    print()
    print("Approval voting gives")
    printresult(a)
    a = seqPhragménwithpostprocessing(votelist,4)
    print("Sequential Phragmén with post processing gives")
    printresult(a)

def example3():
    #Proportional representation test.
    #Red should has 50% more votes than blue. So under PR, it would get 12/20 seats
    redparty=["Red"+str(i) for i in range(20)]
    blueparty=["Blue"+str(i) for i in range(20)]
    redvoters = [("RedV"+str(i),20.0,redparty) for i in range(30)]
    bluevoters = [("BlueV"+str(i),20.0,blueparty) for i in range(20)]
    votelist= redvoters+bluevoters
    #print("Votes ",votelist)
    a = seqPhragmén(votelist,20)
    print("Sequential Phragmén gives")
    printresult(a, listvoters=False)
    a = approvalvoting(votelist,20)
    print()
    print("Approval voting gives")
    printresult(a, listvoters=False)
    a = seqPhragménwithpostprocessing(votelist,20)
    print("Sequential Phragmén with post processing gives")
    printresult(a, listvoters=False)

def example4():
    #Now we want an example where seq Phragmén is not so good.
    votelist=[("A",30.0,["V","W"]),("B",20.0,["V","Y"]),("C",20.0,["W","Z"]),("D",20.0,["Z"])]
    print("Votes ",votelist)
    a = seqPhragmén(votelist,4)
    print("Sequential Phragmén gives")
    printresult(a)
    a = approvalvoting(votelist,4)
    print()
    print("Approval voting gives")
    printresult(a)
    a = seqPhragménwithpostprocessing(votelist,4)
    print("Sequential Phragmén with post processing gives")
    printresult(a)

def example5():
    votelist = [
		("10", 1000, ["10"]),
		("20", 1000, ["20"]),
		("30", 1000, ["30"]),
		("40", 1000, ["40"]),
		('2', 500, ['10', '20', '30']),
		('4', 500, ['10', '20', '40'])
	]
    print("Votes ",votelist)
    a = seqPhragmén(votelist,2)
    print("Sequential Phragmén gives")
    printresult(a)
    a = approvalvoting(votelist,4)
    print()
    print("Approval voting gives")
    printresult(a)
    a = seqPhragménwithpostprocessing(votelist,4)
    print("Sequential Phragmén with post processing gives")
    printresult(a)

def exampleLine():
    votelist = [
		("a", 2000, ["A"]),
		("b", 1000, ["A","B"]),
		("c", 1000, ["B","C"]),
		("d", 1000, ["C","D"]),
		("e", 1000, ["D","E"]),
		("f", 1000, ["E","F"]),
                ("g", 1000, ["F","G"])
	]
    print("Votes ",votelist)
    a = seqPhragmén(votelist,7)
    print("Sequential Phragmén gives")
    printresult(a)
    a = approvalvoting(votelist,7)
    print()
    print("Approval voting gives")
    printresult(a)
    a = seqPhragménwithpostprocessing(votelist,7)
    print("Sequential Phragmén with post processing gives")
    printresult(a)


    
    
            

    


    
            

    
        
        
        
            
            

                
        


            
    
    
    
    
    
