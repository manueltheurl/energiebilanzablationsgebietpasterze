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

# The gui is constructed as singletons .. this order therefor has to be maintained
import GUI.gui_main_frame as gui_main
import GUI.navigation_bar as navigation_bar
import GUI.info_bar as info_bar
import GUI.frame_plot as frame_plot
import GUI.frame_energy_balance as frame_scope
import GUI.frame_model as frame_model
import GUI.frame_read as frame_read
import GUI.frame_energy_balance as frame_energy_balance
import GUI.frame_sum as frame_sum
import visualizer


class Manager:
    def __init__(self):
        self.path_to_meteorologic_measurements = cfg["DATA_PATH"]
        self.startTime = "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.read()
        self.calculate()
        self.visualize()

    def read(self):

        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        multiple_measurements.singleton.fetch_file_metadata()

        reader.singleton.read_meterologic_file_to_objects(starttime=None,
                                                          endtime=None,
                                                          resolution_by_percentage=10,
                                                          resolution_by_time_interval=None)

        # meteorologic_measurements.change_measurement_resolution_by_percentage(1)
        # meteorologic_measurements.change_measurement_resolution_by_time_interval(dt.timedelta(days=1))

    def calculate(self):

        multiple_measurements.singleton.calculate_energy_balance_for_all()
        # multiple_measurements.singleton.sum_measurements_by_amount(30)

        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=5))

    def visualize(self):
        # print("BALA")
        # visualizer.plot_total_energy_balance()
        # visualizer.singleton.plot_summed_total_energy_balance()

        visualizer.singleton.plot_periodic_trend_eliminated("total_energy_balance")
        visualizer.singleton.plot_periodic_trend_eliminated("sw_radiation_in")
        visualizer.singleton.plot_periodic_trend_eliminated("sw_radiation_out")
        visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_in")
        visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_out")
        # visualizer.singleton.plot_periodic_trend_eliminated("sensible_heat")
        # visualizer.singleton.plot_periodic_trend_eliminated("latent_heat")

        # visualizer.plot_energy_balance_components(latent_heat=True)


if __name__ == "__main__":
    if cfg["NO_GUI"]:
        manager = Manager()

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
        frame_model.create_singleton()
        frame_sum.create_singleton()
        frame_read.create_singleton()

        # JUST FOR TESTING DELETE FROM HERE
        reader.singleton.add_file_path("PAS_10min_SHORT.csv")

        read_in_measurements = reader.singleton.read_meterologic_file_to_objects()

        reader.singleton.fetch_file_metadata()

        info_bar_text_list = [
            "Measurements: " + str(multiple_measurements.singleton.get_measurement_amount()),
            "First: " + str(multiple_measurements.singleton.get_date_of_first_measurement()),
            "Last: " + str(multiple_measurements.singleton.get_date_of_last_measurement()),
            "Time resolution: " + str(multiple_measurements.singleton.get_time_resolution()) + " minutes"
        ]
        info_bar.singleton.change_read_info("\t".join(info_bar_text_list))

        frame_energy_balance.singleton.fill_fields_with_read_in_values()
        multiple_measurements.singleton.calculate_energy_balance_for_scope()

        info_bar_text = ""
        sum_by_amount = "10"
        sum_by_time_interval = None

        if sum_by_amount is not None and sum_by_amount.isdigit():
            info_bar_text += "One summed measurement contains: " + str(sum_by_amount)
            multiple_measurements.singleton.sum_measurements_by_amount(int(sum_by_amount))
            frame_plot.singleton.enable_option_to_use_summed_measurements()
        elif sum_by_time_interval is not None:
            info_bar_text += "Measurements every " + str(sum_by_time_interval.seconds // 60) + " minutes summed"
            multiple_measurements.singleton.sum_measurements_by_time_interval(sum_by_time_interval)
            frame_plot.singleton.enable_option_to_use_summed_measurements()

        info_bar.singleton.change_sum_info(info_bar_text)



        navigation_bar.singleton.show_plot_frame()

        # TILL HERE

        gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
        gui_thread.start()

        # gui_main.singleton.mainloop()
