import os
import matplotlib.pyplot as plt
from config_handler import cfg
import matplotlib.dates
import matplotlib.cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.markers import MarkerStyle
import os
from matplotlib import patches
from operator import sub
import datetime as dt
# from matplotlib import rc
# rc('text', usetex=True)
from measurement_handler import MeasurementHandler
import scipy
import scipy.stats
import numpy as np
from scipy import optimize
import misc as fc
import calendar
from height_level import HeightLevel
import shapefile as shp
from descartes import PolygonPatch
import matplotlib.colors
import matplotlib.colorbar
from hydrologic_year import HydrologicYear
from matplotlib.ticker import MaxNLocator
from measurement import MeanStationMeasurement
import copy
import csv
import locale
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm

matplotlib.rcParams.update({'font.size': float(cfg["plot_text_size"])})
matplotlib.rcParams['axes.formatter.use_locale'] = True
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

DAYS_365 = dt.timedelta(days=365)  # hours=5, minutes=48     365.2422 days in year approximately  dont change to that


class Downloader:
    download_path = cfg["RESULT_PLOT_PATH"]

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    @classmethod
    def download_components(cls, components: list, cumulate_components, use_mean_measures=False, NaN_value="None", save_name=None):
        """
        Functions to download various data

        :param components:
        :param use_mean_measures:
        :return:
        """
        # currently not support for downloading averaged measurements

        if not os.path.exists(cfg["RESULT_DATA_DOWNLOAD_PATH"]):
            os.makedirs(cfg["RESULT_DATA_DOWNLOAD_PATH"])

        with open(cfg["RESULT_DATA_DOWNLOAD_PATH"] + f"/data_download_{'cumulated_' if cumulate_components else ''}" + '_'.join(components) + ".csv", "w") as f:
            writer = csv.writer(f)

            if cumulate_components:
                writer.writerow(["Date", '+'.join(components)])
            else:
                writer.writerow(["Date"] + components)

            y_dates = MeasurementHandler.get_all_of("datetime",
                                                    use_mean_measurements=use_mean_measures)

            if cumulate_components:
                x_vals = MeasurementHandler.get_cumulated_vals_of_components(
                    components, use_mean_measures)

                for date, val in zip(y_dates, x_vals):
                    writer.writerow([date, round(val, 5) if val is not None else NaN_value])

            else:
                multiple_component_vals = []

                for component in components:
                    try:
                        multiple_component_vals.append(MeasurementHandler.get_all_of(
                            component, use_mean_measurements=use_mean_measures))
                    except AttributeError:
                        print(component, "does not exist")

                for i, date in enumerate(y_dates):
                    writer.writerow([date] + [round(val[i]) if val[i] is not None else NaN_value for val in multiple_component_vals ])

    @classmethod
    def download_in_cosipy_format(cls):
        """
        Functions to download various data

        PRES        ::   Air Pressure [hPa]
        N           ::   Cloud cover  [fraction][%/100]
        RH2         ::   Relative humidity (2m over ground)[%]
        RRR         ::   Precipitation per time step [mm]
        SNOWFALL    ::   Snowfall per time step [m]
        G           ::   Solar radiation at each time step [W m-2]
        T2          ::   Air temperature (2m over ground) [K]
        U2          ::   Wind speed (magnitude) [m/s]
        HGT         ::   Elevation [m]

        :return:
        """
        # currently not support for downloading summed measurements

        if not os.path.exists(cfg["RESULT_DATA_DOWNLOAD_PATH"]):
            os.makedirs(cfg["RESULT_DATA_DOWNLOAD_PATH"])

        with open(cfg["RESULT_DATA_DOWNLOAD_PATH"] + "/data_download_for_cosipy.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["TIMESTAMP", "T2", "PRES", "N", "U2", "RH2", "RRR", "SNOWFALL", "G", "LWin"])

            measures_to_take = [
                MeasurementHandler.all_mean_measures[i] for i in sorted(MeasurementHandler.current_mean_index_scope)]

            for obj in measures_to_take:
                obj: MeanStationMeasurement

                snow = obj.snow_depth_delta_natural if obj.snow_depth_delta_natural > 0 else 0

                writer.writerow(
                    [obj.datetime, obj.temperature+273.15, obj.air_pressure/100, "", obj.wind_speed, obj.rel_moisture, 0,
                     snow, obj.sw_radiation_in, obj.lw_radiation_in])