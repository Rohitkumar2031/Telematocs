#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import argparse
import warnings
import os

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()

parser.add_argument(
    "--base-dir" , type=str , default="."
)
parser.add_argument(
    "--file"  , default="rawfeed_april_0_CAN.csv"
)
parser.add_argument(
    "--save" , type=bool , default=False
)
parser.add_argument(
    "--plot" , type=bool , default=False
)

args = parser.parse_args()

if __name__ == "__main__":
	base_dir = args.base_dir
	plot = args.plot
	save = args.save
	file_ = args.file
	filename = os.path.join(base_dir , file_)
	data = pd.read_csv(filename)
	deviceData = []
	ids = data["deviceID"].unique()
	for device in ids:
		temp = data[data.deviceID == device].copy()
		temp = temp.sort_values("utc" , ascending=True)
		deviceData.append(temp)
		for i in range(len(deviceData)):
			deviceData[i]["Acceleration"] = deviceData[i].vehicleSpeed.diff() * (5.0/18.0) / deviceData[i].utc.diff()
	max_acc = 0.01
	for i in range(len(deviceData)):
		print(" {:.2f}% of Cases have hard Acceleration Device ID : {}".format(100 *np.mean(np.array(deviceData[i].Acceleration > max_acc).astype(np.float32)) , ids[i]))
	data_weeks = data.utc//(60 * 60 * 24 * 7) - 1003
	data_weeks.value_counts(0)
	for i in range(len(deviceData)):
		deviceData[i]["Mileage"] = deviceData[i]["totalDistance"].diff() / (deviceData[i]['tripFuel'].diff() * 3.8 )
	corr_matrix = deviceData[0].corr()
	corr_matrix_list = []
	for i in range(len(deviceData)):
		corr_matrix_list.append(deviceData[i].corr())
	print("Important Features with Linear Relationships (With Mileage): DeviceID : {}".format(ids[0]))
	print(corr_matrix["Mileage"][abs(corr_matrix["Mileage"]) > 0.1])
	valid_cols = []
	for col  in corr_matrix.columns:
		if not corr_matrix.Mileage.isna()[col] :
			valid_cols.append(col)
	if save:
		for i , id_ in zip(range(len(deviceData)) , ids):
			deviceData_Mileage = corr_matrix_list[i][valid_cols]
			deviceData_Mileage.to_csv("Mileage Correlations - {}.csv".format(id_))

	rnd_clf = RandomForestRegressor(n_estimators=100 , bootstrap=True , n_jobs=-1 , oob_score = True)

	useless = [ "Mileage", "Unnamed: 0", "id" , "deviceID" , "sequenceNo" ,"latitude", "longitude", "utc"  , "hrlfc", "sweetSpot" , "seconds"  , "minute" , "hour" , "month" , "day" ]
	for col in useless :
		try :
			valid_cols.remove(col)
		except : pass

	X = deviceData[0][valid_cols].copy().values
	X[np.isnan(X)] = 0
	y = deviceData[0]["Mileage"].copy().values
	y[np.isnan(y)] = 0
	y[np.isinf(y)] = 0

	zero_mileage_indicies = y != 0

	X = X[zero_mileage_indicies]
	ind2 = X[: , -1] != 0
	X = X[ind2]
	y = y[zero_mileage_indicies]
	y = y[ind2]

	rnd_clf.fit(X , y)

	print("Most Important Features for consideration of Mileage (Ranked) \n")

	importances = rnd_clf.feature_importances_
	indx = importances.argsort()

	valid_cols = np.array(valid_cols)
	valid_cols_sorted = valid_cols[indx]
	importances = importances[indx]

	output = str()
	for i in reversed(range(len(valid_cols))):
		output = output + str( valid_cols_sorted[i] ) + str(importances[i]) + "\n"
	print("Regressor R squared : {}".format(100 * rnd_clf.oob_score_))

	#ch = input("Save to file ? (y/n)")
	if save:
		with open("Milage_Feature_importances_LMD.txt" , 'w+') as file_:
			file_.write(output)
	temp = deviceData[0][zero_mileage_indicies][ind2]
	if plot:
		print("Size of Dots : Engine Oil Pressure \nColor of Dots : Vehicle Speed")
		plt.style.use('ggplot')
		plt.figure(figsize=(8 , 8))
		plt.scatter(x=temp.Mileage , y=temp.Acceleration , alpha=0.4 , c=temp.vehicleSpeed , cmap=plt.get_cmap('jet'),s=temp.engineOilPressure )
		plt.xlabel('Mileage')
		plt.ylabel('Acceleration')
		plt.show()