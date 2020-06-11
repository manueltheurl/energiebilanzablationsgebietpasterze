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
            #
            # with open(self.pickle_file_name, 'wb') as f:
            #     pickle.dump(multiple_measurements.singleton, f)
            #
            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)


            # multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            #     starttime=dt.datetime(2016, 11, 1))

            # TODO if this is really going to be a bigger project, maybe summarize single and mean measurement (inheritance) for making it possible to calc the energy balance for a mean measurement as well
            # Maybe just treat them exactly alike .. single measurement would then have a start and ending time but that would not even be bad and would make it a bit easier probably

            # multiple_measurements.singleton.cumulate_ablation_for_scope()
            multiple_measurements.singleton.correct_snow_measurements_for_scope()

            multiple_measurements.singleton.calculate_snow_height_deltas_for_scope()
            multiple_measurements.singleton.simulate_artificial_snowing()

            # multiple_measurements.singleton.change_albedo_for_snowy_times()

            # Now do the artificial part
            # snow events, albedo change, bulk coefficient change

            # multiple_measurements.singleton.calculate_energy_balance_for_scope()

            # multiple_measurements.singleton.convert_energy_balance_to_water_rate_equivalent_for_scope()

            multiple_measurements.singleton.sum_measurements_by_time_interval(res)
            # multiple_measurements.singleton.set_initial_snow_height_to_zero()  # not needed if not using model

            radiations_at_station = pickle.load(open("pickle_radiations_at_station", "rb"))
            height_level_objects = pickle.load(open("pickle_height_level_objects", "rb"))

            multiple_measurements.singleton.simulate(height_level_objects, radiations_at_station)

            # total_meltwater = multiple_measurements.singleton.get_total_theoretical_meltwater_per_square_meter_for_current_scope_with_summed_measurements()
            # swes = multiple_measurements.singleton.calculate_water_input_through_snow_for_scope()

            visualizer.singleton.show_plots = True

            visualizer.singleton.plot_components_lvls(height_level_objects, use_summed_measurements=True,
                                                      save_name="height_lvls")

            # visualizer.singleton.plot_components(("total_snow_depth", "snow_depth_natural", "snow_depth_artificial"),
            #                                      r"$m$", ("theoretical_melt_water_per_sqm",), r"$l/m^2$",
            #                                      use_summed_measurements=True, save_name="pasterze_0_with_albedo")

            # visualizer.singleton.plot_components(("total_snow_depth",),
            #                                      r"$m$", ("albedo",), "",
            #                                      use_summed_measurements=True)



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
