import numpy as np
from gwemlightcurves.KNModels import table
import gwemlightcurves.EjectaFits.DiUj2017 as du
from gwemlightcurves.KNModels.io.DiUj2017 import calc_lc
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import random
import sys
from threading import Thread
import h5py
import pandas as pd

#creates lightcurve dataframes from input data using the Dietrich Ujevic 2017 model codebase from the gwemlightcurves python package
#to make with other models similair programmes to this one can be made using different parts of the gwemlightcurve package.

def Generate_LightCurve(m1,m2,l1,l2,plot = False):
    """A function to generate lightcurves based off of the two apparent masses of the neutron stars and their tidal deformabilities.
            -m1,m2,l1,l2: Float inputs
            -plot: boolean for whether or not to plot the generated lightcurves
    """
    #initial parameters for the lightcurve
    tini = 0
    tmax = 11
    dt = 0.01
    kappa = 10
    eps = 1.58e10
    alp = 1.2
    eth = 0.5

    vmin = 0.02

    #calculate c1 and c2 from l1,l2
    c1 = table.CLove(l1) #Compactness-Love relation for neutron stars
    c2 = table.CLove(l2)
    
    #calculate M_ej
    mb1 = table.EOSfit(m1,c1)
    mb2 = table.EOSfit(m2,c2)
    mej = du.calc_meje(m1,mb1,c1,m2,mb2,c2)

    #calculate v_ej
    v_rho = du.calc_vrho(m1,c1,m2,c2)
    v_z = du.calc_vz(m1,c1,m2,c2)
    vej = du.calc_vej(m1,c1,m2,c2)

    #calculate angles
    th = du.calc_qej(m1,c1,m2,c2)
    ph = du.calc_phej(m1,c2,m2,c2)
    
    t_d, lbol_d,mag_new = calc_lc(tini,tmax,dt,mej,vej,vmin,th,ph,kappa,eps,alp,eth,flgbct = False)
    #t_d is time in days. lbol_d is bolometric luminosity, mag_new is the magnitude which we are interested in
    if plot == True:
        u = mag_new[0]
        g = mag_new[1]
        r = mag_new[2]
        i = mag_new[3]
        z = mag_new[4]
        y = mag_new[5]
        J = mag_new[6]
        H = mag_new[7]
        K = mag_new[8]

        plt.style.use("bmh")
        plt.subplot(121)
        plt.plot(t_d,u,label = "u")
        plt.plot(t_d,g,label = "g")
        plt.plot(t_d,r,label = "r")
        plt.plot(t_d,i,label = "i")
        plt.plot(t_d,z,label = "z")
        #plt.xscale("log")
        plt.xticks(np.arange(tini,tmax))
        plt.gca().invert_yaxis()
        plt.legend(prop={'size': 6})

        plt.subplot(122)
        #plt.plot(t_d,y,label = "y")
        plt.plot(t_d,J,label = "J")
        plt.plot(t_d,H,label = "H")
        plt.plot(t_d,K,label = "K")
        plt.xticks(np.arange(tini,tmax))
        plt.gca().invert_yaxis()
        plt.legend(prop={'size': 6})
        #plt.xscale("log")
        plt.show()
    return([m1,m2,l1,l1],np.array([t_d,mag_new]))#useful to return inputs



def generate_data(data):
    "function to generate multiple lightcurves based on a give dataset of inputs"
    output = []
    for i in np.arange(len(data)):
        line = data[i]
        if "idlelib" not in sys.modules:
            print(f'\r{100*i/len(data):.3f}% finished',end = '\r')
        m1,m2,l1,l2 = line
        temp_in,temp_out = Generate_LightCurve(m1,m2,l1,l2)
        output.append([temp_in,temp_out])
    return(output)




def thread_fn(m1,m2,l1,l2,fname,printing = False):
    "function used for multithreading the process. Speeds up data creation significantly"
    final_data = []
    L = len(m1)
    for i in np.arange(L):
        if printing == True:
            if "idlelib" not in sys.modules:#if running in a command or execution window
                print(f'\r{100*i/L:.3f}% finished',end = '\r')
            else: #if just running from IDLE
                if not i % 1000:
                    print(f'{i}/{L}\t{100*i/L:.2f}%')

        for x in np.arange(1):#if adding noise you would have np.arange(n) for number of points created around the initial.
            #When adding noise consideer: m1 > m2 => l1 < l2
            #These comments were intiial attempts to add noise
            m1_ = m1[i] #+ random.uniform(0,0.01)*m1[i] 
            m2_ = m2[i] #+ random.uniform(-0.01,0)*m2[i]
            l1_ = l1[i] #+ random.uniform(-0.01,0)*l1[i]
            l2_ = l2[i] #+ random.uniform(0,0.01)*l2[i]
                
            conditions,lightcurves = Generate_LightCurve(m1[i],m2[i],l1[i],l2[i])
            t_d,curves = lightcurves
            m1_,m2_,l1_,l2_ = conditions
            g = curves[1]
            r = curves[2]
            I = curves[3]
            z = curves[4]

            d = np.array([m1_,m2_,l1_,l2_,t_d,g,r,I,z])
            final_data.append(d)

    final_data = np.array(final_data)
    df = pd.DataFrame(data = final_data,
                          columns = list(['m1','m2','l1','l2','time','g','r','i','z']))

    df.to_pickle(f"{fname}.pkl")
    print(f"{fname} done")
    #returning from a thread is quite confusing so it's better to just save the individual files and recombine later
    
def thread_fn2(fname,i,printing = False):
    "The second threading function which attempts to add noise. Was never used later in the process but in theory should work."

    print(f'thread {i} starting')
    final_data = []
    data = np.array(pd.read_pickle(fname).values)
    t = 0
    
    for d in data:
        L = len(data)
        t += 1
        if printing == True:
            if "idlelib" not in sys.modules:
                print(f'\r{100*t/L:.3f}% finished',end = '\r')
            else:
                if not i % 1000:
                    print(f'{t}/{L}\t{100*t/L:.2f}%')
        m1,m2,l1,l2,t_d,g,r,I,z = d
        for j in np.arange(5):
            m1_ = m1 + random.uniform(0,0.01)*m1 #m1 > m2 => l1 < l2
            m2_ = m2 + random.uniform(-0.01,0)*m2 #add a random value between m2 and m2 - 1%*m2
            l1_ = l1 + random.uniform(-0.01,0)*l1
            l2_ = l2 + random.uniform(0,0.01)*l2
            new_d = np.array([m1_,m2_,l1_,l2_,t_d,g,r,I,z])
            final_data.append(new_d)
            
    final_data = np.array(final_data)

    #print(final_data[0])
    df = pd.DataFrame(data = final_data,
                      columns = list(['m1','m2','l1','l2','time','g','r','i','z']))
    df.to_pickle(f"{fname}_noise.pkl")
    print(f'thread {i} finished')
    

if __name__ == "__main__":#if not being imported to another python file.
    """NB: Data creation took a long time (at least 2 hours if not more if I remember correctly)
            it might be possible to take this code and instead of multithreading create data
            in sections."""
    
    #Making the first data
    filedir = "mass_lambda/mass_lambda_distributions.h5"#the file containing the input m1,m2,l1,l2

    d = h5py.File(filedir, 'r')
    data = np.array(d.get('labels'))
    d.close()

    m1 = data[:,0]
    m2 = data[:,1]
    l1 = np.exp(data[:,2])
    l2 = np.exp(data[:,3])

    N_threads = 1 #depends on processor being used. More threads the better.

    #split the inputs into constituent parts for multithreading.
    part_m1 = np.split(m1, 16*N_threads)
    part_m2 = np.split(m2, 16*N_threads)
    part_l1 = np.split(l1, 16*N_threads)
    part_l2 = np.split(l2, 16*N_threads)
    threads = list()
    
    for i in np.arange(N_threads):
        #launch all the threads
        printing = False
        if i == 0:
            #only have printing = True for the first thread to act as an indication of how long the overal process has
            printing = True
        i+= 3
        x = Thread(target = thread_fn, args = (part_m1[i],part_m2[i],part_l1[i],part_l2[i],
                                                         f'DU17_training/DU17_{i}',printing,))
        threads.append(x)
        x.start()
        
    for thread in threads:
        thread.join()
    print("All threads finished")

    

    
    
