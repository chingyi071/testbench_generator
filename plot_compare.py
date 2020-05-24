import matplotlib.pyplot as plt
import numpy as np

for i in range(4):
    fmeasured = open('vop%d.out' % i)
    lines = fmeasured.readlines()
    time_measured = [float(l.split(' ')[0]) for l in lines]
    value_measured = [float(l.split(' ')[1]) for l in lines]
    
    # fideal = open('vop_ideal.out')
    # lines = fideal.readlines()
    # time_ideal = [float(l.split(' ')[0]) for l in lines]
    # value_ideal = [float(l.split(' ')[1]) for l in lines]
    
    plt.plot(time_measured, value_measured, label='measured')
    # plt.plot(time_ideal, value_ideal, label='ideal')
    plt.legend()
    plt.show()
