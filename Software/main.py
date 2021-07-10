"""
This software was originally written for a Bachelor's Thesis in 2019
The title of the bachelor thesis is "Energiebilanz im Ablationsgebiet der Pasterze"

GNU General Public License v3.0

@author Manuel Theurl
"""

from config_handler import cfg
import datetime as dt
import os
import threading
from reader import Reader
import sys
import pickle
import numpy as np
from height_level import HeightLevel
import copy
from importlib import reload

sys.path.append("GUI")

# The gui is constructed as singletons .. this order therefor has to be maintained
import gui_main_frame as gui_main
import navigation_bar
import version_bar
import info_bar

import frame_plot
import frame_download
import frame_read
import frame_scope
import frame_conversion
import frame_energy_balance
import frame_prepare_measurements
import frame_mean
from visualizer import Visualizer
from hydrologic_year import HydrologicYear
from energy_balance import EnergyBalance
from stats_printer import Statistics
from measurement_handler import MeasurementHandler
from downloader import Downloader


class NoGuiManager:
    def __init__(self):
        """
        Class to run stuff without a gui. Specific knowledge about the software is needed.
        """
        self.path_to_meteorologic_measurements = "../Meteorologic_data/PAS_10min.csv"
        self.hydrologic_years_looked_at = [2012, 2013, 2014, 2016, 2017, 2018]  # 2015 is baad
        self.startTime = dt.datetime(self.hydrologic_years_looked_at[0], 10,
                                     1)  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = dt.datetime(self.hydrologic_years_looked_at[-1] + 1, 9,
                                   30)  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.simulation_accuracy = 0.0001
        self.use_tongue_only = True
        self.no_debris = False
        self.high_res_rad_grid = True
        height_level_step_width = 25
        self.hourly_resolution = 24
        self.pickle_multiple_measurement_singleton = f"outputData/pickle_multiple_measurements_singleton_h{self.hourly_resolution}.pkl"
        self.pickle_multiple_measurement_singleton_filled = f"outputData/pickle_multiple_measurements_singleton_filled_h{self.hourly_resolution}.pkl"

        self.pickle_meteorological_years = f"pickle_meteorologic_years_h{self.hourly_resolution}.pkl"
        self.pickle_height_levels_objects = f"pickle_height_level_objects.pkl"
        self.pickle_radiations_at_station = "pickle_radiations_at_station.pkl"

        self.subfolder_name = f"height_level_step_width_{height_level_step_width}"
        self.filename = 'outputData/session.out'

        if self.use_tongue_only:
            self.subfolder_name += "_tongue"
        if self.no_debris:
            self.subfolder_name += "_noDebris"
        if self.high_res_rad_grid:  # this could be removed some day, if always the high rad grids are taken TODO
            self.subfolder_name += "_radGridHighRes"

    # def save_current_session(self):
    #     self.filename = 'outputData/session.out'
    #     my_shelf = shelve.open(self.filename, 'n')  # 'n' for new
    #
    #     for key in dir():
    #         try:
    #             my_shelf[key] = globals()[key]
    #         except TypeError:
    #             #
    #             # __builtins__, my_shelf, and imported modules can not be shelved.
    #             #
    #             print('ERROR shelving: {0}'.format(key))
    #     my_shelf.close()
    #
    # def restore_current_session(self):
    #     my_shelf = shelve.open(self.filename)
    #     for key in my_shelf:
    #         globals()[key] = my_shelf[key]
    #     my_shelf.close()

    @staticmethod
    def save_handler(fname):
        MeasurementHandler.save_me2(fname)  # its not even saving correctly

    @staticmethod
    def load_handler(fname):
        one, two, three, fore = MeasurementHandler.load_me(fname)
        MeasurementHandler.current_single_index_scope = one
        MeasurementHandler.all_single_measures = two
        MeasurementHandler.current_mean_index_scope = three
        MeasurementHandler.all_mean_measures = fore

    def run_calculations_height_levels(self, recalculate=True):
        """

        :return:
        """
        print("STARTING WITH THE CALCULATIONS")

        Reader.add_file_path(self.path_to_meteorologic_measurements)

        if recalculate:
            Reader.read_meterologic_file_to_objects(starttime=self.startTime, endtime=self.endTime)
            self.combined_preparing_of_measurements(sum_hourly_resolution=24)
            # needed for the height adaptions of the meteorologic values
            MeasurementHandler.calculate_wetbulb_temperature_for_mean_measures()
            self.save_handler(self.pickle_multiple_measurement_singleton)
        else:
            self.load_handler(self.pickle_multiple_measurement_singleton)

        radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))
        height_level_objects = pickle.load(
            open(f"outputData/{self.subfolder_name}/{self.pickle_height_levels_objects}", "rb"))

        snowings_per_day_for_height_levels_starting_value = list(
            reversed(np.linspace(0.01, 0.1, len(height_level_objects) // 2)))
        snowings_per_day_for_height_levels_starting_value += [0] * (
                len(height_level_objects) - len(snowings_per_day_for_height_levels_starting_value))

        hydrologic_years = dict()

        for year in self.hydrologic_years_looked_at:
            print(f"___ Looking at hydrologic year {year} ___")
            hydrologic_years[year] = HydrologicYear(copy.deepcopy(height_level_objects))
            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            for i, height_level in enumerate(hydrologic_years[year].height_level_objects):
                """ Lets try to find the optimum amount of snowing for not loosing mass """
                print("Doing calculations for height level", height_level)
                current_snowing_per_day = snowings_per_day_for_height_levels_starting_value[i]
                current_delta = None

                while True:
                    print("Snowing per day", round(current_snowing_per_day * 1000, 1), "mm", current_delta)
                    height_level.clear_simulated_measurements()
                    height_level.artificial_snowing_per_day = current_snowing_per_day

                    liters_melted_anyways = MeasurementHandler.overall_height_level_simulation(height_level,
                                                                                               radiations_at_station)
                    swe_in_liters_at_end = height_level.get_swe_of_last_measurement_and_constantly_laying_snow()

                    if swe_in_liters_at_end > liters_melted_anyways:
                        if current_delta is None:  # this will be true for the second iteration
                            current_delta = -0.01
                        else:
                            if current_delta > 0:
                                current_delta /= -2
                            else:
                                # reduced snowing and it is still too much -> stick with the bigger delta value
                                pass
                        if abs(current_delta) < self.simulation_accuracy:
                            print("Found good enough estimate:", round(current_snowing_per_day * 1000, 1),
                                  "mm snowing per day needed")
                            print(
                                f"Compensated {int(liters_melted_anyways)} liters/m^2 from beginning of meteorological year")
                            break  # found good enough estimation
                        elif current_snowing_per_day <= 0:
                            print("No snowing needed at all")
                            break
                    else:
                        if current_delta is None:  # this will be true for the second iteration
                            current_delta = 0.01
                        else:
                            if current_delta < 0:
                                current_delta /= -2
                            else:
                                # increased snowing and it is still too little -> stick with the bigger delta value
                                pass

                    current_snowing_per_day += current_delta

                    if current_snowing_per_day < 0:
                        current_snowing_per_day = 0

            print("Overall water needed:",
                  round(hydrologic_years[year].overall_amount_of_water_needed_in_liters / 1000, 1), "m^3")

        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", "wb") as f:
            pickle.dump(hydrologic_years, f)

        self.save_handler(self.pickle_multiple_measurement_singleton_filled)

    def run_visualizations_height_levels(self):
        """

        :return:
        """
        print("STARTING WITH THE VISUALIZATIONS")
        Visualizer.show_plots = False

        Visualizer.change_result_plot_subfolder(f"{self.subfolder_name}_h{self.hourly_resolution}")

        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", 'rb') as f:
            meteorologic_years = pickle.load(f)

        self.load_handler(self.pickle_multiple_measurement_singleton_filled)

        radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))
        #
        # try:
        #     Visualizer.plot_comparison_of_years(
        #         meteorologic_years, save_name=f"req_snow_compare_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}")
        # except TypeError:
        #     print("bar plot not working here, this is a todo still")
        #
        # Visualizer.plot_day_of_ice_exposures_for_years_at_height(meteorologic_years, cfg["AWS_STATION_HEIGHT"], radiations_at_station,
        #                                                                    save_name=f"day_of_ice_exposure_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

        fix_lower_limit = 3 if self.use_tongue_only else 0
        fix_upper_limit = 7.5
        # # TODO for whole pasterze, equality_line_2018 from all hast to be taken
        Visualizer.plot_pasterze(meteorologic_years, self.hydrologic_years_looked_at, "inputData/AWS_Station.shp",
                                 "inputData/equality_line_2018.shp", only_tongue=self.use_tongue_only,
                                 fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                 save_name=f"pasterze_water_needed_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}_")

        exit()

        Visualizer.plot_compare_water_and_height(self.hydrologic_years_looked_at, meteorologic_years,
                                                 save_name=f"water_vs_height_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}")

        for year in self.hydrologic_years_looked_at:
            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            Visualizer.plot_components_lvls([
                meteorologic_years[year].get_height_level_close_to_height(cfg["AWS_STATION_HEIGHT"])],
                ("total_snow_water_equivalent", "artificial_snow_water_equivalent", "natural_snow_water_equivalent"),
                "m w. e.", factor=1 / 1000, stack_fill=True,
                use_mean_measures=True, show_estimated_measurement_areas=True,
                save_name=f"all_snow_water_equivalents_{year}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

            Visualizer.plot_compare_water_and_height([year], meteorologic_years,
                                                     save_name=f"water_vs_height_{year}")

            Visualizer.plot_day_of_ice_exposures_for_year(year, meteorologic_years, radiations_at_station,
                                                          save_name=f"day_of_ice_exposure_{year}")

            Visualizer.plot_pasterze(meteorologic_years, [year], "inputData/AWS_Station.shp",
                                     f"inputData/equality_line_{year}.shp", only_tongue=self.use_tongue_only,
                                     fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                     save_name=f"pasterze_water_needed_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5),
                                            ("natural_snow_water_equivalent",), "m w. e.",
                                            use_mean_measures=True, show_estimated_measurement_areas=True,
                                            factor=1 / 1000,
                                            save_name=f"natural_snow_water_equivalent_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5),
                                            ("artificial_snow_water_equivalent",), "m w. e.",
                                            use_mean_measures=True, show_estimated_measurement_areas=True,
                                            factor=1 / 1000,
                                            save_name=f"artificial_snow_water_equivalent_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5),
                                            ("total_snow_water_equivalent",), "m w. e.",
                                            use_mean_measures=True, show_estimated_measurement_areas=True,
                                            factor=1 / 1000,
                                            save_name=f"total_snow_water_equivalent_{year}")

            # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
            # Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("albedo",), "",
            #                                           use_mean_measures=True, show_estimated_measurement_areas=True,
            #                                           save_name=f"albedo{year}")

    def sum_up_paper_values(self):
        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", 'rb') as f:
            hydrologic_years = pickle.load(f)

        # self.load_handler(self.pickle_multiple_measurement_singleton_filled)

        print("Year", "Water[m3]", "ArtificialSnow[m3]")
        for year in self.hydrologic_years_looked_at:
            water_l = hydrologic_years[year].overall_amount_of_water_needed_in_liters
            print(year, int(water_l / 1000), int(water_l / cfg["ARTIFICIAL_SNOW_SWE_FACTOR"] / 1000))

    def run_calculations_bachelor(self, startime: dt.datetime, endtime: dt.datetime, pegel_measure, type_="new"):
        """

        :param startime:
        :param endtime:
        :param pegel_measure:
        :param type_:
        :return:
        """
        print(
            f"\nRunning bachelor calaculations {type_} for {startime.strftime('%d.%m.%Y')} till {endtime.strftime('%d.%m.%Y')}:")
        Reader.add_file_path(self.path_to_meteorologic_measurements)

        Reader.read_meterologic_file_to_objects(starttime=startime, endtime=endtime)

        self.combined_preparing_of_measurements(type_=type_)
        self.combined_calculation_of_energy_balance_and_all_associated_values(type_=type_)

        measured_ablations = MeasurementHandler.get_all_of("relative_ablation_measured", use_mean_measurements=True)
        modeled_ablations = MeasurementHandler.get_all_of("relative_ablation_modeled", use_mean_measurements=True)

        print("Nones measured_ablations:", sum(x is None for x in measured_ablations))
        print("Nones modeled_ablations:", sum(x is None for x in modeled_ablations))

        for i in range(len(measured_ablations)):
            measured_ablations[i] = 0 if measured_ablations[i] is None else measured_ablations[i]
        for i in range(len(modeled_ablations)):
            modeled_ablations[i] = 0 if modeled_ablations[i] is None else modeled_ablations[i]

        # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
        # Visualizer.plot_single_component("albedo", "", use_mean_measures=True,
        #                                            save_name=f"albedo_{year}_{type_}_onlysummer_{only_summer}")

        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("temperature",), "°C", use_mean_measures=True,
        #                                            save_name=f"sensible_heat_and_temperature")
        #
        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("air_pressure",), "pa",
        #                                      use_mean_measures=True,
        #                                      save_name=f"sensible_heat_and_air_pressure")
        #
        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("wind_speed",), "m/s",
        #                                      use_mean_measures=True,
        #                                      save_name=f"sensible_heat_and_wind_speed")

        # Visualizer.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("albedo",), "-",
        #                                      use_mean_measures=True,
        #                                      save_name=f"swinout")

        # Visualizer.plot_components(("albedo",), "-",
        #                                      use_mean_measures=True,
        #                                      save_name=f"albedo_normal")
        #
        # Visualizer.plot_components(("midday_albedo",), "-",
        #                                      use_mean_measures=True,
        #                                      save_name=f"albedo_midday")

        # Visualizer.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("total_snow_depth",), "m",
        #                                      use_mean_measures=True,
        #                                      save_name=f"snow_depth")

        modeled_ablation = sum(modeled_ablations)
        measured_ablation = sum(measured_ablations)
        reality_factor_ablation = measured_ablation / modeled_ablation
        reality_factor_pegel = (pegel_measure / 100) / modeled_ablation
        print("Measured ablation", round(measured_ablation, 2), "Pegel measure", pegel_measure / 100)
        print("modeled ablation",
              round(modeled_ablation, 2))  # measured stays the same .. cause thats wont be affected
        print("Reality factor ablation:", round(reality_factor_ablation, 2))
        print("Reality factor pegel:", round(reality_factor_pegel, 2))

    @staticmethod
    def combined_preparing_of_measurements(sum_hourly_resolution=24, type_="new",
                                           measurements_to_fix=("temperature", "rel_moisture", "air_pressure",
                                                                "wind_speed", "sw_radiation_in", "sw_radiation_out",
                                                                "lw_radiation_in", "lw_radiation_out", "snow_delta",
                                                                "relative_ablation_measured")):
        """
        Basic steps that are used to prepare the measurements.
        :param sum_hourly_resolution:
        :param type_:
        :return:
        """
        # Preparations of measurements
        MeasurementHandler.correct_snow_measurements_for_single_measures()
        # MeasurementHandler.correct_long_wave_measurements_for_scope()
        MeasurementHandler.correct_short_wave_measurements_for_single_measures()
        MeasurementHandler.cumulate_ice_thickness_measures_for_single_measures(method="SameLevelPositiveFix")

        MeasurementHandler.calculate_snow_height_deltas_for_single_measures()

        if type_ == "new":
            MeasurementHandler.mean_measurements_by_time_interval(
                dt.timedelta(hours=sum_hourly_resolution))
            MeasurementHandler.fix_invalid_mean_measurements(measurements_to_fix)

    @staticmethod
    def combined_calculation_of_energy_balance_and_all_associated_values(type_="new"):
        # do not forget to set scope before that
        if type_ == "new":
            MeasurementHandler.calculate_energy_balance_for_mean_measures()
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for_mean_measures()
            MeasurementHandler.convert_measured_and_modeled_rel_ablations_in_water_equivalents_for_mean_measures()
        elif type_ == "original":
            MeasurementHandler.calculate_energy_balance_for_single_measures()
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for_single_measures()
            MeasurementHandler.mean_measurements_by_time_interval(dt.timedelta(days=1))
            MeasurementHandler.calculate_measured_and_theoretical_ablation_values_for_summed()

    def compare_measured_ablation_measured_pegel_and_measured(self, pegel_tuples, max_est_measures=0, recalculate=True):
        Visualizer.show_plots = False

        fname = f"outputData/scatter_compare_measured_pegel.pkl"

        if recalculate:
            Reader.add_file_path(self.path_to_meteorologic_measurements)
            Reader.read_meterologic_file_to_objects()
            self.combined_preparing_of_measurements(sum_hourly_resolution=24)
            self.save_handler(fname)
        else:
            self.load_handler(fname)

        Visualizer.plot_scatter_pegel_vs_X(
            pegel_tuples, vs="relative_ablation_measured",
            save_name=f"pegel_vs_measured (allow {max_est_measures}% est. measures)",
            max_estimated_ablation_measures_percent=max_est_measures)

    def compare_measured_ablation_measured_pegel_and_modeled(self, pegel_tuples, max_est_measures=0,
                                                             recalculate=True):
        """

        :param pegel_tuples:
        :param max_est_measures: Maximum estimated measures in percent
        :param recalculate:
        :return:
        """
        Visualizer.show_plots = False

        if recalculate:
            Reader.add_file_path(self.path_to_meteorologic_measurements)
            Reader.read_meterologic_file_to_objects()
            self.combined_preparing_of_measurements(sum_hourly_resolution=24)

        for i, rs in enumerate([(0.001, 0.001), (0.002, 0.001), (0.003, 0.001), (0.004, 0.001)]):
            f_name = f"tmp/picklsave_{rs[0]}_z0_snow{rs[1]}_{cfg['CLEAN_ICE_ALBEDO']}"
            if recalculate:
                EnergyBalance.set_new_roughness_parameters(rs[0], rs[1])
                MeasurementHandler.reset_scope_to_all()
                self.combined_calculation_of_energy_balance_and_all_associated_values()
                self.save_handler(f_name)
            self.load_handler(f_name)

            # """ Statistics """
            # Statistics.compare_pegel_measured_and_modeled_for_time_intervals(
            #     pegel_tuples, heading=f"\nSetup: z0 ice: {rs[0]} z0 snow {rs[1]}) max est. abl. measures {max_est_measures}",
            #     max_estimated_ablation_measures_percent=max_est_measures)


            # """ Plotting difference between measured and modeled """
            # Visualizer.plot_scatter_measured_modeled_ablation(
            #     pegel_tuples, save_name=f"measured_vs_modeled_z0-ice={rs[0]}_z0-snow={rs[1]}_ice-albedo-{cfg['CLEAN_ICE_ALBEDO']}_{max_est_measures}p-estimated",
            #     max_estimated_ablation_measures_percent=max_est_measures, measured_per_day_has_to_be_above_mm=1)

            """ Plotting difference between pegel vs modeled"""
            Visualizer.plot_scatter_pegel_vs_X(
                pegel_tuples,
                save_name=f"pegel_vs_modeled_z0-ice={rs[0]}_z0-snow={rs[1]}_ice-albedo-{cfg['CLEAN_ICE_ALBEDO']}_{max_est_measures}p-estimated",
                max_estimated_ablation_measures_percent=max_est_measures)

    def ablation_cumulation_test(self, recalculate=True):
        Visualizer.change_result_plot_subfolder(f"ablation_cumulation")
        Visualizer.show_plots = False

        f_name = "outputData/ablation_cumulation_test.pkl"

        Reader.add_file_path(self.path_to_meteorologic_measurements)
        Reader.read_meterologic_file_to_objects()

        if recalculate:
            MeasurementHandler.change_measurement_resolution_by_start_end_time(dt.datetime(2016, 1, 1),
                                                                               dt.datetime(2019, 1, 1))
            MeasurementHandler.cumulate_ice_thickness_measures_for_single_measures(method="SameLevelPositiveFix")

            self.save_handler(f_name)
        else:
            self.load_handler(f_name)

        Visualizer.plot_components(("cumulated_ice_thickness",), use_mean_measures=False,
                                   save_name=f"cum_ice")

    def cosipy_compare_mass_bilance_plot(self):
        f_name = f"tmp/picklsave_cosipy_prep"

        # TODO put this into cosipy verification project

        self.load_handler(f_name)
        import xarray as xr

        for year in (2014, 2015, 2016, 2017, 2018):
            try:
                netcad_file = xr.open_dataset(f"../../cosipy_verification/output/Pasterze{year}1001-{year + 1}0930.nc")
            except FileNotFoundError:
                print("No file for", year)
                continue

            cosipy_data = []

            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            modeled_data = MeasurementHandler.get_all_of("relative_ablation_modeled", use_mean_measurements=True)
            # compare_data = MeasurementHandler.get_all_of("lw_radiation_out", use_mean_measurements=True)

            # modeled_data = MeasurementHandler.get_all_of("total_energy_balance", use_mean_measurements=True)

            for dat in netcad_file.MB.data:
                cosipy_data.append(-dat[0][0])

            # for dat in netcad_file.ME.data:
            #     cosipy_data.append(dat[0][0])

            cosipy_cumulated = []
            modeled_cumulated = []

            cur_cos = 0
            for cos in cosipy_data:
                cur_cos += cos
                cosipy_cumulated.append(cur_cos)

            cur_modeled = 0
            for mod in modeled_data:
                cur_modeled += mod
                modeled_cumulated.append(cur_modeled)

            import matplotlib.pyplot as plt

            # plt.plot(cosipy_data, label="cosipy")
            # plt.plot(modeled_data, label="modeled")

            # plt.plot(cosipy_cumulated, label="cosipy")
            # plt.plot(modeled_cumulated, label="modeled")

            diff = []
            for i in range(len(cosipy_cumulated)):
                diff.append(modeled_cumulated[i] - cosipy_cumulated[i])

            for compare_value in ("sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out",
                                  "total_snow_depth", "rel_moisture", "wind_speed", "air_pressure", "sensible_heat",
                                  "latent_heat"):
                plt.figure(figsize=(10, 6))
                ax1 = plt.subplot()
                ax2 = ax1.twinx()

                compare_data = MeasurementHandler.get_all_of(compare_value, use_mean_measurements=True)

                ax1.plot(compare_data, color="blue", zorder=2, label=compare_value)
                ax2.plot(diff, color="orange", zorder=1, label="Ablation diff [m]")
                ax2.set_ylim(-2, 2)

                ax1.grid()

                ax1.set_xlabel("Time [s]")
                # ax1.set_ylabel("Ice level drop [m]")
                ax2.set_ylabel("Ablation diff [m]")
                ax1.set_ylabel(compare_value)

                # plt.title(f"Comparison Cosipy and Bulk mass bilance for hyd. year {year}")
                plt.title(f"Comparison Cosipy and Bulk mass bilance for hyd. year {year}")
                plt.savefig(f"plots/cosipy_verification/diff_compared_with_{compare_value}.png")

                ax1.legend()
                ax2.legend()

                # plt.legend()
                # plt.show()
                plt.close()

            exit()

    def cosipy_compare_mass_bilance_plot_snow_height(self):
        f_name = f"tmp/picklsave_cosipy_prep"

        # TODO put this into cosipy verification project

        self.load_handler(f_name)
        import xarray as xr

        for year in (2014, 2015, 2016, 2017, 2018):
            try:
                netcad_file = xr.open_dataset(f"../../cosipy_verification/output/Pasterze{year}1001-{year + 1}0930.nc")
            except FileNotFoundError:
                print("No file for", year)
                continue

            cosipy_data = []

            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            modeled_data = MeasurementHandler.get_all_of("total_snow_depth", use_mean_measurements=True)

            for dat in netcad_file.SNOWHEIGHT.data:
                cosipy_data.append(dat[0][0])

            cosipy_cumulated = []
            modeled_cumulated = []

            cur_cos = 0
            for cos in cosipy_data:
                cur_cos += cos
                cosipy_cumulated.append(cur_cos)

            modeled_data_no_neg = []

            for x in modeled_data:
                if x < 0:
                    modeled_data_no_neg.append(0)
                else:
                    modeled_data_no_neg.append(x)

            cur_modeled = 0
            for mod in modeled_data_no_neg:
                cur_modeled += mod
                modeled_cumulated.append(cur_modeled)

            import matplotlib.pyplot as plt

            plt.plot(cosipy_data, label="cosipy")
            plt.plot(modeled_data_no_neg, label="modeled")

            plt.xlabel("Time [s]")
            plt.ylabel("Snow height [m]")

            plt.legend()

            plt.savefig(f"plots/cosipy_verification/snow_{year}")

            # plt.plot(cosipy_cumulated, label="cosipy")
            # plt.plot(modeled_cumulated, label="modeled")

            # plt.show()

    def cosipy_compare_mass_bilance_plot_energy(self):
        f_name = f"tmp/picklsave_cosipy_prep"

        # TODO put this into cosipy verification project

        self.load_handler(f_name)
        import xarray as xr

        for year in (2014, 2015, 2016, 2017, 2018):
            try:
                netcad_file = xr.open_dataset(f"../../cosipy_verification/output/Pasterze{year}1001-{year + 1}0930.nc")
            except FileNotFoundError:
                print("No file for", year)
                continue

            cosipy_data = []

            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            modeled_data = MeasurementHandler.get_all_of("total_energy_balance", use_mean_measurements=True)

            for dat in netcad_file.ME.data:
                cosipy_data.append(dat[0][0])

            cosipy_cumulated = []
            modeled_cumulated = []

            cur_cos = 0
            for cos in cosipy_data:
                cur_cos += cos
                cosipy_cumulated.append(cur_cos)

            modeled_data_no_neg = []

            for x in modeled_data:
                if x < 0:
                    modeled_data_no_neg.append(0)
                else:
                    modeled_data_no_neg.append(x)

            cur_modeled = 0
            for mod in modeled_data_no_neg:
                cur_modeled += mod
                modeled_cumulated.append(cur_modeled)

            import matplotlib.pyplot as plt

            # plt.plot(cosipy_data, label="cosipy")
            # plt.plot(modeled_data_no_neg, label="modeled")

            plt.plot(cosipy_cumulated, label="cosipy")
            plt.plot(modeled_cumulated, label="modeled")

            plt.show()

    def demo_cosipy_data_format_downloader(self, recalculate=True):

        f_name = f"tmp/picklsave_cosipy_prep"

        # WARNING! Please check the data, its seems they are out of a reasonable range G MAX: 1199.98 MIN: -0.94

        if recalculate:
            Reader.add_file_path(self.path_to_meteorologic_measurements)
            Reader.read_meterologic_file_to_objects()
            self.combined_preparing_of_measurements(sum_hourly_resolution=1,
                                                    measurements_to_fix=("temperature", "rel_moisture", "air_pressure",
                                                                         "wind_speed", "sw_radiation_in",
                                                                         "lw_radiation_in", "snow_delta"))

            self.combined_calculation_of_energy_balance_and_all_associated_values()
            self.save_handler(f_name)
        else:
            self.load_handler(f_name)

        Downloader.download_in_cosipy_format()
        # MeasurementHandler.download_in_cosipy_format()

    def verify_with_cosipy(self):
        f_name = f"tmp/picklsave_cosipy_prep"

        self.load_handler(f_name)

        for year in self.hydrologic_years_looked_at:
            print(f"___ Looking at hydrologic year {year} ___")
            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            rel_ablations_modeled = MeasurementHandler.get_all_of("relative_ablation_modeled",
                                                                  use_mean_measurements=True)
            rel_ablations_measured = MeasurementHandler.get_all_of("relative_ablation_measured",
                                                                   use_mean_measurements=True)

            print("Ablation modeled:", sum(rel_ablations_modeled))
            print("Ablation measured:", sum(rel_ablations_measured))


if __name__ == "__main__":
    if not cfg["GUI"]:
        tasks = {
            "cosipy_verification": False,  # not working currently
            "height_level_calc_and_vis_for_paper": True,
            "calculations_bachelor": False,
            "ablation_cumulation_methods_test": False,
            "pegel_vs_measured_scatter_compare": False,
            "pegel_vs_modeled_scatter_compare": False,
        }

        no_gui_manager = NoGuiManager()

        if tasks["cosipy_verification"]:
            no_gui_manager.demo_cosipy_data_format_downloader()  # inside this saving the pickle file for the following cosipy related tasks?
            no_gui_manager.verify_with_cosipy()

            no_gui_manager.cosipy_compare_mass_bilance_plot_energy()  # this was just for verifying the model with cosipy
            no_gui_manager.cosipy_compare_mass_bilance_plot_snow_height()
            no_gui_manager.cosipy_compare_mass_bilance_plot()

        """ Height level calculations with visualizations """
        if tasks["height_level_calc_and_vis_for_paper"]:
            # no_gui_manager.run_calculations_height_levels(recalculate=False)  #
            # no_gui_manager.sum_up_paper_values()
            no_gui_manager.run_visualizations_height_levels()

        """ Single time frame comparison with measurement fixing """
        if tasks["calculations_bachelor"]:
            no_gui_manager.run_calculations_bachelor(dt.datetime(2013, 8, 29), dt.datetime(2013, 9, 25), 95)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 7, 7), dt.datetime(2017, 7, 26), 132)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 7, 26), dt.datetime(2017, 10, 14), 246)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 10, 14), dt.datetime(2018, 6, 22), 223)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 6, 22), dt.datetime(2018, 7, 16), 135)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 7, 16), dt.datetime(2018, 9, 30), 393)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 9, 30), dt.datetime(2019, 6, 24), 182)
            no_gui_manager.run_calculations_bachelor(dt.datetime(2019, 6, 24), dt.datetime(2019, 7, 17), 179)

        """ Combined time frame comparison with measurement fixing """
        if tasks["ablation_cumulation_methods_test"]:
            no_gui_manager.ablation_cumulation_test()

        if tasks["pegel_vs_measured_scatter_compare"] or tasks["pegel_vs_modeled_scatter_compare"]:
            """ Comparison of measured and modeled ablation and pegel measurement """
            pegel_time_spans = [
                (dt.datetime(2013, 8, 29), dt.datetime(2013, 9, 25), 95),
                (dt.datetime(2013, 9, 25), dt.datetime(2014, 8, 6), 424),
                (dt.datetime(2014, 8, 6), dt.datetime(2014, 9, 23), 151),
                (dt.datetime(2014, 9, 23), dt.datetime(2015, 6, 22), 193),
                (dt.datetime(2015, 6, 22), dt.datetime(2015, 6, 26), 12),
                (dt.datetime(2015, 6, 26), dt.datetime(2015, 7, 28), 283),
                (dt.datetime(2015, 7, 28), dt.datetime(2015, 8, 2), 27),
                (dt.datetime(2015, 8, 2), dt.datetime(2015, 10, 12), 292),
                # (dt.datetime(2015, 10, 12), dt.datetime(2016, 5, 27), -5),  # bad snow measurements for that frame
                # (dt.datetime(2016, 5, 27), dt.datetime(2016, 6, 30), 176),  # bad snow measurements for that frame
                (dt.datetime(2016, 6, 30), dt.datetime(2016, 7, 21), 129),
                (dt.datetime(2016, 7, 21), dt.datetime(2016, 9, 14), 317),
                (dt.datetime(2016, 9, 14), dt.datetime(2016, 10, 17), 48),
                (dt.datetime(2016, 10, 17), dt.datetime(2017, 7, 7), 294),
                (dt.datetime(2017, 7, 7), dt.datetime(2017, 7, 26), 132),
                (dt.datetime(2017, 7, 26), dt.datetime(2017, 10, 14), 246),
                (dt.datetime(2017, 10, 14), dt.datetime(2018, 6, 22), 223),
                (dt.datetime(2018, 6, 22), dt.datetime(2018, 7, 16), 135),
                (dt.datetime(2018, 7, 16), dt.datetime(2018, 9, 30), 393),
                (dt.datetime(2018, 9, 30), dt.datetime(2019, 6, 24), 182),
                (dt.datetime(2019, 6, 24), dt.datetime(2019, 7, 17), 179),
                (dt.datetime(2019, 7, 17), dt.datetime(2019, 10, 4), 370)]
            # (dt.datetime(2019, 10, 4), dt.datetime(2020, 7, 21), 362)]

            Visualizer.change_result_plot_subfolder(f"scatter_compare")

            if tasks["pegel_vs_measured_scatter_compare"]:
                no_gui_manager.compare_measured_ablation_measured_pegel_and_measured(
                    pegel_time_spans, max_est_measures=0, recalculate=False)
                no_gui_manager.compare_measured_ablation_measured_pegel_and_measured(
                    pegel_time_spans, max_est_measures=100, recalculate=False)

            if tasks["pegel_vs_modeled_scatter_compare"]:
                no_gui_manager.compare_measured_ablation_measured_pegel_and_modeled(
                    pegel_time_spans, max_est_measures=0, recalculate=False)

    else:
        """
        Order matters here, cause all need the gui_main_frame
        So each singleton is saved in a singleton variable in the corresponding file. So every file can then access
        those singletons by including the module    
        """
        #
        gui_main.create_singleton()
        navigation_bar.create_singleton()
        info_bar.create_singleton()
        frame_scope.create_singleton()
        frame_energy_balance.create_singleton()
        frame_prepare_measurements.create_singleton()
        frame_conversion.create_singleton()
        frame_plot.create_singleton()
        frame_download.create_singleton()
        frame_mean.create_singleton()
        frame_read.create_singleton()
        version_bar.create_singleton()

        gui_main.singleton.mainloop()
