
# coding: utf-8

# In[106]:

#!/bin/bash

import sys
import pandas as pd
import matplotlib.pyplot as plt
plt.use('Agg')
import pylab


with open(sys.argv[1]) as f: #open input file
    rdata = f.read()
    
def parse(rdata):
    lines = rdata.split('\n') #Parse input file into list of lines
    data = []
    for line in lines[:-1]:
        d1 = line.split(":")
        d2 = []
        ods = d1[2][2:-6].split(",")
        for od in ods:
            d2.append(float(od))
        data.append(tuple(d2))
    return data
  
data = parse(rdata)

labels = ['ODC1','ODC2','ODC3','ODC4','ODC5','ODC6','ODC7','ODC8']

df = pd.DataFrame.from_records(data, columns=labels)  
plt.figure(); df.plot();
plt.savefig(sys.argv[2])



# In[ ]:



