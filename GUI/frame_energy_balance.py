import tkinter as tk
import multiple_measurements
import functions as fc
import gui_main_frame as gui_main_frame
import navigation_bar as navigation_bar
import info_bar as info_bar
from tkinter import ttk
import datetime as dt
import reader


class ScopeFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        # self.config(bg="black")
        self.grid_propagate(False)

        self.lbl_currentScope = tk.Label(self, text="Change current scope of all read in measurements")
        self.lbl_currentScope.pack(pady=(40, 30))

        self.ckbox_percentScope_value = tk.IntVar()
        self.ckbox_percentScope = tk.Checkbutton(self,
                                                 command=self.toggle_percent_scope,
                                                 variable=self.ckbox_percentScope_value, state="normal")
        self.ckbox_percentScope.pack()

        self.lbl_percentScope = tk.Label(self, text="Percent to take from read in measurements")
        self.lbl_percentScope.pack()
        self.entry_percentScope = tk.Entry(self, state="disabled")
        self.entry_percentScope.pack()

        self.ckbox_timeintervalScope_value = tk.IntVar()
        self.ckbox_timeintervalScope = tk.Checkbutton(self,
                                                 command=self.toggle_time_interval_scope,
                                                 variable=self.ckbox_timeintervalScope_value, state="normal")
        self.ckbox_timeintervalScope.pack(pady=(7, 0))

        self.lbl_timeintervalScope = tk.Label(self, text="Time interval scope")
        self.lbl_timeintervalScope.pack()
        self.entry_timeintervalScope = tk.Entry(self, state="disabled")
        self.entry_timeintervalScope.pack()

        self.lbl_timeIntervalScopeUnit = tk.Label(self, text="Time interval scope unit")
        self.lbl_timeIntervalScopeUnit.pack()

        self.cmbobox_timeIntervalScopeUnit = ttk.Combobox(self, values=["Minutes", "Hours", "Days", "Months", "Years"],
                                                          state="disabled")
        self.cmbobox_timeIntervalScopeUnit.pack()

        self.ckbox_startTime_value = tk.IntVar()
        self.ckbox_startTime = tk.Checkbutton(self,
                                              command=self.toggle_add_starttime,
                                              variable=self.ckbox_startTime_value)
        self.ckbox_startTime.pack(pady=(7, 0))
        self.lbl_startTime = tk.Label(self, text="Add starttime")
        self.lbl_startTime.pack()
        self.entry_startTime = tk.Entry(self, state="disabled")
        self.entry_startTime.pack()

        self.ckbox_endTime_value = tk.IntVar()
        self.ckbox_endTime = tk.Checkbutton(self,
                                            command=self.toggle_add_endtime,
                                            variable=self.ckbox_endTime_value)
        self.ckbox_endTime.pack(pady=(7, 0))
        self.lbl_endTime = tk.Label(self, text="Add endTime")
        self.lbl_endTime.pack()
        self.entry_endTime = tk.Entry(self, state="disabled")
        self.entry_endTime.pack()

        self.btn_changeCurrentScope = tk.Button(self,
                                                text="Change current scope",
                                                command=self.change_current_scope,
                                                state="disabled")
        self.btn_changeCurrentScope.pack(pady=(20, 0))

        self.btn_resetScope = tk.Button(self,
                                        text="Reset scope",
                                        command=self.reset_scope,
                                        state="normal")
        self.btn_resetScope.pack(pady=5)

        self.lbl_simulate_dimming_brightening = tk.Label(self, text="Simulate global dimming and brightening [W/m^2]").pack()

        self.scale_simulate_dimming_brightening = tk.Scale(self, from_=-9, to=4, orient="horizontal")
        self.scale_simulate_dimming_brightening.pack()

        self.btn_calcEnergyBalance = tk.Button(self,
                                               text="Calculate Energy Balance and cumulate Ablation",
                                               command=self.calculate_energy_balance_and_cumulate_ablation,
                                               state="normal")
        self.btn_calcEnergyBalance.pack(pady=30)

        self.grid(row=0, column=0, sticky="nsew")

    def toggle_add_starttime(self):
        widgets_to_toggle_state = [
            self.entry_startTime
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_startTime_value.get())
        self.activate_btn_change_current_scope_if_anything_active()

    def toggle_add_endtime(self):
        widgets_to_toggle_state = [
            self.entry_endTime
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_endTime_value.get())
        self.activate_btn_change_current_scope_if_anything_active()

    def fill_fields_with_read_in_values(self):
        self.entry_percentScope["state"] = "normal"
        self.entry_percentScope.delete(0, 'end')
        self.entry_percentScope.insert(0, 100)
        self.entry_percentScope["state"] = "disabled"

        self.entry_timeintervalScope["state"] = "normal"
        self.entry_timeintervalScope.delete(0, 'end')
        self.entry_timeintervalScope.insert(
            0,  # no minutes available for next line .. only seconds
            int(reader.singleton.get_single_file_metadata("time_resolution").total_seconds() // 60))
        self.entry_timeintervalScope["state"] = "disabled"

        self.entry_startTime["state"] = "normal"
        self.entry_startTime.delete(0, 'end')
        self.entry_startTime.insert(0, multiple_measurements.singleton.get_date_of_first_measurement(of="scope"))
        self.entry_startTime["state"] = "disabled"

        self.entry_endTime["state"] = "normal"
        self.entry_endTime.delete(0, 'end')
        self.entry_endTime.insert(0, multiple_measurements.singleton.get_date_of_last_measurement(of="scope"))
        self.entry_endTime["state"] = "disabled"

        self.cmbobox_timeIntervalScopeUnit.current(0)  # possible here without state normal first

    def activate_btn_change_current_scope_if_anything_active(self):
        fc.set_widget_state([self.btn_changeCurrentScope],
                            self.ckbox_percentScope_value.get() or self.ckbox_timeintervalScope_value.get() or
                            self.ckbox_startTime_value.get() or self.ckbox_endTime_value.get())

    def toggle_percent_scope(self):
        widgets_to_toggle_state = [
            self.entry_percentScope
        ]
        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_percentScope_value.get())
        self.activate_btn_change_current_scope_if_anything_active()

    def toggle_time_interval_scope(self):
        widgets_to_toggle_state = [
            self.entry_timeintervalScope,
            self.cmbobox_timeIntervalScopeUnit
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_timeintervalScope_value.get())
        self.activate_btn_change_current_scope_if_anything_active()

    @staticmethod
    def reset_scope():
        multiple_measurements.singleton.reset_scope_to_all()
        info_bar.singleton.change_scope_info("")

    def change_current_scope(self):
        multiple_measurements.singleton.reset_scope_to_all()

        percent_scope = None
        if self.ckbox_percentScope_value.get():
            percent_scope = self.entry_percentScope.get()

        timeinterval_scope = None
        months_scope = None
        years_scope = None

        if self.ckbox_timeintervalScope_value.get():
            if self.entry_timeintervalScope.get().isdigit():
                time_interval_unit = self.cmbobox_timeIntervalScopeUnit.get()

                if time_interval_unit == "Minutes":
                    timeinterval_scope = dt.timedelta(minutes=int(self.entry_timeintervalScope.get()))
                elif time_interval_unit == "Hours":
                    timeinterval_scope = dt.timedelta(hours=int(self.entry_timeintervalScope.get()))
                elif time_interval_unit == "Days":
                    timeinterval_scope = dt.timedelta(days=int(self.entry_timeintervalScope.get()))
                elif time_interval_unit == "Months":
                    months_scope = int(self.entry_timeintervalScope.get())
                elif time_interval_unit == "Years":
                    years_scope = int(self.entry_timeintervalScope.get())

        starttime_scope = None
        if self.ckbox_startTime_value.get():
            starttime_scope = self.entry_startTime.get()

        endttime_scope = None
        if self.ckbox_endTime_value.get():
            endttime_scope = self.entry_endTime.get()

        if percent_scope is not None and percent_scope.isdigit():
            multiple_measurements.singleton.change_measurement_scope_by_percentage(int(percent_scope))

        # Only one such event can occur
        if timeinterval_scope is not None:
            multiple_measurements.singleton.change_measurement_scope_by_time_interval(timeinterval_scope)
        elif months_scope is not None:
            multiple_measurements.singleton.change_measurement_scope_by_months(months_scope)
        elif years_scope is not None:
            multiple_measurements.singleton.change_measurement_scope_by_years(years_scope)

        if starttime_scope is not None or endttime_scope is not None:
            multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(starttime_scope,
                                                                                            endttime_scope)

        info_bar_text_list = [
            "Measurements: " + str(multiple_measurements.singleton.get_measurement_amount(of="scope")),
            "First: " + str(multiple_measurements.singleton.get_date_of_first_measurement(of="scope")),
            "Last: " + str(multiple_measurements.singleton.get_date_of_last_measurement(of="scope")),
            "Time resolution: " + multiple_measurements.singleton.get_time_resolution(of="scope",
                                                                                      as_beautiful_string=True)
        ]
        info_bar.singleton.change_scope_info("\t".join(info_bar_text_list))

    def calculate_energy_balance_and_cumulate_ablation(self):
        multiple_measurements.singleton.calculate_energy_balance_for_scope(
            self.scale_simulate_dimming_brightening.get()
        )
        multiple_measurements.singleton.cumulate_ablation_for_scope()
        multiple_measurements.singleton.convert_energy_balance_to_water_equivalent()

        navigation_bar.singleton.btn_downloadframe["state"] = "normal"
        navigation_bar.singleton.show_sum_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = ScopeFrame()

