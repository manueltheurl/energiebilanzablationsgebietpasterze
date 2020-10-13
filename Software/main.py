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
import dill

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
import frame_sum
from visualizer import Visualizer
from hydrologic_year import HydrologicYear
from energy_balance import EnergyBalance
from measurement_handler import MeasurementHandler, save_measurement_handler, load_measurement_handler


class NoGuiManager:
    def __init__(self):
        """
        Class to run stuff without a gui. Specific knowledge about the software is needed.
        """
        self.path_to_meteorologic_measurements = "../Meteorologic_data/PAS_10min.csv"
        self.hydrologic_years_looked_at = [2012, 2013, 2014, 2016, 2017, 2018]  # 2015 is baad
        self.startTime = dt.datetime(self.hydrologic_years_looked_at[0], 10, 1)  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = dt.datetime(self.hydrologic_years_looked_at[-1]+1, 9, 30)  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.simulation_accuracy = 0.0001
        self.use_tongue_only = True
        self.no_debris = True
        self.high_res_rad_grid = True
        height_level_step_width = 25
        self.hourly_resolution = 24
        self.pickle_multiple_measurement_singleton = f"outputData/pickle_multiple_measurements_singleton_h{self.hourly_resolution}.pkl"
        self.pickle_meteorological_years = f"pickle_meteorologic_years_h{self.hourly_resolution}.pkl"
        self.pickle_height_levels_objects = f"pickle_height_level_objects.pkl"
        self.pickle_radiations_at_station = "pickle_radiations_at_station.pkl"
        self.subfolder_name = f"height_level_step_width_{height_level_step_width}"

        if self.use_tongue_only:
            self.subfolder_name += "_tongue"
        if self.no_debris:
            self.subfolder_name += "_noDebris"
        if self.high_res_rad_grid:  # this could be removed some day, if always the high rad grids are taken TODO
            self.subfolder_name += "_radGridHighRes"

    def run_calculations_height_levels(self):
        """

        :return:
        """
        print("STARTING WITH THE CALCULATIONS")
        recalculate = True

        Reader.add_file_path(self.path_to_meteorologic_measurements)

        if recalculate:
            Reader.read_meterologic_file_to_objects(starttime=self.startTime, endtime=self.endTime)
            self.combined_preparing_of_measurements(sum_hourly_resolution=24)
            # needed for the height adaptions of the meteorologic values
            MeasurementHandler.calculate_wetbulb_temperature_for_summed_scope()

            with open(self.pickle_multiple_measurement_singleton, 'wb') as f:
                pickle.dump(MeasurementHandler, f)
        else:
            with open(self.pickle_multiple_measurement_singleton, 'rb') as f:
                MeasurementHandler = pickle.load(f)

        radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))
        height_level_objects = pickle.load(open(f"outputData/{self.subfolder_name}/{self.pickle_height_levels_objects}", "rb"))

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
                dt.datetime(year, 10, 1), dt.datetime(year+1, 9, 30))

            for i, height_level in enumerate(hydrologic_years[year].height_level_objects):
                """ Lets try to find the optimum amount of snowing for not loosing mass """
                print("Doing calculations for height level", height_level)
                current_snowing_per_day = snowings_per_day_for_height_levels_starting_value[i]
                current_delta = None

                while True:
                    print("Snowing per day", round(current_snowing_per_day*1000, 1), "mm", current_delta)
                    height_level.clear_simulated_measurements()
                    height_level.artificial_snowing_per_day = current_snowing_per_day

                    liters_melted_anyways = MeasurementHandler.simulate(height_level, radiations_at_station)
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
                            print("Found good enough estimate:", round(current_snowing_per_day*1000, 1), "mm snowing per day needed")
                            print(f"Compensated {int(liters_melted_anyways)} liters/m^2 from beginning of meteorological year")
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

            print("Overall water needed:", round(hydrologic_years[year].overall_amount_of_water_needed_in_liters/1000, 1), "m^3")

        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", "wb") as f:
            pickle.dump(hydrologic_years, f)

        with open("multiple_measurements_singleton_filled.pkl", 'wb') as f:
            pickle.dump(MeasurementHandler, f)

    def run_visualizations_height_levels(self):
        """

        :return:
        """
        print("STARTING WITH THE VISUALIZATIONS")
        Visualizer.show_plots = False

        Visualizer.change_result_plot_subfolder(f"{self.subfolder_name}_h{self.hourly_resolution}")

        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", 'rb') as f:
            meteorologic_years = pickle.load(f)
        # height_level_objects = pickle.load(
        #     open(f"outputData/{self.subfolder_name}/pickle_height_level_objects_filled.pkl", "rb"))
        # with open("multiple_measurements_singleton_filled.pkl", 'rb') as f:
        #     MeasurementHandler = pickle.load(f)
        with open(self.pickle_multiple_measurement_singleton, 'rb') as f:
            MeasurementHandler = pickle.load(f)

        radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))

        Visualizer.plot_comparison_of_years(meteorologic_years,
                                                      save_name=f"req_snow_compare_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}")

        Visualizer.plot_day_of_ice_exposures_for_years_at_height(meteorologic_years, cfg["AWS_STATION_HEIGHT"], radiations_at_station,
                                                                           save_name=f"day_of_ice_exposure_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

        fix_lower_limit = 3 if self.use_tongue_only else 0
        fix_upper_limit = 7.5

        # # TODO for whole pasterze, equality_line_2018 from all hast to be taken
        Visualizer.plot_pasterze(meteorologic_years, self.hydrologic_years_looked_at, "inputData/AWS_Station.shp",
                                           "inputData/equality_line_2018.shp", only_tongue=self.use_tongue_only,
                                           fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                           save_name=f"pasterze_water_needed_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}_")

        Visualizer.plot_compare_water_and_height(self.hydrologic_years_looked_at, meteorologic_years,
                                                           save_name=f"water_vs_height_{self.hydrologic_years_looked_at[0]}_{self.hydrologic_years_looked_at[-1]}")

        for year in self.hydrologic_years_looked_at:
            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            Visualizer.plot_components_lvls([
                meteorologic_years[year].get_height_level_close_to_height(cfg["AWS_STATION_HEIGHT"])],
                ("total_snow_water_equivalent", "artificial_snow_water_equivalent", "natural_snow_water_equivalent"),
                "m w. e.", factor=1/1000, stack_fill=True,
                use_summed_measurements=True, show_estimated_measurement_areas=True,
                save_name=f"all_snow_water_equivalents_{year}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

            Visualizer.plot_compare_water_and_height([year], meteorologic_years,
                                                               save_name=f"water_vs_height_{year}")

            Visualizer.plot_day_of_ice_exposures_for_year(year, meteorologic_years, radiations_at_station,
                                                           save_name=f"day_of_ice_exposure_{year}")

            Visualizer.plot_pasterze(meteorologic_years, [year], "inputData/AWS_Station.shp",
                                            f"inputData/equality_line_{year}.shp", only_tongue=self.use_tongue_only,
                                               fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                               save_name=f"pasterze_water_needed_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("natural_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"natural_snow_water_equivalent_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("artificial_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"artificial_snow_water_equivalent_{year}")

            Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("total_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"total_snow_water_equivalent_{year}")

            # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
            # Visualizer.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("albedo",), "",
            #                                           use_summed_measurements=True, show_estimated_measurement_areas=True,
            #                                           save_name=f"albedo{year}")

    def run_calculations_bachelor(self, startime: dt.datetime, endtime: dt.datetime, pegel_measure, type_="new"):
        """

        :param startime:
        :param endtime:
        :param pegel_measure:
        :param type_:
        :return:
        """
        print(f"\nRunning bachelor calaculations {type_} for {startime.strftime('%d.%m.%Y')} till {endtime.strftime('%d.%m.%Y')}:")
        Reader.add_file_path(self.path_to_meteorologic_measurements)

        Reader.read_meterologic_file_to_objects(starttime=startime, endtime=endtime)

        self.combined_preparing_of_measurements(type_=type_)
        self.combined_calculation_of_energy_balance_and_all_associated_values(type_=type_)

        measured_ablations = MeasurementHandler.get_all_of("relative_ablation_measured", use_summed_measurements=True)
        modelled_ablations = MeasurementHandler.get_all_of("relative_ablation_modelled", use_summed_measurements=True)

        print("Nones measured_ablations:", sum(x is None for x in measured_ablations))
        print("Nones modelled_ablations:", sum(x is None for x in modelled_ablations))

        for i in range(len(measured_ablations)):
            measured_ablations[i] = 0 if measured_ablations[i] is None else measured_ablations[i]
        for i in range(len(modelled_ablations)):
            modelled_ablations[i] = 0 if modelled_ablations[i] is None else modelled_ablations[i]

        # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
        # Visualizer.plot_single_component("albedo", "", use_summed_measurements=True,
        #                                            save_name=f"albedo_{year}_{type_}_onlysummer_{only_summer}")

        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("temperature",), "°C", use_summed_measurements=True,
        #                                            save_name=f"sensible_heat_and_temperature")
        #
        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("air_pressure",), "pa",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"sensible_heat_and_air_pressure")
        #
        # Visualizer.plot_components(("sensible_heat",), "W/m^2", ("wind_speed",), "m/s",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"sensible_heat_and_wind_speed")

        # Visualizer.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("albedo",), "-",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"swinout")

        # Visualizer.plot_components(("albedo",), "-",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"albedo_normal")
        #
        # Visualizer.plot_components(("midday_albedo",), "-",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"albedo_midday")

        # Visualizer.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("total_snow_depth",), "m",
        #                                      use_summed_measurements=True,
        #                                      save_name=f"snow_depth")

        modelled_ablation = sum(modelled_ablations)
        measured_ablation = sum(measured_ablations)
        reality_factor_ablation = measured_ablation / modelled_ablation
        reality_factor_pegel = (pegel_measure/100) / modelled_ablation
        print("Measured ablation", round(measured_ablation, 2), "Pegel measure", pegel_measure/100)
        print("Modelled ablation",
              round(modelled_ablation, 2))  # measured stays the same .. cause thats wont be affected
        print("Reality factor ablation:", round(reality_factor_ablation, 2))
        print("Reality factor pegel:", round(reality_factor_pegel, 2))

    @staticmethod
    def combined_preparing_of_measurements(sum_hourly_resolution=24, type_="new"):
        """
        Basic steps that are used to prepare the measurements.
        :param sum_hourly_resolution:
        :param type_:
        :return:
        """
        # Preparations of measurements
        MeasurementHandler.correct_snow_measurements_for_scope()
        # MeasurementHandler.correct_long_wave_measurements_for_scope()
        MeasurementHandler.correct_short_wave_measurements_for_scope()
        MeasurementHandler.cumulate_ice_thickness_measures_for_scope(method="SameLevelPositiveFix")

        MeasurementHandler.calculate_snow_height_deltas_for_scope()

        if type_ == "new":
            MeasurementHandler.sum_measurements_by_time_interval(
                dt.timedelta(hours=sum_hourly_resolution))
            MeasurementHandler.fix_invalid_summed_measurements()

    @staticmethod
    def combined_calculation_of_energy_balance_and_all_associated_values(type_="new"):
        # do not forget to set scope before that
        if type_ == "new":
            MeasurementHandler.calculate_energy_balance_for("summed")
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for("summed")
            MeasurementHandler.convert_measured_and_modeled_rel_ablations_in_water_equivalents_for_summed()
        elif type_ == "original":
            MeasurementHandler.calculate_energy_balance_for("scope")
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for("scope")
            MeasurementHandler.sum_measurements_by_time_interval(dt.timedelta(days=1))
            MeasurementHandler.calculate_measured_and_theoretical_ablation_values_for_summed()

    def compare_measured_ablation_measured_pegel_and_modelled(self, type_, pegel_tuples):
        Visualizer.show_plots = False
        Visualizer.change_result_plot_subfolder(f"scatter_compare")
        recalculate = True

        if recalculate:
            Reader.add_file_path(self.path_to_meteorologic_measurements)
            Reader.read_meterologic_file_to_objects()
            self.combined_preparing_of_measurements(sum_hourly_resolution=24)

        for i, rs in enumerate([(0.001, 0.001), (0.002, 0.001), (0.003, 0.001), (0.004, 0.001)]):
            f_name = f"tmp/picklsave_{rs[0]}_z0snow{rs[1]}_type{type_}"
            if recalculate:
                EnergyBalance.set_new_roughness_parameters(rs[0], rs[1])
                MeasurementHandler.reset_scope_to_all()
                self.combined_calculation_of_energy_balance_and_all_associated_values()

                save_measurement_handler(f_name)

            load_measurement_handler(f_name)

            max_estimated_ablation_measures_percent = 0

            # """ Statistics """
            # StatsPrinter.compare_pegel_measured_and_modelled_for_time_intervals(
            #     pegel_tuples, heading=f"\nSetup: z0 ice: {rs[0]} z0 snow {rs[1]}, {type_}) max est. abl. measures {max_estimated_ablation_measures_percent}",
            #     max_estimated_ablation_measures_percent=max_estimated_ablation_measures_percent)

            """ Plotting """
            Visualizer.plot_scatter_measured_modelled_ablation(
                pegel_tuples, save_name=f"z0ice{rs[0]}z0 snow{rs[1]} ({max_estimated_ablation_measures_percent}% est. abl. measures)",
                max_estimated_ablation_measures_percent=max_estimated_ablation_measures_percent, measured_per_day_has_to_be_above_mm=1)

            # if not i:
            #     Visualizer.plot_components(("total_snow_depth",), "m", use_summed_measurements=False,
            #                                          save_name=f"total_snow_depth")

    def ablation_cumulation_test(self):
        Visualizer.change_result_plot_subfolder(f"ablation_cumulation")
        Visualizer.show_plots = False

        # Reader.add_file_path(self.path_to_meteorologic_measurements)
        # Reader.read_meterologic_file_to_objects()
        # MeasurementHandler.change_measurement_resolution_by_start_end_time(dt.datetime(2016, 1, 1), dt.datetime(2019, 1, 1))
        #
        # with open("tmp/tmpi.pkl", 'wb') as f:
        #     pickle.dump(MeasurementHandler, f)

        with open("tmp/tmpi.pkl", 'rb') as f:
            MeasurementHandler = pickle.load(f)

        MeasurementHandler.cumulate_ice_thickness_measures_for_scope(method="SameLevelPositiveFix")

        Visualizer.plot_components(("cumulated_ice_thickness",), "m",  use_summed_measurements=False,
                                             save_name=f"cum_ice")


if __name__ == "__main__":
    if not cfg["GUI"]:
        no_gui_manager = NoGuiManager()

        """ Height level calculations with visualizations """
        # no_gui_manager.run_calculations_height_levels()
        # no_gui_manager.run_visualizations_height_levels()

        """ Single time frame comparison with measurement fixing """
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2013, 8, 29), dt.datetime(2013, 9, 25), 95)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 7, 7), dt.datetime(2017, 7, 26), 132)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 7, 26), dt.datetime(2017, 10, 14), 246)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2017, 10, 14), dt.datetime(2018, 6, 22), 223)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 6, 22), dt.datetime(2018, 7, 16), 135)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 7, 16), dt.datetime(2018, 9, 30), 393)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2018, 9, 30), dt.datetime(2019, 6, 24), 182)
        # no_gui_manager.run_calculations_bachelor(dt.datetime(2019, 6, 24), dt.datetime(2019, 7, 17), 179)

        """ Combined time frame comparison with measurement fixing """

        # no_gui_manager.ablation_cumulation_test()
        # exit()

        """ Comparison of measured and modeled ablation and pegel measurement """
        tups = [
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

        no_gui_manager.compare_measured_ablation_measured_pegel_and_modelled("adapted", tups)

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
        frame_sum.create_singleton()
        frame_read.create_singleton()
        version_bar.create_singleton()
        #
        # navigation_bar.singleton.show_sum_frame()
        # navigation_bar.singleton.show_prepare_frame()
        # navigation_bar.singleton.show_energy_balance_frame()
        # navigation_bar.singleton.show_plot_frame()
        # navigation_bar.singleton.show_scope_frame()
        # navigation_bar.singleton.show_read_frame()

        gui_main.singleton.mainloop()

        # gui_thread = threading.Thread(target=)
        # gui_thread.start()



        # gui_main.singleton.mainloop()
