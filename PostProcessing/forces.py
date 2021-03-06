"""
Analyze forces dumped with LAMMPS: 
*   Plot forces of empirical potential that is reproduced and 
    NN forces as function of time step to compare
    (both real simulations and pseudo-simulations)
*   Calculate various error estimates
*   Check that sum of forces is zero



"""

import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler

import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandParentDir = os.path.dirname(parentdir)
gGrandParentDir = os.path.dirname(grandParentDir)
sys.path.insert(0, parentdir) 
sys.path.insert(1, grandParentDir)
sys.path.insert(2, gGrandParentDir)

import TensorFlow.DataGeneration.readers as readers
import TensorFlow.Tools.matplotlibParameters as pltParams


def readForceFile(filename):
   
    with open(filename, 'r') as infile:
        
        force = False  
        timeStep = False                    
        forces = []
        timeSteps = []
        
        # read number of atoms and first time step
        infile.readline()
        timeSteps.append(int(infile.readline()))
        
        infile.readline()
        numberOfAtoms = int(infile.readline())
        print "Number of atoms: ", numberOfAtoms
      
        i = 0
        for line in infile:
            words = line.split()
            
            if words[-1] == 'TIMESTEP':
                timeStep = True
                continue
                
            if words[-1] == 'fz':
                force = True
                continue
            
            if timeStep:
                timeSteps.append(int(words[0]))
                timeStep = False
                continue
                
            if force:
                i += 1
                forcei = []
                forcei.append(float(words[1]))
                forcei.append(float(words[2]))
                forcei.append(float(words[3]))
                forces.append(forcei)
                if i == numberOfAtoms:
                    i = 0
                    force = False 
           
    return np.array(timeSteps), np.array(forces), numberOfAtoms


def readTau(filename, atom):
    
    with open(filename, 'r') as infile:
        
        tau = []
        for line in infile:
            words = line.split()
            tau.append(int(words[atom]))
     
    return np.array(tau)
    
    
def readStep(filename, atom):
    
    with open(filename, 'r') as infile:
        
        steps = []
        for line in infile:
            words = line.split()
            if int(words[0]) == atom:
                steps.append(int(words[1]))
                                 
    return np.array(steps)
               
               
def writeNeighbourData(filename, x, y, z, r, E, types=None):
    
    print 'Writing to file:', filename
    
    with open(filename, 'w') as outfile:
        
        for i in xrange(len(x)):
            for j in xrange(len(x[i])):
                if types is not None:
                    outStr = '%.16g %.16g %.16g %.16g %d ' % (x[i][j], y[i][j], z[i][j], r[i][j], types[i][j])
                else:
                    outStr = '%.16g %.16g %.16g %.16g ' % (x[i][j], y[i][j], z[i][j], r[i][j])
                outfile.write(outStr)
            outfile.write('%.16g' % E[i][0])
            outfile.write('\n')
                
        
        
        

class AnalyzeForces:
    
    def __init__(self, dirNameNN='', dirNameTarget='', neighbourFile='', chosenAtom=0):
                     
        if dirNameNN and dirNameTarget:
            
            # write out README files
            print "Content of SW folder:"
            os.system('cat ' + dirNameTarget + 'README.txt')
            print "Content of NN folder:"
            os.system('cat ' + dirNameNN + 'README.txt')
            
            # read all forces in force file
            timeStepsNN, self.forcesNN, numberOfAtomsNN = readForceFile(dirNameNN + 'forces.txt')
            timeStepsTarget, self.forcesTarget, numberOfAtomsTarget = readForceFile(dirNameTarget + 'forces.txt')
            #assert(numberOfAtomsNN == numberOfAtomsTarget)
            self.numberOfAtoms = numberOfAtomsNN
            
            # check that time step arrays of SW and NN are equal
            if not np.array_equal(timeStepsNN, timeStepsTarget):
                print 'Forces for NN and SW must be sampled for the same time steps'
                exit(1)
            else:
                self.timeSteps = timeStepsNN    
            
            self.nTimeSteps = len(self.timeSteps)
            print "Number of time steps: ", self.nTimeSteps
            
            self.chosenAtom = chosenAtom
            print "Chosen atom: ", chosenAtom
            
            self.initializeForces()
            
        if dirNameTarget and not dirNameNN:
            
            timeStepsTarget, self.forcesTarget, numberOfAtomsTarget = readForceFile(dirNameTarget + 'forces.txt')
                        
            self.timeSteps = timeStepsTarget
            self.nTimeSteps = len(self.timeSteps)
            print "Number of time steps: ", self.nTimeSteps
            
            self.numberOfAtoms = numberOfAtomsTarget
            
            self.chosenAtom = chosenAtom
            print "Chosen atom: ", chosenAtom
            
            self.initializeForcesTarget()
            
        if neighbourFile:
            
            self.x, self.y, self.z, self.r, _ = readers.readNeighbourData(neighbourFile)
            
    
    def initializeForces(self):
        
        numberOfAtoms   = self.numberOfAtoms
        forcesNN        = self.forcesNN
        forcesTarget    = self.forcesTarget
        chosenAtom      = self.chosenAtom
                  
        # access components
        FxNNTot = forcesNN[:,0]
        FyNNTot = forcesNN[:,1]
        FzNNTot = forcesNN[:,2]
        
        FxTargetTot = forcesTarget[:,0]
        FyTargetTot = forcesTarget[:,1]
        FzTargetTot = forcesTarget[:,2]
        
        FxNN = FxNNTot[np.arange(chosenAtom, len(FxNNTot), numberOfAtoms)]
        FyNN = FyNNTot[np.arange(chosenAtom, len(FyNNTot), numberOfAtoms)]
        FzNN = FzNNTot[np.arange(chosenAtom, len(FzNNTot), numberOfAtoms)]
        FxTarget = FxTargetTot[np.arange(chosenAtom, len(FxTargetTot), numberOfAtoms)]
        FyTarget = FyTargetTot[np.arange(chosenAtom, len(FyTargetTot), numberOfAtoms)]
        FzTarget = FzTargetTot[np.arange(chosenAtom, len(FzTargetTot), numberOfAtoms)]
        
        Fnn = np.sqrt(FxNN**2 + FyNN**2 + FzNN**2)
        Ftarget = np.sqrt(FxTarget**2 + FyTarget**2 + FzTarget**2)
        
        self.FxNNTot        = FxNNTot
        self.FyNNTot        = FyNNTot
        self.FzNNTot        = FzNNTot
        self.FxTargetTot    = FxTargetTot
        self.FyTargetTot    = FyTargetTot
        self.FzTargetTot    = FzTargetTot        
        self.FxNN           = FxNN
        self.FyNN           = FyNN
        self.FzNN           = FzNN
        self.FxTarget       = FxTarget
        self.FyTarget       = FyTarget
        self.FzTarget       = FzTarget
        self.Fnn            = Fnn
        self.Ftarget        = Ftarget
        
    def initializeForcesTarget(self):
        
        numberOfAtoms   = self.numberOfAtoms
        forcesTarget    = self.forcesTarget
        chosenAtom      = self.chosenAtom
                  
        # access components      
        FxTargetTot = forcesTarget[:,0]
        FyTargetTot = forcesTarget[:,1]
        FzTargetTot = forcesTarget[:,2]
        
        FxTarget = FxTargetTot[np.arange(chosenAtom, len(FxTargetTot), numberOfAtoms)]
        FyTarget = FyTargetTot[np.arange(chosenAtom, len(FyTargetTot), numberOfAtoms)]
        FzTarget = FzTargetTot[np.arange(chosenAtom, len(FzTargetTot), numberOfAtoms)]
        
        Ftarget = np.sqrt(FxTarget**2 + FyTarget**2 + FzTarget**2)
        
        self.FxTargetTot    = FxTargetTot
        self.FyTargetTot    = FyTargetTot
        self.FzTargetTot    = FzTargetTot        
        self.FxTarget       = FxTarget
        self.FyTarget       = FyTarget
        self.FzTarget       = FzTarget
        self.Ftarget        = Ftarget
        
    
    def sumOfForces(self):
        
        nTimeSteps = self.nTimeSteps
        numberOfAtoms = self.numberOfAtoms
            
        # check that sum of forces is zero
        sumsNN = np.zeros((nTimeSteps, 3))
        sumsTarget = np.zeros((nTimeSteps, 3))
        for i in xrange(nTimeSteps):
            timeStep = numberOfAtoms*i
            sumsNN[i][0] = np.sum(self.FxNNTot[timeStep:timeStep+numberOfAtoms])
            sumsNN[i][1] = np.sum(self.FyNNTot[timeStep:timeStep+numberOfAtoms])
            sumsNN[i][2] = np.sum(self.FzNNTot[timeStep:timeStep+numberOfAtoms])
            sumsTarget[i][0] = np.sum(self.FxTargetTot[timeStep:timeStep+numberOfAtoms])
            sumsTarget[i][1] = np.sum(self.FyTargetTot[timeStep:timeStep+numberOfAtoms])
            sumsTarget[i][2] = np.sum(self.FzTargetTot[timeStep:timeStep+numberOfAtoms])
            
        if (sumsNN > 1e-4).any():
            print "Sum of forces is not zero"
            
        print "Max sum-of-forces NN: ", np.max(sumsNN)
        print "Max sum-of-forces target: ", np.max(sumsTarget)
        
               
    
    def forceError(self, plotErrorVsF=True, plotError=True):
                       
        FxNN        = self.FxNN
        FyNN        = self.FyNN
        FzNN        = self.FzNN
        FxTarget    = self.FxTarget
        FyTarget    = self.FyTarget
        FzTarget    = self.FzTarget
        Fnn         = self.Fnn
        Ftarget     = self.Ftarget
        timeSteps   = self.timeSteps
                
        xError = FxNN - FxTarget
        yError = FyNN - FyTarget
        zError = FzNN - FzTarget
        absError = Fnn - Ftarget
        squareError = (Fnn - Ftarget)**2
        self.absError = absError
           
        # plot error vs |F|
        if plotErrorVsF:
            errorVsForce = []
            forceValues = np.linspace(0, np.max(Fnn), 10)
            binCenters  = (forceValues[1:] + forceValues[:-1]) / 2.0
            for i in xrange(len(forceValues)-1):
                interval = np.where(Fnn < forceValues[i+1])[0]
                #errorVsForce.append(np.std(absError[interval]))
                errorVsForce.append(np.sqrt(np.sum(squareError[interval])/len(interval)))
            plt.figure()
            plt.plot(binCenters, errorVsForce, 'bo--')
            plt.xlabel(r'$F_{\mathrm{NN}} \; [\mathrm{eV/\AA{}}]$')
            plt.ylabel('RMSE')
            plt.tight_layout()
            plt.savefig('../../Oppgaven/Figures/Results/SiForces.pdf')
            plt.draw()
            raw_input('Press to continue: ')
            
        plt.figure()
        plt.hist(Fnn, bins=30)
        plt.draw()
        raw_input('Press to continue: ')
        
        # output
        print "Average error Fx: ", np.average(xError)
        print "Average error Fy: ", np.average(yError)
        print "Average error Fz: ", np.average(zError)
        print "Average error |F|: ", np.average(absError)
        print
        print "RMSE Fx: ", np.sqrt( np.average(xError**2) )
        print "RMSE Fy: ", np.sqrt( np.average(yError**2) )
        print "RMSE Fz: ", np.sqrt( np.average(zError**2) )
        print "RMSE |F|: ", np.sqrt( np.average(absError**2) )
        print "RMSE |F|: ", np.sqrt(np.sum(squareError)/len(Fnn))
        print 
        print "Std. dev. error Fx: ", np.std(xError)
        print "Std. dev. error Fy: ", np.std(yError)
        print "Std. dev. error Fz: ", np.std(zError)
        print "Std. dev. error |F|: ", np.std(absError)
        
        # plot NN and SW forces plus the errors
        if plotError:
            plt.subplot(4,2,1)
            plt.plot(timeSteps, FxNN, 'b-', timeSteps, FxTarget, 'g-')
            plt.legend([r'$F_x^{NN}$', r'$F_x^{SW}$'])
            
            plt.subplot(4,2,3)
            plt.plot(timeSteps, FyNN, 'b-', timeSteps, FyTarget, 'g-')
            plt.legend([r'$F_y^{NN}$', r'$F_y^{SW}$'])   
            
            plt.subplot(4,2,5)        
            plt.plot(timeSteps, FzNN, 'b-', timeSteps, FzTarget, 'g-')
            plt.legend([r'$F_z^{NN}$', r'$F_z^{SW}$'])
            
            plt.subplot(4,2,7)       
            plt.plot(timeSteps, Fnn, 'b-', timeSteps, Ftarget, 'g-')
            plt.xlabel('Timestep')
            plt.legend([r'$|F|^{NN}$', r'$|F|^{SW}$'])
            
            plt.subplot(4,2,2)
            plt.plot(timeSteps, xError)
            plt.ylabel(r'$\Delta F_x$')
            
            plt.subplot(4,2,4)
            plt.plot(timeSteps, yError)
            plt.ylabel(r'$\Delta F_y$')     
            
            plt.subplot(4,2,6)        
            plt.plot(timeSteps, zError)
            plt.ylabel(r'$\Delta F_z$')
            
            plt.subplot(4,2,8)       
            plt.plot(timeSteps, absError)
            plt.xlabel('Timestep')
            plt.ylabel(r'$\Delta F$')
            
            plt.draw()
            raw_input('Press to continue: ')
            
    
    def visualizeSampling(self, tauFile='', stepFile='', plotHist=True, plotForceVsTime=True,
                          nBins=10, chosenID=None):
        
        timeSteps   = self.timeSteps
        Ftarget     = self.Ftarget
        chosenAtom  = self.chosenAtom
        
        # plot tau
        if tauFile:
            tau = readTau(tauFile, chosenAtom)
            
        if plotHist:
            n, bins, patches = plt.hist(Ftarget, nBins)
            plt.xlabel('|F|')
            plt.ylabel('Number of forces')
            plt.legend(['Without sampling algorithm'])
            plt.draw()
            raw_input('Press to continue: ')
            
            # get indicies where sampled
            if stepFile:
                if chosenID is not None:
                    steps = readStep(stepFile, chosenID)
                else:
                    steps = readStep(stepFile, chosenAtom)

                # plot distribution of forces with sampling algorithm               
                n2, bins, patches = plt.hist(Ftarget[steps], nBins)
                plt.xlabel('|F|')
                plt.ylabel('Number of forces')
                plt.legend(['With sampling algorithm'])
                plt.draw()
                raw_input('Press to continue: ')
                
                binCenters = (bins[1:] + bins[:-1]) / 2
                plt.plot(binCenters, n/max(n), ls='steps') 
                plt.plot(binCenters, n2/max(n2), ls='steps', linewidth=2)
                plt.legend(['Without sampling algorithm', 'With sampling algorithm'], prop={'size':15})
                #plt.title('Normed')
                plt.xlabel(r'$F_i \, [\mathrm{eV}/\mathrm{\AA{}}]$')
                plt.ylabel('Normalized force counts')
                plt.tight_layout()
                plt.savefig('tmp/forceDistSamplingAlgoNormed.pdf')
                #plt.draw()
                raw_input('Press to continue: ')
            
                plt.plot(binCenters, n, ls='steps') 
                plt.plot(binCenters, n2, ls='steps', linewidth=2)
                plt.legend(['Without sampling algorithm', 'With sampling algorithm'], prop={'size':15})
                #plt.title('Not normed')
                plt.xlabel(r'$F_i \, [\mathrm{eV}/\mathrm{\AA{}}]$')
                plt.ylabel('Force counts')
                plt.tight_layout()
                plt.savefig('tmp/forceDistSamplingAlgo.pdf')
                #plt.draw()
                raw_input('Press to continue: ')
                
        if plotForceVsTime:
            if tauFile:
                plt.plot(timeSteps, Ftarget, 'b-', timeSteps, tau, 'g-')
                plt.legend(['|F|', 'tau type %d' % chosenAtom])
                plt.xlabel('Time step')
                plt.draw()
                raw_input('Press to continue: ')
            else:
                plt.plot(timeSteps, Ftarget, 'b-')
                plt.xlabel('Time step')
                plt.ylabel('|F|')     
                plt.draw()
                raw_input('Press to continue: ')
            
        print "Average |F|: ",   np.mean(Ftarget)
        print "Max |F|: ",       np.max(Ftarget)
        print "Min |F|: ",       np.min(Ftarget)
        print "Std. dev. |F|: ", np.std(Ftarget)
        print "Counts: ", n
        
        if stepFile:
            # update class member
            self.Ftarget = Ftarget[steps]
            
            print
            print "With sampling algo:"
            print "Average |F|: ",   np.mean(self.Ftarget)
            print "Max |F|: ",       np.max(self.Ftarget)
            print "Min |F|: ",       np.min(self.Ftarget)
            print "Std. dev. |F|: ", np.std(self.Ftarget)
            print "Counts: ", n2
        
    
    def transformDistribution(self, nBins=7, write=False, neighbourDir=''):
        
        Ftarget = self.Ftarget
        chosenAtom = self.chosenAtom

        n, bins, patches = plt.hist(Ftarget, nBins, fill=False)
        n = np.array(n)
        nMin = n[-4]
        deletes = n - nMin
        indiciesDeleted = []
        for i in xrange(len(n)):
            indicies = np.where(((Ftarget > bins[i]) & (Ftarget <= bins[i+1])))[0]
            if len(indicies) > nMin:
                indicies2 = np.random.choice(indicies, int(deletes[i]), replace=False).tolist()
                indiciesDeleted.append(indicies2)
            
        indiciesDeleted = [item for sublist in indiciesDeleted for item in sublist]
        Ftarget = np.delete(Ftarget, indiciesDeleted)
        
        print 'Number of deleted neighbour lists: ', len(indiciesDeleted)        
        
        n2, bins2, patches2 = plt.hist(Ftarget, nBins, fill=False)
        plt.draw()
        raw_input('Press to continue: ')
        
        binCenters = (bins[1:] + bins[:-1])/2
        
        plt.figure()
        plt.plot(binCenters, n, ls='steps')
        plt.plot(binCenters, n2, ls='steps')
        plt.draw()
        raw_input('Press to continue: ')
        
        print
        print "After tranformation:"
        print "Average |F|: ",   np.mean(Ftarget)
        print "Max |F|: ",       np.max(Ftarget)
        print "Min |F|: ",       np.min(Ftarget)
        print "Std. dev. |F|: ", np.std(Ftarget)
        print "Counts: ", n2
        
        # make new stripped data set
        if write:
            neighbourFile = neighbourDir + '/neighbours%d.txt' % chosenAtom
            print 'Reading data file', neighbourFile
            x, y, z, r, types, E = readers.readNeighbourDataMultiType(neighbourFile)
            
            x     = np.delete(x, indiciesDeleted, axis=0)
            y     = np.delete(y, indiciesDeleted, axis=0)
            z     = np.delete(z, indiciesDeleted, axis=0)
            r     = np.delete(r, indiciesDeleted, axis=0)
            types = np.delete(types, indiciesDeleted, axis=0)
            E     = np.delete(E, indiciesDeleted, axis=0)
            
            writeName = neighbourDir + '/neighbours%dFlattened.txt' % chosenAtom
            writeNeighbourData(writeName, x, y, z, r, E, types=types)
    
        

    def distAndCoords(self, plotDistFlag=True, plotCoordsFlag=True):
    
        # calculate various properties of the chemical environment of the 
        # chosen atom as a function of time step
        # read neighbour file
    
        timeSteps = self.timeSteps
        r = self.r
    
        rAverage = np.zeros(len(r))
        rMax = np.zeros(len(r))
        rMin = np.zeros(len(r))
        rStd = np.zeros(len(r))
        coordNumber = np.zeros(len(r))
        for i in xrange(len(r)):
            ri = np.sqrt(np.array(r[i]))
            rAverage[i] = np.average(ri)
            rMax[i] = np.max(ri)
            rMin[i] = np.min(ri)
            rStd[i] = np.std(ri)
            coordNumber[i] = len(ri)
            
        if plotDistFlag:    
            # plots of environment variables
            plt.subplot(4,1,1)
            plt.plot(rAverage)
            plt.legend(['rAverage'])
            plt.subplot(4,1,2)
            plt.plot(rMax)
            plt.legend(['rMax'])
            plt.subplot(4,1,3)
            plt.plot(rMin)
            plt.legend(['rMin'])
            plt.subplot(4,1,4)
            plt.plot(rStd)
            plt.legend(['rStd'])
            plt.show()  
            #plt.savefig('tmp/dist.pdf')
            
        if plotCoordsFlag:
            plt.figure()
            plt.plot(timeSteps[0::10], coordNumber)
            plt.xlabel('Time step')
            plt.ylabel('Coordination number')
            plt.show()
            
            # correlations with coordination number
            coordUnique = np.unique(coordNumber)
            print "Coordination numbers: ", coordUnique
            plt.figure()
            plt.hist(coordNumber, bins=4)
            plt.legend(['Coordination numbers'])
        
            # find error as function of coordination number
            errorVsCoords = []
            for coord in coordUnique:
                indicies = np.where(coordNumber == coord)[0]
                errorVsCoords.append(np.std(self.absError[indicies]))
                
            plt.figure()
            plt.plot(coordUnique, errorVsCoords) 
            plt.xlabel('Coordination number')
            plt.ylabel('Error')
            plt.show()
   
   
##### main #####   
   
# interactive plot session (to avoid freezing of second plot)
plt.ion() 

pltParams.defineColormap(6, plt.cm.jet)

# read force files
dirNameNN       = '../TestNN/Data/Si/Forces/L3T300N3000PseudoFinal/'
dirNameTarget   = '../Silicon/Data/Forces/L3T300N3000/'

nTypes = 1

# SiO2
if nTypes > 1:
    alpha1 = 3.0
    alpha2 = 1.5
    
    tauFile         = '../Quartz/tmp/1e4tau%1.1f-%1.1f.txt' % (alpha1, alpha2)
    stepFile        = '../Quartz/tmp/1e4step%1.1f-%1.1f.txt' % (alpha1, alpha2)
    
    neighbourDir   = '../Quartz/Data/TrainingData/Bulk/L4T1000N1e4Algo'
    
# Si
else:
    alpha = 3.0
    
    tauFile         = '../Silicon/tmp/1e4tau%1.1f.txt' % (alpha)
    stepFile        = '../Silicon/tmp/1e4step%1.1f.txt' % (alpha)
    
    neighbourDir   = '../Silicon/Data/TrainingData/Bulk/L4T1000N2000'

# set chosenID if chosenAtom value does not correspond to atom ID
# chosenAtom should be the first atom whose tau is written out in case of multitype
# chosenID is the LAMMPS id of the atom we want to plot force distribution for
chosenAtom = 100
chosenID = 10
#chosenID = None

includeNN = True

if includeNN:
    analyze = AnalyzeForces(dirNameNN=dirNameNN, dirNameTarget=dirNameTarget, chosenAtom=chosenAtom)
    analyze.sumOfForces()
    analyze.forceError()
else: 
    analyze = AnalyzeForces(dirNameTarget=dirNameTarget, chosenAtom=chosenAtom)
    analyze.visualizeSampling(stepFile=stepFile, 
                              tauFile=tauFile, 
                              plotHist=True, nBins=7,
                              plotForceVsTime=False, 
                              chosenID=chosenID)
    #analyze.transformDistribution(nBins=7, write=False, neighbourDir=neighbourDir)
              












