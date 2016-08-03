from funs import *
from ant import Ant
import time
import pickle
from os import path

dataM=readData('Input/solomon_r101.txt')
#for d in dataM:
#    print(d)
#    time.sleep(30)

txtFile=open('Output/DataM.txt','w')
for rec in dataM:
    txtFile.write(str(rec))
    txtFile.write('\n')
txtFile.close()

distM=createDistanceMatrix(dataM)

phiM1=createPheromoneMatix(size=len(distM),distance=1888)
feasLocIN1=len(distM)*[0]


vehicleNumber=60

ant0=Ant(vehicleCount=vehicleNumber,dataM=dataM)
bestSolution=ant0.calculate(dataM,distM,phiM1,feasLocIN1,1)

print('all done')

#iteration=0
#while iteration <200:
    
    #solution 1 is looking for a valid solution with fewer number of vehicles
#    ant1=Ant(vehicleCount=vehicleNumber-1,dataM=dataM)
#    solution1=ant1.calculate(dataM,distM,phiM1,feasLocIN1,1)
       

