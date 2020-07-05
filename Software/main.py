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

        self.years_looked_at = list(range(2012, 2020))
        self.startTime = dt.datetime(self.years_looked_at[0], 10, 1)  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = dt.datetime(self.years_looked_at[-1], 9, 30)  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.pickle_file_name = "multiple_measurements_singleton.pkl"
        self.simulation_accuracy = 0.0001
        self.use_tongue_only = True
        self.high_res_rad_grid = True
        height_level_step_width = 25

        self.subfolder_name = f"height_level_step_width_{height_level_step_width}"

        if self.use_tongue_only:
            self.subfolder_name += "_tongue"
        if self.high_res_rad_grid:
            self.subfolder_name += "_radGridHighRes"
        visualizer.singleton.change_result_plot_subfolder(self.subfolder_name)

    def run(self):
        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        reader.singleton.fetch_file_metadata()

        if not os.path.exists(self.pickle_file_name) or not cfg["USE_PICKLE_FOR_SAVING_TIME"] or True:
            res = dt.timedelta(days=1)

            reader.singleton.read_meterologic_file_to_objects(starttime=self.startTime,
                                                              endtime=self.endTime,
                                                              resolution_by_percentage=100,
                                                              resolution_by_time_interval=None)

            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

            multiple_measurements.singleton.correct_snow_measurements_for_scope()
            multiple_measurements.singleton.calculate_snow_height_deltas_for_scope()
            multiple_measurements.singleton.sum_measurements_by_time_interval(res)

            # with open(self.pickle_file_name, 'wb') as f:
            #     pickle.dump(multiple_measurements.singleton, f)
            #
            # #
            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

            multiple_measurements.singleton.fix_invalid_summed_measurements_for_scope()



            radiations_at_station = pickle.load(open(f"outputData/{self.subfolder_name}/pickle_radiations_at_station.pkl", "rb"))
            height_level_objects = pickle.load(open(f"outputData/{self.subfolder_name}/pickle_height_level_objects.pkl", "rb"))

            # for now create yearly height level objects .. this will probably be over-thinked again and will be different later TODO

            snowings_per_day_for_height_levels_starting_value = list(
                reversed(np.linspace(0.01, 0.1, len(height_level_objects) // 2)))
            snowings_per_day_for_height_levels_starting_value += [0] * (
                        len(height_level_objects) - len(snowings_per_day_for_height_levels_starting_value))

            meteorologic_years = dict()

            for year in self.years_looked_at[:-1]:
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

                        multiple_measurements.singleton.simulate(height_level, radiations_at_station)

                        if height_level.is_continuously_snow_laying():
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

            with open(f"outputData/{self.subfolder_name}/meteorologic_years.pkl", "wb") as f:
                pickle.dump(meteorologic_years, f)

            # with open(f"outputData/{self.subfolder_name}/meteorologic_years.pkl", 'rb') as f:
            #     meteorologic_years = pickle.load(f)

            with open("multiple_measurements_singleton_filled.pkl", 'wb') as f:
                pickle.dump(multiple_measurements.singleton, f)

            # with open("multiple_measurements_singleton_filled.pkl", 'rb') as f:
            #     multiple_measurements.singleton = pickle.load(f)

            # visualizer.singleton.show_plots = True

            visualizer.singleton.plot_comparison_of_years(meteorologic_years,
                                                          save_name=f"req_water_compare_{self.years_looked_at[0]}_{self.years_looked_at[-1]}")

            for year in self.years_looked_at[:-1]:
                visualizer.singleton.plot_shape(meteorologic_years[year], "inputData/AWS_Station.shp",
                                                "inputData/equality_line_2018.shp", only_tongue=self.use_tongue_only,
                                                save_name=f"pasterze_water_needed_{year}")

                # total_meltwater = multiple_measurements.singleton.get_total_theoretical_meltwater_per_square_meter_for_current_scope_with_summed_measurements()
                # swes = multiple_measurements.singleton.calculate_water_input_through_snow_for_scope()

                # visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("total_snow_depth", ), "m",
                #                                           use_summed_measurements=True,
                #                                           save_name="height_lvls")

                visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("total_snow_water_equivalent",), "l",
                                                          use_summed_measurements=True,
                                                          save_name=f"snow_water_equivalent_{year}")
                continue
                # visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("artificial_snow_water_equivalent",), "l",
                #                                           use_summed_measurements=True,
                #                                           save_name="height_lvls")

                # visualizer.singleton.plot_components_lvls(height_level_objects, ("air_pressure",), "m",
                #                                           use_summed_measurements=True,
                #                                           save_name="air_pressure")

                # visualizer.singleton.plot_components_lvls(height_level_objects, ("temperature",), "m",
                #                                           use_summed_measurements=True,
                #                                           save_name="temperature")

                # visualizer.singleton.plot_components_lvls(height_level_objects, ("temperature",), "m",
                #                                           use_summed_measurements=True,
                #                                           save_name="temperature")

                # visualizer.singleton.plot_components(("total_snow_depth", "snow_depth_natural", "snow_depth_artificial"),
                #                                      r"$m$", ("theoretical_melt_water_per_sqm",), r"$l/m^2$",
                #                                      use_summed_measurements=True, save_name="pasterze_0_with_albedo")

                # visualizer.singleton.plot_components(("total_snow_depth",),
                #                                      r"$m$", ("albedo",), "",
                #                                      use_summed_measurements=True)

                # visualizer.singleton.plot_components_lvls(height_level_objects, ("snow_depth_delta_artificial",), "m",
                #                                           use_summed_measurements=True,
                #                                           save_name="snow_depth_delta_artificial")

                # visualizer.singleton.plot_single_component("theoretical_melt_water_per_sqm", "m", use_summed_measurements=True)

                exit()

            if cfg["USE_PICKLE_FOR_SAVING_TIME"]:
                with open(self.pickle_file_name, 'wb') as f:
                    pickle.dump(multiple_measurement_singleton, f)
        else:
            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

        total_meltwater = multiple_measurements.singleton.get_total_theoretical_meltwater_per_square_meter_for_current_scope_with_summed_measurements()

        swes = multiple_measurements.singleton.calculate_water_input_through_snow_for_scope()
        total_swe = sum(swes)
        print(total_swe)

        print(f"{int(total_meltwater-total_swe)} liters water deficit per square "
              f"meter from {self.startTime} till {self.endTime}")

    def run_without_calculations(self):
        with open(f"outputData/{self.subfolder_name}/meteorologic_years.pkl", 'rb') as f:
            meteorologic_years = pickle.load(f)

        with open("multiple_measurements_singleton_filled.pkl", 'rb') as f:
            multiple_measurements.singleton = pickle.load(f)

        visualizer.singleton.plot_comparison_of_years(meteorologic_years,
                                                      save_name=f"req_water_compare_{self.years_looked_at[0]}_{self.years_looked_at[-1]}")

        for year in self.years_looked_at[:-1]:
            multiple_measurements.singleton.reset_scope_to_all()
            multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            fix_lower_limit = 4000 if self.use_tongue_only else 0
            visualizer.singleton.plot_shape(meteorologic_years[year], "inputData/AWS_Station.shp",
                                            "inputData/equality_line_2018.shp", only_tongue=self.use_tongue_only,
                                            fix_lower_limit=fix_lower_limit, fix_upper_limit=7500,
                                            save_name=f"pasterze_water_needed_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("natural_snow_water_equivalent",), "l",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True,
                                                      save_name=f"natural_snow_water_equivalent_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("albedo",), "l",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True,
                                                      save_name=f"albedo{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("artificial_snow_water_equivalent",), "l",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True,
                                                      save_name=f"artificial_snow_water_equivalent_{year}")

            visualizer.singleton.plot_components_lvls(meteorologic_years[year], ("total_snow_water_equivalent",), "l",
                                                      use_summed_measurements=True, show_estimated_measurement_areas=True,
                                                      save_name=f"total_snow_water_equivalent_{year}")


if __name__ == "__main__":
    if not cfg["GUI"]:
        no_gui_manager = NoGuiManager()
        # no_gui_manager.run()
        no_gui_manager.run_without_calculations()

    else:
        """
        Order matters here, cause all need the gui_main_frame
        So each singleton is saved in a singleton variable in the corresponding file. So every file can then access
        those singletons by including the module    
        """
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
