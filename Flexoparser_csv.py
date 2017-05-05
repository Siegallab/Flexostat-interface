
# coding: utf-8

# In[100]:

import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import pylab
import csv

parser = argparse.ArgumentParser(description='Turbidostat Data Parser') # This section defines the command line inputs
parser.add_argument("-i", "--input", 
                    help ="Input the filename of the file you want to parse")
parser.add_argument("-o", "--output", default="all", 
                    help ="Input what outputs tou want to get. all, od, u or z")# This creates a command line argument c
parser.add_argument("-b", "--begin",
                    help = "input a machine time at which you want the parser to start in the data")
parser.add_argument("-e", "--end", 
                    help = "input a machine time you want the parser to stap parsing the data")
parser.add_argument("-f", "--filename", default= "data",
                    help = "input a machine time you want the parser to stap parsing the data")
args = parser.parse_args()

with open(args.input) as f: #open input file
    log = f.read()


def parse_od(rdata):
    lines = rdata.split('\n') #Parse input file into list of lines
    data = []
    for line in lines[:-1]:
        d1 = line.split(":")
        d2 = [int(d1[1][:-7])]
        ods = d1[2][2:-6].split(",")
        for od in ods:
            d2.append(float(od))
        if args.begin and args.end:
            d2 = d2[args.begin:args.end]
        elif args.begin:
            d2 = d2[args.begin:]
        elif args.end:
            d2 = d2[:args.end]
        data.append(tuple(d2))
        
    return data

def parse_u(rdata):
    lines = rdata.split('\n') #Parse input file into list of lines
    data = []
    for line in lines[:-1]:
        d1 = line.split(":")
        d2 = [int(d1[1][:-7])]
        us = d1[3][2:-6].split(",")
        for u in us:
            d2.append(float(u))
        if args.begin and args.end:
            d2 = d2[args.begin:args.end]
        elif args.begin:
            d2 = d2[args.begin:]
        elif args.end:
            d2 = d2[:args.end]
        data.append(tuple(d2))
    return data


def parse_z(rdata):
    lines = rdata.split('\n') #Parse input file into list of lines
    data = []
    for line in lines[:-1]:
        d1 = line.split(":")
        d2 = [int(d1[1][:-7])]
        zs = d1[4][2:-2].split(",")
        d2.append(float(zs[0][1:-2]))
        for z in zs[1:]:
            d2.append(float(z[2:-1]))
        if args.begin and args.end:
            d2 = d2[args.begin:args.end]
        elif args.begin:
            d2 = d2[args.begin:]
        elif args.end:
            d2 = d2[:args.end]
        data.append(tuple(d2))
    return data


if args.output == "all":
    oddata = parse_od(log)
    udata = parse_u(log)
    zdata = parse_z(log)
    
    odfile = open(args.filename + "_od.csv", 'wb')
    wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
    for od in oddata:
        wrod.writerow(od)
    
    ufile = open(args.filename + "_u.csv", 'wb')
    wru = csv.writer(ufile, quoting=csv.QUOTE_ALL)
    for u in udata:
        wru.writerow(u)
    
    zfile = open(args.filename + "_z.csv", 'wb')
    wrz = csv.writer(zfile, quoting=csv.QUOTE_ALL)
    for z in zdata:
        wrz.writerow(z)
        
if args.output == "od":
    oddata = parse_od(log)
    
    odfile = open(args.filename + "_od.csv", 'wb')
    wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
    for od in oddata:
        wrod.writerow(od)
        
if args.output == "u":
    udata = parse_u(log)
    
    ufile = open(args.filename + "_u.csv", 'wb')
    wru = csv.writer(ufile, quoting=csv.QUOTE_ALL)
    for u in udata:
        wru.writerow(u)

if args.output == "z":
    zdata = parse_z(log)
    
    zfile = open(args.filename + "_z.csv", 'wb')
    wrz = csv.writer(zfile, quoting=csv.QUOTE_ALL)
    for z in zdata:
        wrz.writerow(z)


# In[ ]:



