import numpy as np
import matplotlib.pyplot as plt


def readFile(filename):
    
    with open(filename, 'r') as infile:
        
        # skip two comment lines
        infile.readline()
        infile.readline()
        
        temperature = []
        kineticEnergy = []
        potentialEnergy = []
        pressure = []
        for line in infile:
            words = line.split()
            temperature.append(float(words[1]))
            kineticEnergy.append(float(words[2]))
            potentialEnergy.append(float(words[3]))
            pressure.append(float(words[4]))
            
    temperature = np.array(temperature)
    kineticEnergy = np.array(kineticEnergy)
    potentialEnergy = np.array(potentialEnergy)
    pressure = np.array(pressure)
    
    return temperature, kineticEnergy, potentialEnergy, pressure
    

tempNN, kinNN, potNN, pressNN = readFile('../TestNN/Data/Thermo/16.03-15.29.28/thermo.txt')
tempSW, kinSW, potSW, pressSW = readFile('../Silicon/Data/Thermo/thermo.txt')

totalEnergyNN = kinNN + potNN
totalEnergySW = kinSW + potSW

# compute averages
#aveTempNN = np.sum(tempNN) / 

plt.subplot(2,2,1)
plt.plot(tempNN, 'b-', tempSW, 'g-')
plt.subplot(2,2,2)
plt.plot(kinNN, 'b-', kinSW, 'g-')
plt.subplot(2,2,3)
plt.plot(potNN, 'b-', potSW, 'g-')
plt.subplot(2,2,4)
plt.plot(totalEnergyNN, 'b-', totalEnergySW, 'g-')
plt.show()
