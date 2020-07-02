import pickle
import matplotlib.pyplot as plt
from natural_snow_scaler import NaturalSnowScaler

height_level_step_width = 25
subfolder_name = f"height_level_step_width_{height_level_step_width}"

radiations_at_station = pickle.load(open(f"outputData/{subfolder_name}/pickle_radiations_at_station.pkl", "rb"))
height_level_objects = pickle.load(open(f"outputData/{subfolder_name}/pickle_height_level_objects.pkl", "rb"))


from_ = 3100
to = 3000

station = 2366
measured_snow = 20


last_scale_linear = 0
last_scale_quadratic = 0
last_scale_fixed_7 = 0
last_scale_fixed_10 = 0
plt.figure()

plt.scatter(station, measured_snow, color="red")

for level in range(1800, 3300, 100):
    scale_linear = NaturalSnowScaler.linear_scale_factor(level, station)
    scale_quadratic = NaturalSnowScaler.quadratic_scale_factor(level, station)
    scale_fixed_7 = NaturalSnowScaler.fixed_percentage_per_100_meter_scale_factor(level, station, 0.07)
    scale_fixed_10 = NaturalSnowScaler.fixed_percentage_per_100_meter_scale_factor(level, station, 0.1)

    print("Percentage increase per 100m for linear: ", round((scale_linear-last_scale_linear)*100, 2))
    print("Percentage increase per 100m for quadratic: ", round((scale_quadratic-last_scale_quadratic)*100, 2))
    print("Percentage increase per 100m for fixed 7 percent: ", round((scale_fixed_7-last_scale_fixed_7)*100, 2))
    print("Percentage increase per 100m for fixed 10 percent: ", round((scale_fixed_10-last_scale_fixed_10)*100, 2))

    last_scale_linear = scale_linear
    last_scale_quadratic = scale_quadratic
    last_scale_fixed_7 = scale_fixed_7
    last_scale_fixed_10 = scale_fixed_10
    plt.scatter(level, measured_snow * scale_linear, color="orange")
    plt.scatter(level, measured_snow * scale_quadratic, color="blue")
    plt.scatter(level, measured_snow * scale_fixed_7, color="green")
    plt.scatter(level, measured_snow * scale_fixed_10, color="purple")

plt.scatter(None, None, color="orange", label="Linear")
plt.scatter(None, None, color="blue", label="Quadratic")
plt.scatter(None, None, color="green", label="Fixed 7 percent/100m")
plt.scatter(None, None, color="purple", label="Fixed 10 percent/100m")


plt.legend()
plt.xlabel("Height [m]")
plt.ylabel("Snow height [cm]")
plt.grid()
plt.show()
