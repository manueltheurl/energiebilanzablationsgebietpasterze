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

# The gui is constructed as singletons .. this order therefor has to be maintained
import gui_main_frame as gui_main
import navigation_bar
import info_bar
import frame_plot
import frame_energy_balance
import frame_download
import frame_read
import frame_energy_balance as frame_scope
import frame_sum
import visualizer
TEST = False
sys.path.append("GUI")


class NoGuiManager:
    def __init__(self):
        self.path_to_meteorologic_measurements = "../Meteorologic_data/PAS_10min.csv"

        # read
        self.startTime = None  # "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = None  # "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"
        self.pickle_file_name = "multiple_measurements_singleton.pkl"

    def run(self):
        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        reader.singleton.fetch_file_metadata()

        if not os.path.exists(self.pickle_file_name):
            reader.singleton.read_meterologic_file_to_objects(starttime=self.startTime,
                                                              endtime=self.endTime,
                                                              resolution_by_percentage=100,
                                                              resolution_by_time_interval=None)
            multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
                starttime=dt.datetime(2016, 11, 1))
            multiple_measurements.singleton.calculate_energy_balance_for_scope()
            multiple_measurements.singleton.cumulate_ablation_for_scope()
            multiple_measurements.singleton.check_for_snow_covering_for_scope()  # yet TODO
            multiple_measurements.singleton.convert_energy_balance_to_water_equivalent_for_scope()

            multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=2))

            multiple_measurement_singleton = multiple_measurements.singleton

            with open(self.pickle_file_name, 'wb') as f:
                pickle.dump(multiple_measurement_singleton, f)
        else:
            with open(self.pickle_file_name, 'rb') as f:
                multiple_measurements.singleton = pickle.load(f)

        # BEGIN --- NOT NEEDED JUST FOR REFERENCE
        # multiple_measurements.singleton.change_measurement_scope_by_percentage(80)
        # multiple_measurements.singleton.change_measurement_resolution_by_time_interval(dt.timedelta(days=1))
        # multiple_measurements.singleton.sum_measurements_by_amount(30)
        # END --- NOT NEEDED JUST FOR REFERENCE

        # BEGIN --- plots in use
        visualizer.singleton.plot_total_energy_balance(save_name="Total_energy_balance")
        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       save_name="Total_energy_balance_summed")

        visualizer.singleton.plot_energy_balance_components({
            "sw_radiation_in": "Short wave in",
            "sw_radiation_out": "Short wave out",
            "lw_radiation_in": "Long wave in",
            "lw_radiation_out": "Long wave out"},
            use_summed_measurements=True, save_name="Energy_balance_only_radiation")

        visualizer.singleton.plot_energy_balance_components({
            "sensible_heat": "Sensible heat",
            "latent_heat": "Latent heat"},
            use_summed_measurements=True, save_name="Energy_balance_only_sens_and_latent_heat")
        # END --- plots in use

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_ablation",
                                                       save_name="Total_energy_balance_summed_with_ablation")

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_water_equivalent",
                                                       save_name="Total_energy_balance_summed_with_water_equivalent")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2017, 5, 15), endtime=dt.datetime(2017, 9, 15))

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_water_equivalent",
                                                       save_name="Total_energy_balance_summed_with_water_equivalent_2017")

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_ablation",
                                                       save_name="Total_energy_balance_summed_with_ablation_2017")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2018, 5, 15), endtime=dt.datetime(2018, 9, 15))

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_water_equivalent",
                                                       save_name="Total_energy_balance_summed_with_water_equivalent_2018")

        multiple_measurements.singleton.reset_scope_to_all()
        visualizer.singleton.plot_periodic_trend_eliminated_total_energy_balance(use_summed_measurements=True,
                                                                                 save_name="Total_energy_balance_summed_periodic_trend_eliminated")

        visualizer.singleton.plot_periodic_trend_eliminated_selected_option({
            "sw_radiation_in": "Short wave in",
            "sw_radiation_out": "Short wave out",
            "lw_radiation_in": "Long wave in",
            "lw_radiation_out": "Long wave out"},
            use_summed_measurements=True, save_name="Radiation_summed_periodic_trend_eliminated")

        visualizer.singleton.plot_periodic_trend_eliminated_selected_option({
            "sensible_heat": "Sensible heat",
            "latent_heat": "Latent heat"},
            use_summed_measurements=True, save_name="Latent_and_Sensible_summed_periodic_trend_eliminated")

        # visualizer.singleton.plot_periodic_trend_eliminated_selected_option("sw_radiation_in")

        # visualizer.singleton.plot_periodic_trend_eliminated("sw_radiation_out")
        # visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_in")
        # visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_out")
        # visualizer.singleton.plot_periodic_trend_eliminated("sensible_heat")
        # visualizer.singleton.plot_periodic_trend_eliminated("latent_heat")

        # visualizer.plot_energy_balance_components(latent_heat=True)


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

        if TEST:
            navigation_bar.singleton.btn_energybalanceframe["state"] = "normal"
            navigation_bar.singleton.btn_sumframe["state"] = "normal"
            navigation_bar.singleton.btn_plotframe["state"] = "normal"

            reader.singleton.add_file_path("PAS_10min_MED.csv")

            read_in_measurements = reader.singleton.read_meterologic_file_to_objects(resolution_by_percentage=20)

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
            sum_by_amount = "30"
            sum_by_time_interval = None

            if sum_by_amount is not None and sum_by_amount.isdigit():
                info_bar_text += "One summed measurement contains: " + str(sum_by_amount)
                multiple_measurements.singleton.sum_measurements_by_amount(int(sum_by_amount))
                frame_plot.singleton.enable_option_to_use_summed_measurements()
            elif sum_by_time_interval is not None:
                info_bar_text += "Measurements every " + str(int(sum_by_time_interval.total_seconds() // 60)) + " minutes summed"
                multiple_measurements.singleton.sum_measurements_by_time_interval(sum_by_time_interval)
                frame_plot.singleton.enable_option_to_use_summed_measurements()

            info_bar.singleton.change_sum_info(info_bar_text)

            navigation_bar.singleton.show_plot_frame()

            visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True, add_ablation=True)

        gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
        gui_thread.start()

        # gui_main.singleton.mainloop()
