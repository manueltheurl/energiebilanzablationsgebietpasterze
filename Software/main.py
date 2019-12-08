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

        if not os.path.exists(self.pickle_file_name) or not cfg["USE_PICKLE_FOR_SAVING_TIME"]:
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

            multiple_measurements.singleton.sum_measurements_by_months(1)

            multiple_measurement_singleton = multiple_measurements.singleton

            if cfg["USE_PICKLE_FOR_SAVING_TIME"]:
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

        visualizer.singleton.accumulate_plots = True
        visualizer.singleton.plot_energy_balance_components([
            "sw_radiation_in"],
            use_summed_measurements=True)
        visualizer.singleton.plot_energy_balance_components([
            "sw_radiation_out"],
            use_summed_measurements=True)
        visualizer.singleton.plot_energy_balance_components([
            "lw_radiation_in"],
            use_summed_measurements=True)
        visualizer.singleton.plot_energy_balance_components([
            "lw_radiation_out"],
            use_summed_measurements=True)
        visualizer.singleton.plot_energy_balance_components([
            "latent_heat"],
            use_summed_measurements=True)
        visualizer.singleton.plot_energy_balance_components([
            "sensible_heat"],
            use_summed_measurements=True, save_name="Energy_balance_components_monthly_mean")
        visualizer.singleton.accumulate_plots = False

        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))

        visualizer.singleton.plot_scatter_measured_and_component(
            [2017, 2018], "theoretical_mm_we_per_d", save_name="Scatter_measured_and_modelled_water_equivalent")

        visualizer.singleton.plot_scatter_measured_and_component(
            [2017, 2018], "temperature", save_name="Scatter_measured_water_equivalent_and_temperature")

        # BEGIN --- plots in use
        visualizer.singleton.plot_total_energy_balance(save_name="Total_energy_balance")
        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       save_name="Total_energy_balance_summed")

        # visualizer.singleton.plot_single_component("temperature", "°C", use_summed_measurements=True,
        #                                            save_name="Temperature")

        visualizer.singleton.plot_single_component("wind_speed", "m/s", use_summed_measurements=False,
                                                   save_name="Wind_speed")

        visualizer.singleton.plot_single_component("air_pressure", "Pa", use_summed_measurements=False,
                                                   save_name="air_pressure")

        visualizer.singleton.plot_energy_balance_components([
            "sw_radiation_in",
            "sw_radiation_out",
            "lw_radiation_in",
            "lw_radiation_out"],
            use_summed_measurements=True, save_name="Energy_balance_only_radiation")

        # visualizer.singleton.plot_energy_balance_components(["sensible_heat",
        #     "latent_heat"],
        #     use_summed_measurements=True, save_name="Energy_balance_only_sens_and_latent_heat")
        #

        visualizer.singleton.accumulate_plots = True
        visualizer.singleton.plot_energy_balance_components([
            "latent_heat"],
            use_summed_measurements=True)

        visualizer.singleton.plot_energy_balance_components([
            "sensible_heat"],
            use_summed_measurements=True, save_name="Energy_balance_only_sens_and_latent_heat_accum")
        visualizer.singleton.accumulate_plots = False

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

        # visualizer.singleton.plot_temperature_and_water_equivalent(use_summed_measurements=False,
        #                                                            save_name="Temperature_and_waterequivalent_2017")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2018, 5, 15), endtime=dt.datetime(2018, 9, 15))

        visualizer.singleton.plot_total_energy_balance(use_summed_measurements=True,
                                                       ablation_or_water_equivalent="show_water_equivalent",
                                                       save_name="Total_energy_balance_summed_with_water_equivalent_2018")

                # visualizer.singleton.plot_temperature_and_water_equivalent(use_summed_measurements=False,
        #                                                            save_name="Temperature_and_waterequivalent_2018")

        multiple_measurements.singleton.reset_scope_to_all()
        visualizer.singleton.plot_periodic_trend_eliminated_total_energy_balance(
            use_summed_measurements=True, save_name="Total_energy_balance_summed_periodic_trend_eliminated")

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

        # END --- plots in use

        # some info printed -----------------------------------------

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2017, 1, 1), endtime=dt.datetime(2018, 1, 1))
        self.print_info("2017")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2017, 6, 1), endtime=dt.datetime(2018, 9, 1))
        self.print_info("2017_JJA")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2018, 1, 1), endtime=dt.datetime(2019, 1, 1))
        self.print_info("2018")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2018, 6, 1), endtime=dt.datetime(2019, 9, 1))
        self.print_info("2018_JJA")

        # --------------------------------------------------------------

        multiple_measurements.singleton.reset_scope_to_all()
        # global dimming and brightening checking
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            starttime=dt.datetime(2018, 6, 1), endtime=dt.datetime(2018, 9, 1))

        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))

        measured_ablation_3_months = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_measured", use_summed_measurements=True))
        modelled_ablation_3_months = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True))

        multiple_measurements.singleton.calculate_energy_balance_for_scope(simulate_global_dimming_brightening=-9)
        multiple_measurements.singleton.convert_energy_balance_to_water_equivalent_for_scope()
        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))

        modelled_ablation_3_months_minus_9 = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True))

        multiple_measurements.singleton.calculate_energy_balance_for_scope(simulate_global_dimming_brightening=-6)
        multiple_measurements.singleton.convert_energy_balance_to_water_equivalent_for_scope()
        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))


        modelled_ablation_3_months_minus_6 = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True))

        multiple_measurements.singleton.calculate_energy_balance_for_scope(simulate_global_dimming_brightening=-3)
        multiple_measurements.singleton.convert_energy_balance_to_water_equivalent_for_scope()
        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))


        modelled_ablation_3_months_minus_3 = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True))

        multiple_measurements.singleton.calculate_energy_balance_for_scope(simulate_global_dimming_brightening=3)
        multiple_measurements.singleton.convert_energy_balance_to_water_equivalent_for_scope()
        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=1))


        modelled_ablation_3_months_plus_3 = sum(
            multiple_measurements.singleton.get_all_of("relative_ablation_modelled", use_summed_measurements=True))

        reality_factor = measured_ablation_3_months/modelled_ablation_3_months

        print("Measured ablation in 3 months", round(measured_ablation_3_months, 2))
        print("Modelled ablation in 3 months", round(modelled_ablation_3_months, 2))  # measured stays the same .. cause thats wont be affected
        print("With respect to the reality factor:", round(reality_factor, 2))
        print("Modelled ablation in 3 months -9", round(modelled_ablation_3_months_minus_9*reality_factor, 2))
        print("--> Diff:", round(modelled_ablation_3_months_minus_9*reality_factor - measured_ablation_3_months, 2))
        print("Modelled ablation in 3 months -6", round(modelled_ablation_3_months_minus_6*reality_factor, 2))
        print("--> Diff:", round(modelled_ablation_3_months_minus_6 * reality_factor - measured_ablation_3_months, 2))
        print("Modelled ablation in 3 months -3", round(modelled_ablation_3_months_minus_3*reality_factor, 2))
        print("--> Diff:", round(modelled_ablation_3_months_minus_3 * reality_factor - measured_ablation_3_months, 2))
        print("Modelled ablation in 3 months +3", round(modelled_ablation_3_months_plus_3*reality_factor, 2))
        print("--> Diff:", round(modelled_ablation_3_months_plus_3 * reality_factor - measured_ablation_3_months, 2))

    @staticmethod
    def print_info(date_range: str):
        print(
            "EB mean " + date_range, round(
                float(
                    np.mean(multiple_measurements.singleton.get_all_of("total_energy_balance"))
                ), 1), "W/m^2")

        print(
            "Radiation mean " + date_range, round(
                float(np.mean(multiple_measurements.singleton.get_vals_and_dates_of_selected_options(
                    ["sw_radiation_in",
                     "sw_radiation_out",
                     "lw_radiation_in",
                     "lw_radiation_out"])[0]
                )), 1),
            "W/m^2")

        print(
            "Sensible/latent heat mean " + date_range, round(
                float(np.mean(multiple_measurements.singleton.get_vals_and_dates_of_selected_options(
                    ["sensible_heat",
                     "latent_heat"])[0]
                )), 1),
            "W/m^2")


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

        gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
        gui_thread.start()

        # gui_main.singleton.mainloop()
