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


class NoGuiManager:
    def __init__(self):
        self.path_to_meteorologic_measurements = "../Meteorologic_data/PAS_10min.csv"

        # read
        self.startTime = dt.datetime(2016, 10, 1)  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = dt.datetime(2019, 9, 30)  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.pickle_file_name = "multiple_measurements_singleton.pkl"

    def run(self):
        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        reader.singleton.fetch_file_metadata()

        # TODO NO ABLATION VALUES starting from october 2018

        if not os.path.exists(self.pickle_file_name) or not cfg["USE_PICKLE_FOR_SAVING_TIME"] or True:
            res = dt.timedelta(days=1)
            #
            # reader.singleton.read_meterologic_file_to_objects(starttime=self.startTime,
            #                                                   endtime=self.endTime,
            #                                                   resolution_by_percentage=100,
            #                                                   resolution_by_time_interval=None)
            # #
            # with open(self.pickle_file_name, 'wb') as f:
            #     pickle.dump(multiple_measurements.singleton, f)
            #
            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

            multiple_measurements.singleton.correct_snow_measurements_for_scope()
            multiple_measurements.singleton.calculate_snow_height_deltas_for_scope()
            multiple_measurements.singleton.sum_measurements_by_time_interval(res)
            # multiple_measurements.singleton.set_initial_snow_height_to_zero()  # not needed if not using model

            height_level_step_width = 25
            use_tongue_only = True
            high_res_rad_grid = True

            subfolder_name = f"height_level_step_width_{height_level_step_width}"

            if use_tongue_only:
                subfolder_name += "_tongue"
            if high_res_rad_grid:
                if use_tongue_only:
                    subfolder_name += "_radGridHighRes"

            radiations_at_station = pickle.load(open(f"outputData/{subfolder_name}/pickle_radiations_at_station.pkl", "rb"))
            height_level_objects = pickle.load(open(f"outputData/{subfolder_name}/pickle_height_level_objects.pkl", "rb"))

            visualizer.singleton.show_plots = True

            snowings_per_day_for_height_levels_starting_value = list(
                reversed(np.linspace(0.01, 0.04, len(height_level_objects) // 2)))
            snowings_per_day_for_height_levels_starting_value += [0] * (
                        len(height_level_objects) - len(snowings_per_day_for_height_levels_starting_value))

            # for i, height_level in enumerate(height_level_objects):
            #     print(height_level, height_level.mean_radiation)
            #
            # exit()

            for i, height_level in enumerate(height_level_objects):
                """ Lets try to find the optimum amount of snowing for not loosing mass """
                print("Doing calculations for height level", height_level)
                current_snowing_per_day = snowings_per_day_for_height_levels_starting_value[i]
                current_delta = None

                while True:
                    print("Snowing per day", round(current_snowing_per_day*1000, 1), "mm", current_delta)
                    height_level.clear_simulated_measurements()
                    multiple_measurements.singleton.simulate(height_level, radiations_at_station, current_snowing_per_day)

                    if height_level.is_continuously_snow_laying():
                        if current_delta is None:  # this will be true for the second iteration
                            current_delta = -0.01
                        else:
                            if current_delta > 0:
                                current_delta /= -2
                            else:
                                # reduced snowing and it is still too much -> stick with the bigger delta value
                                pass
                        if abs(current_delta) < 0.0001:
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

            total_overall_amount_of_water_in_liters = 0
            for height_level in height_level_objects:
                height_level: HeightLevel
                total_amount_water_for_height_level = height_level.get_mean_yearly_water_consumption_of_snow_canons_for_height_level_in_liters()
                print(height_level)
                print(f" - Total water needed: {round(total_amount_water_for_height_level/1000, 1)} m^3")
                print(f" - Water per square meter: {round(total_amount_water_for_height_level/height_level.area, 1)} liters")
                total_overall_amount_of_water_in_liters += total_amount_water_for_height_level

            print("Overall water needed:", round(total_overall_amount_of_water_in_liters/1000, 1), "m^3")

            visualizer.singleton.plot_shape(height_level_objects)

            # total_meltwater = multiple_measurements.singleton.get_total_theoretical_meltwater_per_square_meter_for_current_scope_with_summed_measurements()
            # swes = multiple_measurements.singleton.calculate_water_input_through_snow_for_scope()

            visualizer.singleton.plot_components_lvls(height_level_objects, ("total_snow_depth", ), "m",
                                                      use_summed_measurements=True,
                                                      save_name="height_lvls")

            visualizer.singleton.plot_components_lvls(height_level_objects, ("total_snow_water_equivalent",), "l",
                                                      use_summed_measurements=True,
                                                      save_name="height_lvls")

            visualizer.singleton.plot_components_lvls(height_level_objects, ("artificial_snow_water_equivalent",), "l",
                                                      use_summed_measurements=True,
                                                      save_name="height_lvls")

            exit()
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


if __name__ == "__main__":
    if not cfg["GUI"]:
        no_gui_manager = NoGuiManager()
        no_gui_manager.run()

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
