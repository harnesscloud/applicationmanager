#!/usr/bin/env python
import os, sys
import json

def avg(l):
	return sum(l)/float(len(l))
 
def filter_and_average(data):
	filtered_data = []
	while len(data) > 0:
		d = data[0]
		
		filtered_data.append(d)
		
		x = filtered_data[-1]["Configuration"]
		f = filter(lambda item: item["Configuration"] == x, data)
		filtered_data[-1]["Results"]["TotalCost"] = avg(map(lambda item: item["Results"]["TotalCost"], f))
		filtered_data[-1]["Results"]["ExeTime"] = avg(map(lambda item: item["Results"]["ExeTime"], f))
		
		data = filter(lambda item: item["Configuration"] != x, data)
		
		
	#print "FILTERED DATA :", filtered_data
	return filtered_data
""" 
    Transform new log format in old log format
"""
if len(sys.argv) < 2:
	print "Provide the path to the exp folder."
	sys.exit()
	
path = sys.argv[1]
 
exps = map(lambda p: os.path.join(path, p),os.listdir(path))
#print exps

experiment_list = []

points_x = []
points_y = []

exp_data = []
for exp in exps:
	e = open(exp, "r").read()
	e = json.loads(e)
	try:
		e["Results"]["TotalCost"]
		e["Results"]["ExeTime"]
		e["RuntimeData"]["Usage"][0]
		if e["Configuration"]["%master_cores"] < 4 and  e["Configuration"]["%master_cores"] > 16:
			raise Exception()
		if "large" in e["Arguments"]["%arg1"]: 
			raise Exception()
	except:	
		#print "ignore file...corrupt : ", e["Configuration"]
		continue
	exp_data.append(e)

exps = filter_and_average(exp_data)

for e in exps:
	conf = e["Configuration"]
	cost = 0.0
	for k in conf:
		if "cores" in k:
			cost = conf[k] * 0.0396801 + cost

		elif "ram" in k:
			conf[k] = conf[k] / 1024
			cost = conf[k] * 0.0186323 + cost #the ram is in MB ---> GB
			
	#normalize costs
	e["Results"]["ExeTime"]  = e["Results"]["ExeTime"]/60.0
	e["Results"]["TotalCost"]  = cost/60.0 * e["Results"]["ExeTime"]

	points_x.append(e["Results"]["TotalCost"] * e["Results"]["ExeTime"])
	points_y.append(e["Results"]["ExeTime"])
	experiment_list.append(e)
    
    
f = open("model.json", "w")
f.write(unicode(json.dumps({ "PerformanceModel" : [experiment_list]}, ensure_ascii=False)))
f.close()


#plot points
import matplotlib.pyplot as plt
plt.figure(1) 
ax = plt.subplot(111)
ax.plot(points_x, points_y, 'ro')
ax.set_ylabel('ExeTime')
ax.set_xlabel('Cost')
plt.show()




    
    

