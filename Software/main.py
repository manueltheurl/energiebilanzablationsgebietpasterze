"""
This software was written for a bachelor thesis in 2019
The title of the bachelor thesis is "Energiebilanz im Ablationsgebiet der Pasterze"
The thesis can be found via TODO

TODO Rights .. open source .. and that stuff

@author Manuel Theurl
"""

from manage_config import cfg
import datetime as dt
import os
import threading
import multiple_measurements
import reader
import sys
import pickle
import numpy as np
from height_level import HeightLevel
import copy

sys.path.append("GUI")


# The gui is constructed as singletons .. this order therefor has to be maintained
import gui_main_frame as gui_main
import navigation_bar
import version_bar
import info_bar

import frame_plot
import frame_energy_balance
import frame_download
import frame_read
import frame_energy_balance as frame_scope
import frame_sum
import visualizer
from height_level import MeteorologicalYear


class NoGuiManager:
    def __init__(self):
        self.path_to_meteorologic_measurements = "../Meteorologic_data/PAS_10min.csv"
        # TODO well seems like it actually is a hydrologic year .. maybe change that some time
        self.meteorologic_years_looked_at = [2012, 2013, 2014, 2016, 2017, 2018]  # 2015 is baad
        self.startTime = dt.datetime(self.meteorologic_years_looked_at[0], 10, 1)  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = dt.datetime(self.meteorologic_years_looked_at[-1]+1, 9, 30)  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
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

    def run_calculations(self):
        print("STARTING WITH THE CALCULATIONS")
        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        reader.singleton.fetch_file_metadata()

        if not os.path.exists(self.pickle_multiple_measurement_singleton) or not cfg["USE_PICKLE_FOR_SAVING_TIME"] or True:
            # reader.singleton.read_meterologic_file_to_objects(starttime=self.startTime,
            #                                                   endtime=self.endTime,
            #                                                   resolution_by_percentage=None,
            #                                                   resolution_by_time_interval=None)
            #
            # multiple_measurements.singleton.correct_snow_measurements_for_scope()
            # multiple_measurements.singleton.calculate_snow_height_deltas_for_scope()
            # multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(hours=self.hourly_resolution))
            # multiple_measurements.singleton.fix_invalid_summed_measurements_for_scope()
            #
            # if int(cfg["ARTIFICIAL_SNOWING_USE_WET_BULB_TEMPERATURE"]):
            #     multiple_measurements.singleton.calculate_wetbulb_temperature_for_summed_scope()
            #
            # with open(self.pickle_multiple_measurement_singleton, 'wb') as f:
            #     pickle.dump(multiple_measurements.singleton, f)

            with open(self.pickle_multiple_measurement_singleton, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

            radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))
            height_level_objects = pickle.load(open(f"outputData/{self.subfolder_name}/{self.pickle_height_levels_objects}", "rb"))

            snowings_per_day_for_height_levels_starting_value = list(
                reversed(np.linspace(0.01, 0.1, len(height_level_objects) // 2)))
            snowings_per_day_for_height_levels_starting_value += [0] * (
                        len(height_level_objects) - len(snowings_per_day_for_height_levels_starting_value))

            meteorologic_years = dict()

            for year in self.meteorologic_years_looked_at:
                print(f"___ Looking at meteorologic year {year} ___")
                meteorologic_years[year] = MeteorologicalYear(copy.deepcopy(height_level_objects))
                multiple_measurements.singleton.reset_scope_to_all()
                multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
                    dt.datetime(year, 10, 1), dt.datetime(year+1, 9, 30))

                for i, height_level in enumerate(meteorologic_years[year].height_level_objects):

                    """ Lets try to find the optimum amount of snowing for not loosing mass """
                    print("Doing calculations for height level", height_level)
                    current_snowing_per_day = snowings_per_day_for_height_levels_starting_value[i]
                    current_delta = None

                    while True:
                        print("Snowing per day", round(current_snowing_per_day*1000, 1), "mm", current_delta)
                        height_level.clear_simulated_measurements()
                        height_level.artificial_snowing_per_day = current_snowing_per_day

                        liters_melted_anyways = multiple_measurements.singleton.simulate(height_level, radiations_at_station)
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

                print("Overall water needed:", round(meteorologic_years[year].overall_amount_of_water_needed_in_liters/1000, 1), "m^3")

            with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", "wb") as f:
                pickle.dump(meteorologic_years, f)

            with open("multiple_measurements_singleton_filled.pkl", 'wb') as f:
                pickle.dump(multiple_measurements.singleton, f)

    def run_visualizations(self):
        print("STARTING WITH THE VISUALIZATIONS")
        visualizer.singleton.change_result_plot_subfolder(f"{self.subfolder_name}_h{self.hourly_resolution}")

        with open(f"outputData/{self.subfolder_name}/{self.pickle_meteorological_years}", 'rb') as f:
            meteorologic_years = pickle.load(f)
        # height_level_objects = pickle.load(
        #     open(f"outputData/{self.subfolder_name}/pickle_height_level_objects_filled.pkl", "rb"))
        # with open("multiple_measurements_singleton_filled.pkl", 'rb') as f:
        #     multiple_measurements.singleton = pickle.load(f)
        with open(self.pickle_multiple_measurement_singleton, 'rb') as f:
            multiple_measurements.singleton = pickle.load(f)

        radiations_at_station = pickle.load(open(f"outputData/{self.pickle_radiations_at_station}", "rb"))

        visualizer.singleton.plot_comparison_of_years(meteorologic_years,
                                                      save_name=f"req_snow_compare_{self.meteorologic_years_looked_at[0]}_{self.meteorologic_years_looked_at[-1]}")

        visualizer.singleton.plot_day_of_ice_exposures_for_years_at_height(meteorologic_years, cfg["AWS_STATION_HEIGHT"], radiations_at_station,
                                                                           save_name=f"day_of_ice_exposure_{self.meteorologic_years_looked_at[0]}_{self.meteorologic_years_looked_at[-1]}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

        fix_lower_limit = 3 if self.use_tongue_only else 0
        fix_upper_limit = 7.5

        # # TODO for whole pasterze, equality_line_2018 from all hast to be taken
        visualizer.singleton.plot_pasterze(meteorologic_years, self.meteorologic_years_looked_at, "inputData/AWS_Station.shp",
                                           "inputData/equality_line_2018.shp", only_tongue=self.use_tongue_only,
                                           fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                           save_name=f"pasterze_water_needed_{self.meteorologic_years_looked_at[0]}_{self.meteorologic_years_looked_at[-1]}_")

        visualizer.singleton.plot_compare_water_and_height(self.meteorologic_years_looked_at, meteorologic_years,
                                                           save_name=f"water_vs_height_{self.meteorologic_years_looked_at[0]}_{self.meteorologic_years_looked_at[-1]}")

        for year in self.meteorologic_years_looked_at:
            multiple_measurements.singleton.reset_scope_to_all()
            multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            visualizer.singleton.plot_components_lvls([
                meteorologic_years[year].get_height_level_close_to_height(cfg["AWS_STATION_HEIGHT"])],
                ("total_snow_water_equivalent", "artificial_snow_water_equivalent", "natural_snow_water_equivalent"),
                "m w. e.", factor=1/1000, stack_fill=True,
                use_summed_measurements=True, show_estimated_measurement_areas=True,
                save_name=f"all_snow_water_equivalents_{year}_for_height_{int(cfg['AWS_STATION_HEIGHT'])}")

            visualizer.singleton.plot_compare_water_and_height([year], meteorologic_years,
                                                               save_name=f"water_vs_height_{year}")

            visualizer.singleton.plot_day_of_ice_exposures_for_year(year, meteorologic_years, radiations_at_station,
                                                           save_name=f"day_of_ice_exposure_{year}")

            visualizer.singleton.plot_pasterze(meteorologic_years, [year], "inputData/AWS_Station.shp",
                                            f"inputData/equality_line_{year}.shp", only_tongue=self.use_tongue_only,
                                               fix_lower_limit=fix_lower_limit, fix_upper_limit=fix_upper_limit,
                                               save_name=f"pasterze_water_needed_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("natural_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"natural_snow_water_equivalent_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("artificial_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"artificial_snow_water_equivalent_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("total_snow_water_equivalent",), "m w. e.",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True, factor=1/1000,
                                                      save_name=f"total_snow_water_equivalent_{year}")

            # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
            # visualizer.singleton.plot_components_lvls(meteorologic_years[year].get_distributed_amount_of_height_levels(5), ("albedo",), "",
            #                                           use_summed_measurements=True, show_estimated_measurement_areas=True,
            #                                           save_name=f"albedo{year}")

    def run_calculations_bachelor(self, type_, year, only_summer=False):
        """
        type_ either adapted or original
        """
        print(f"\nRunning bachelor calaculations {type_} for year {year} (only summer: {only_summer}):")
        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)
        # reader.singleton.fetch_file_metadata()

        if not os.path.exists(self.pickle_multiple_measurement_singleton) or not cfg["USE_PICKLE_FOR_SAVING_TIME"] or True:
            if only_summer:
                reader.singleton.read_meterologic_file_to_objects(starttime=dt.datetime(year, 7, 1),
                                                                  endtime=dt.datetime(year, 7, 30),
                                                                  resolution_by_percentage=None,
                                                                  resolution_by_time_interval=None)
            else:
                reader.singleton.read_meterologic_file_to_objects(starttime=dt.datetime(year, 1, 1),
                                                                  endtime=dt.datetime(year, 12, 31),
                                                                  resolution_by_percentage=None,
                                                                  resolution_by_time_interval=None)

            multiple_measurements.singleton.correct_snow_measurements_for_scope()
            multiple_measurements.singleton.calculate_snow_height_deltas_for_scope()
            multiple_measurements.singleton.cumulate_ablation_for_scope()
            # multiple_measurements.singleton.correct_long_wave_measurements_for_scope()  # TODO if this is used do it above as well
            multiple_measurements.singleton.correct_short_wave_measurements_for_scope()  # TODO if this is used do it above as well, and it will be different, as artificial snowing is done

            if type_ == "original":
                multiple_measurements.singleton.calculate_energy_balance_for("scope")
                multiple_measurements.singleton.convert_energy_balance_to_water_rate_equivalent_for("scope")
                multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))
                multiple_measurements.singleton.calculate_measured_and_theoretical_ablation_values_for_summed()

            elif type_ == "adapted":
                multiple_measurements.singleton.sum_measurements_by_time_interval(
                    dt.timedelta(hours=self.hourly_resolution))

                # multiple_measurements.singleton.fix_invalid_summed_measurements_for_scope()

                multiple_measurements.singleton.calculate_energy_balance_for("summed")
                multiple_measurements.singleton.convert_energy_balance_to_water_rate_equivalent_for("summed")
                multiple_measurements.singleton.calculate_measured_and_theoretical_ablation_values_for_summed()

            measured_ablations = multiple_measurements.singleton.get_all_of("relative_ablation_measured", use_summed_measurements=True)
            modelled_ablations = multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True)

            print("Nones measured_ablations:", sum(x is None for x in measured_ablations))
            print("Nones modelled_ablations:", sum(x is None for x in modelled_ablations))
            for i in range(len(measured_ablations)):
                measured_ablations[i] = 0 if measured_ablations[i] is None else measured_ablations[i]
            for i in range(len(modelled_ablations)):
                modelled_ablations[i] = 0 if modelled_ablations[i] is None else modelled_ablations[i]

            modelled_ablation = sum(modelled_ablations)
            measured_ablation = sum(measured_ablations)
            reality_factor = measured_ablation / modelled_ablation

            # albedo  TODO take a look at this again .. sometimes albedo > 100%? how is that possible, and if swe in is 0 zerodivision error
            # visualizer.singleton.plot_single_component("albedo", "", use_summed_measurements=True,
            #                                            save_name=f"albedo_{year}_{type_}_onlysummer_{only_summer}")

            # visualizer.singleton.plot_components(("sensible_heat",), "W/m^2", ("temperature",), "°C", use_summed_measurements=True,
            #                                            save_name=f"sensible_heat_and_temperature")
            #
            # visualizer.singleton.plot_components(("sensible_heat",), "W/m^2", ("air_pressure",), "pa",
            #                                      use_summed_measurements=True,
            #                                      save_name=f"sensible_heat_and_air_pressure")
            #
            # visualizer.singleton.plot_components(("sensible_heat",), "W/m^2", ("wind_speed",), "m/s",
            #                                      use_summed_measurements=True,
            #                                      save_name=f"sensible_heat_and_wind_speed")

            # visualizer.singleton.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("albedo",), "-",
            #                                      use_summed_measurements=True,
            #                                      save_name=f"swinout")
            #
            # visualizer.singleton.plot_components(("sw_radiation_in", "sw_radiation_out"), "W/m^2", ("total_snow_depth",), "m",
            #                                      use_summed_measurements=True,
            #                                      save_name=f"snow_depth")

            print("Measured ablation", round(measured_ablation, 2))
            print("Modelled ablation",
                  round(modelled_ablation, 2))  # measured stays the same .. cause thats wont be affected
            print("Reality factor:", round(reality_factor, 2))


if __name__ == "__main__":
    if not cfg["GUI"]:
        no_gui_manager = NoGuiManager()
        # no_gui_manager.run_calculations()
        # no_gui_manager.run_visualizations()
        # no_gui_manager.run_bachelor_stuff()

        year = 2017
        # no_gui_manager.run_calculations_bachelor("original", year)
        # no_gui_manager.run_calculations_bachelor("adapted", year)
        # no_gui_manager.run_calculations_bachelor("original", year, only_summer=True)
        no_gui_manager.run_calculations_bachelor("adapted", year, only_summer=True)
    else:
        """
        Order matters here, cause all need the gui_main_frame
        So each singleton is saved in a singleton variable in the corresponding file. So every file can then access
        those singletons by including the module    
        """
        # TODO albedo in gui
        gui_main.create_singleton()
        navigation_bar.create_singleton()
        info_bar.create_singleton()
        frame_scope.create_singleton()
        frame_plot.create_singleton()
        frame_download.create_singleton()
        frame_sum.create_singleton()
        frame_read.create_singleton()
        version_bar.create_singleton()

        gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
        gui_thread.start()

        # gui_main.singleton.mainloop()
