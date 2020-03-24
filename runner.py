# Developed by Jugen Gawande 
# This is a python script to solve Travelling Salesman Problem using an evolutionary optimization
# algorithm called Genetic Algorithm. 

import numpy as np
import random
import math
import pandas as pd

from os import system

import crossover
import mutation

from datetime import datetime
import logging
import configparser 
import matplotlib 
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sys
from time import process_time




CONFIG = configparser.ConfigParser()                                     
CONFIG.read('controller.ini')

#Controller Variables
data = CONFIG['DATASET']['FILE_NAME']
data_type_flag = CONFIG.getint('DATASET', 'DATASET_TYPE')
populationSize = CONFIG.getint('ALGORITHM', 'POP_SIZE')
mutationRate = CONFIG.getfloat('ALGORITHM', 'MUTATION_RATE')
genCount = CONFIG.getint('ALGORITHM', 'GEN_COUNT')
dead_count = CONFIG.getint('ALGORITHM', 'DEAD_COUNTER')


#Calculators
numberOfCities = 0
totalFitness = 0
genEvolved = 0

#Result Store
minDist = math.inf
bestRoute = []

#Data-plotting
fitness_curve = []
generation_fitness = pd.DataFrame(columns = np.arange(populationSize))

#Performance Measure
s_t = 0.0
e_t = 0.0


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    # Print iterations progress
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r{} {} |{}| {}% {} CURR_MIN_DIST={:.2f}'.format(prefix,iteration, bar, percent, suffix, minDist), end = printEnd )
    # Print New Line on Complete
    if iteration == total: 
        print("\n")


def addCity_using_coords():
    
    global numberOfCities, cityCoord,distanceMatrix, s_t, e_t

    s_t = process_time()

    temp_list = []
    try:
        with open(str(data_fname), "r") as f:
            for line in f:
                x, y = line.split()
                temp_list.append([float(x),float(y)])  #Convert to float for accuracy
            cityCoord = pd.DataFrame(temp_list, columns = ["x-coord", "y-coord"])       #Initiating pandas dataframe
        numberOfCities =  len(cityCoord) 
        if numberOfCities > 0:
            distanceMatrix = pd.DataFrame(columns = np.arange(numberOfCities))
            logger.info("Successfully added {cit} cities from data.".format(cit = numberOfCities))
    except:
        logger.warning("Dataset could not be loaded")
        sys.exit()
    #print(cityCoord, numberOfCities)
    

def addCity_using_dist():
    
    global distanceMatrix, numberOfCities, s_t, e_t
    s_t = process_time()
    temp_dist = []
    with open(str(data_fname), "r") as f:
        numberOfCities = int(f.readline())
        distanceMatrix = pd.DataFrame(columns = np.arange(numberOfCities))
    
        i = 0
        for line in f:
            for val in line.split():
                temp_dist.append(float(val))
                i += 1
                if i == numberOfCities:

                    i = 0
                    distanceMatrix.loc[len(distanceMatrix)] = temp_dist
                    temp_dist = [] 

    logger.info("Successfully added {cit} cities from data.".format(cit = numberOfCities))
    e_t = process_time()
    logger.info("CPU took {} to complete data loading and distance matrix building".format(e_t-s_t))


def generateDistMatrix():

    global distanceMatrix, s_t, e_t
    global numberOfCities
    
    for i in range(numberOfCities):
        temp_dist = []
        for j in range(numberOfCities):  #Generating entire matrix. Can be optimized by generating upward triangle matrix
            a = cityCoord.iloc[i].values 
            b = cityCoord.iloc[j].values   
            #Find Euclidean distance between points
            distance = np.linalg.norm(a-b)
            temp_dist.append(float(distance))   #Using python list comprehension for better performance

        distanceMatrix.loc[len(distanceMatrix)] = temp_dist

    e_t = process_time()
    logger.info("CPU took {} to complete data loading and distance matrix building".format(e_t-s_t))
    #print(distanceMatrix)
  

def generateInitPop():
    global numberOfCities, populationSize
    
    pop = [0]
    for i in range(numberOfCities):

        sort_dist = distanceMatrix.iloc[i]
        sort_dist = sort_dist.sort_values(ascending=True)
        

        for index, row in sort_dist.iteritems():
            if row == 0.0:
                continue
            
            if index in pop:
                continue
            else:
                pop.append(index)
                break 
    
    pop = np.asarray(pop)
    populationMatrix.loc[len(populationMatrix)] = pop
 
    for i in range(populationSize-1):
        np.random.shuffle(pop[1:])
        populationMatrix.loc[len(populationMatrix)] = pop

    logger.info("{} intial chromorsome populated".format(len(populationMatrix.index)))
    if (len(populationMatrix.index) == populationSize):
        
        logger.info("Initial population generated successfully\n")
        calculateFitness()


def matingPoolSelection():
    #Using Roulette wheel selection we will assign probabilities from 0-1 to 
    #each individual. The probability will determine how often we select a fit individual
    
    global totalFitness, fitnessMatrix

    index = 0
    r = random.random()

    while( r > 0):
        r = r - fitnessMatrix[index]
        index += 1 
    
    index -= 1

    return populationMatrix.iloc[index].values
    

def calculateFitness():
    global totalFitness, fitnessMatrix, minDist, fitness_curve, bestRoute, nextGenerationMatrix, generation_fitness

    fitness =[]
    for i,individual in populationMatrix.iterrows():
        distance = 0
        for j in range(len(individual)-1):
            #distance += calculateDistance(individual[j],individual[j+1])
            distance += distanceMatrix.iat[individual[j],individual[j+1]]
   
        fitness.append( 1 / distance )  #For routes with smaller distance to have highest fitness

        #Updating the best distance variable when a distance that is smaller than all
        #previous calculations is found
        
        if distance < minDist:
            minDist = distance
            bestRoute = np.copy(individual)
             
    
    fitness_curve.append(round(minDist, 2))
    fitnessMatrix = np.asarray(fitness)
    totalFitness = np.sum(fitnessMatrix)
    fitnessMatrix = np.divide(fitnessMatrix,totalFitness)   #Normalizing the fitness values between [0-1]
    generation_fitness.loc[len(generation_fitness)] = fitnessMatrix  
    nextGenerationMatrix.loc[len(nextGenerationMatrix)] = bestRoute     #Elitism, moving the fittest gene to the new generation as is
    nextGenerationMatrix.loc[len(nextGenerationMatrix)] = bestRoute 


def calculateDistance(loc_1, loc_2):
    return distanceMatrix.iat[loc_1,loc_2]


def mutateChild(gene):
    global mutationRate
    r = random.random()
    if r < mutationRate:
        return mutation.Twors(gene)

def nextGeneration():
    global nextGenerationMatrix, populationMatrix, genCount, bestRoute, dead_count, genEvolved,s_t, e_t

    counter = 0
    i=0
    end_point = dead_count
    printProgressBar(0, end_point, prefix = 'Generation:', suffix = 'Complete', length = 40)

    s_t = process_time()

    while(i < genCount):

        #_ = system('cls')  #refresh and clear terminal window
        m = minDist
        newGen = []

        while (len(newGen) < populationSize-2):
            parentA = matingPoolSelection()
            parentB = matingPoolSelection()    
            childA, childB = crossover.OC_Single(parentA, parentB)
            mutateChild(childA)
            mutateChild(childB)
            newGen.append(childA)
            newGen.append(childB)

       
        nextGenerationMatrix = nextGenerationMatrix.append(newGen[:populationSize-1])
        populationMatrix = nextGenerationMatrix.copy()
        nextGenerationMatrix = nextGenerationMatrix.iloc[0:0]
        calculateFitness()
    
        if(minDist == m):
            counter += 1 
        else:
            counter = 0
            end_point = i + dead_count 

        if (counter == dead_count):
            genEvolved = len(fitness_curve)
            logger.info("GENERATIONS EVOLVED={gen}".format(gen=i))
            e_t = process_time()
            logger.info("CPU execution time: {}".format(e_t-s_t))
            break 
        i+=1 
        printProgressBar(i, end_point , prefix = 'Generation:', suffix = 'Evolved', length = 40)
    #logger.info("GENERATIONS EVOLVED={gen}\n".format(gen=i))   #Enable if a stopping condition is maintained  



#Graphing
def graphing(): 
    global fitness_curve, genEvolved

    fig = plt.figure(figsize = (15,8))
    ax = fig.add_subplot(1, 1, 1)

    # decreasing time
    ax.set_xlabel('Generation', fontname="Calibri",fontweight="bold", fontsize=14)
    ax.set_ylabel('Distance', fontname="Calibri",fontweight="bold", fontsize=14)

    ax.spines['bottom'].set_color('#FFFAFF')
    ax.spines['left'].set_color('#FFFAFF')
    ax.spines['top'].set_color('#1B2533')
    ax.spines['right'].set_color('#1B2533')

    for axis in ['top','bottom','left','right']:
        ax.spines[axis].set_linewidth(1)

    ax.tick_params(axis='x', colors='#FFFAFF')
    ax.tick_params(axis='y', colors='#FFFAFF')

    ax.yaxis.label.set_color('#1B9AAA')
    ax.xaxis.label.set_color('#1B9AAA')
    ax.title.set_color('#EEC643')
    fig.set_facecolor('#1B2533')
    ax.set_facecolor('#1B2533')

    ax.grid(True,linewidth = 0.1)

    plt.title("Fitness Evolution Curve", loc='center' ,fontname="Calibri",fontweight="bold", fontsize=18)


    x = np.arange(genEvolved)
    y = fitness_curve

    x1 = [0]
    y1 = [fitness_curve[0]]
    for i in range(genEvolved-1):
        if fitness_curve[i] != fitness_curve[i+1]:
            y1.append(fitness_curve[i+1])
            x1.append(i+1)

    ax.scatter(x1,y1, color = "#F79824" )
    ax.plot(x,y, color = ("#CC3363"), linewidth = 2)
    #ax.barh(y1,x1, color = ("#DEF4C6"), height = 0.08, alpha = 0.2 )

    gap = int(genEvolved / 25)
    plt.xticks(np.arange(0, genEvolved, gap ))

    fig.text(0.8, 0.84, '[INFO]', color = '#86BBD8')
    fig.text(0.8, 0.8, 'MIN DIST={:.2f}'.format(minDist), color = '#F5F1E3')
    fig.text(0.8, 0.78, 'GEN EVOLVED={}'.format(genEvolved), color = '#F5F1E3')
    fig.text(0.8, 0.76, 'DATASET={}'.format(data), color = '#F5F1E3')
    fig.text(0.8, 0.74, 'POP SIZE={}'.format(populationSize), color = '#F5F1E3')
    fig.text(0.8, 0.72, 'MUT RATE={}'.format(mutationRate), color = '#F5F1E3')

    fig.text(0.62, 0.02, "TSP solved using Genetic Algorithm [Visualizer] {}".format(datetime.now()), color = '#86BBD8')

    logger.info("Fitness Curve generated")

    c=0.95
    x = 0.01
    for i in range(len(x1)):
        if(c < 0.1):
            c = 0.95
            x = 0.92
        fig.text(x,c,"[{}]{}".format(x1[i],y1[i]), fontsize=8, color = "#FAC9B8" )
        c-=0.02

    plt.subplots_adjust(left=0.15)

    """
    for i in range(len(x1)):
        ax.annotate("[{}]{}".format(x1[i],y1[i]), (x1[i], y1[i]), color='#FFFFFF', textcoords="offset points", xytext=(0,10))
    """
    hjhsda = "./logs/output_curve/G_{}_{}_{}.png".format(datetime.now().strftime("%d-%m-%y %H_%M"), data, minDist)
    fig.savefig("./logs/output_curve/G_{}.png".format(datetime.now().strftime("%d-%m-%y %H_%M")),facecolor=fig.get_facecolor(), edgecolor='none')
    logger.info("Fitness Curve exported to logs\nFile name: {}".format(hjhsda) )
    #plt.show()




#Data Logging
fname = "./logs/test_log/TSP_" + datetime.now().strftime("%d-%m-%y %H_%M") + "_" + data +"_"+ str(populationSize) + "_" + str(mutationRate) + ".log"

logger = logging.getLogger('tsp_ga')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(fname)
ch = logging.StreamHandler()
fh.setLevel(logging.INFO)
ch.setLevel(logging.INFO)

logger.addHandler(fh)
logger.addHandler(ch)


logger.info("TSP USING Genetic Algorithm\nDeveloped by Jugen Gawande")
logger.info(str(datetime.now()))
logger.info("\nPOPULATION SIZE={pop} \nMUTATION RATE={mut} \nDATASET SELECTED={name}\n".format(pop =populationSize, mut = mutationRate, name = data))


data_fname = "./dataset/" + data + ".txt"   #Select data file to use

if data_type_flag == 0:
    addCity_using_coords()
else:
    addCity_using_dist()

#Initialize pandas dataframes

populationMatrix = pd.DataFrame(columns=np.arange(numberOfCities))
nextGenerationMatrix = pd.DataFrame(columns=np.arange(numberOfCities))


#Run Genetic Algorithm
if distanceMatrix.empty == True:
    generateDistMatrix()
generateInitPop()
nextGeneration()


logger.info("MINIMAL DISTANCE={}".format(minDist))
logger.info("BEST ROUTE FOUND={}".format(bestRoute))
logger.info("\nAlgorithm Completed Successfully.")
logger.info("FITNESS CURVE:\n{}".format(fitness_curve[:genEvolved - dead_count + 1]))   #Will fail if all generations are exhausted



with open("./logs/visualize_data.txt", "w") as f:
    f.write(" ".join(str(item) for item in fitness_curve))
    f.write("\n")

rname = "./logs/test_{}.csv".format(data)

try:
    with open(rname, "r") as f:
        for index, l in enumerate(f):
            pass
except:
    index = -1

with open(rname, "a") as f:
    f.write("Test {}, {}, {}, {}, {}, {}, {:.2f}\n".format(index+2 ,datetime.now(),CONFIG['OPERATOR']['CROSSOVER_OPERATOR'],CONFIG['OPERATOR']['MUTATION_OPERATOR'], populationSize, mutationRate, minDist ))

logger.info("Test results recorded.")
logger.info("Visualization Data Generated")

generation_fitness = generation_fitness.round(5)
generation_fitness.to_csv("./logs/curve_log/GenFit_data_{}.csv".format(datetime.now().strftime("%d-%m-%y %H_%M")), header=None, index=None, sep=',', mode='a')
generation_fitness.to_csv('./logs/visualize_data.txt', header=None, index=None, sep=' ', mode='a')

graphing()
