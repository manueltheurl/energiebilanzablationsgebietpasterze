import tkinter as tk
from tkinter import filedialog
import reader
import multiple_measurements
from tkinter import ttk
import datetime as dt
import GUI.info_bar as info_bar
import GUI.gui_main as gui_main
import GUI.frame_plot as frame_plot
import functions as fc


class ReadFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.grid_propagate(False)

        self.file_path = None

        self.btn_chooseFile = tk.Button(self, text="Choose File", command=self.select_file)
        self.btn_chooseFile.pack()
        self.lbl_chosenFile = tk.Label(self)
        self.lbl_chosenFile.pack()

        self.ckbox_percentToRead_value = tk.IntVar()
        self.ckbox_percentToRead = tk.Checkbutton(self,
                                                  command=self.toggle_resolution_by_percentage,
                                                  variable=self.ckbox_percentToRead_value, state="disabled")
        self.ckbox_percentToRead.pack()
        self.lbl_percentToRead = tk.Label(self, text="Percent to read in")
        self.lbl_percentToRead.pack()
        self.entry_percentToRead = tk.Entry(self, state="disabled")
        self.entry_percentToRead.pack()

        self.ckbox_timeInterval_value = tk.IntVar()
        self.ckbox_timeInterval = tk.Checkbutton(self,
                                                 command=self.toggle_resolution_by_time_interval,
                                                 variable=self.ckbox_timeInterval_value, state="disabled")
        self.ckbox_timeInterval.pack()
        self.lbl_timeInterval = tk.Label(self, text="Time interval resolution")
        self.lbl_timeInterval.pack()
        self.entry_timeInterval = tk.Entry(self, state="disabled")
        self.entry_timeInterval.pack()
        self.lbl_timeInterval = tk.Label(self, text="Time interval unit")
        self.lbl_timeInterval.pack()
        self.cmbobox_timeIntervalUnit = ttk.Combobox(self, values=["Minutes", "Hours", "Days"], state="disabled")
        self.cmbobox_timeIntervalUnit.pack()

        self.ckbox_startTime_value = tk.IntVar()
        self.ckbox_startTime = tk.Checkbutton(self,
                                              command=self.toggle_add_starttime,
                                              variable=self.ckbox_startTime_value, state="disabled")
        self.ckbox_startTime.pack()
        self.lbl_startTime = tk.Label(self, text="Add starttime")
        self.lbl_startTime.pack()
        self.entry_startTime = tk.Entry(self, state="disabled")
        self.entry_startTime.pack()

        self.ckbox_endTime_value = tk.IntVar()
        self.ckbox_endTime = tk.Checkbutton(self,
                                            command=self.toggle_add_endtime,
                                            variable=self.ckbox_endTime_value, state="disabled")
        self.ckbox_endTime.pack()
        self.lbl_endTime = tk.Label(self, text="Add endTime")
        self.lbl_endTime.pack()
        self.entry_endTime = tk.Entry(self, state="disabled")
        self.entry_endTime.pack()

        self.btn_readFilesToObjects = tk.Button(self,
                                                text="Read in defined measurements",
                                                command=self.read_measurements_to_objects,
                                                state="disabled")
        self.btn_readFilesToObjects.pack()

    def toggle_add_starttime(self):
        widgets_to_toggle_state = [
            self.entry_startTime
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_startTime_value.get())

    def toggle_add_endtime(self):
        widgets_to_toggle_state = [
            self.entry_endTime
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_endTime_value.get())

    def toggle_resolution_by_percentage(self):
        widgets_to_toggle_state = [
            self.entry_percentToRead
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_percentToRead_value.get())

    def toggle_resolution_by_time_interval(self):
        widgets_to_toggle_state = [
            self.entry_timeInterval,
            self.cmbobox_timeIntervalUnit
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_timeInterval_value.get())

    def select_file(self):
        selected_path = tk.filedialog.askopenfilename(filetypes=(("Csv Files", "*.csv"), ("all files", "*.*")))

        if selected_path != "":
            self.file_path = selected_path
            self.lbl_chosenFile['text'] = selected_path
            reader.singleton.add_file_path(selected_path)

            fc.set_widget_state([
                self.ckbox_startTime,
                self.ckbox_endTime,
                self.ckbox_percentToRead,
                self.ckbox_timeInterval,
                self.btn_readFilesToObjects,

                # those have to be set normal to fill in a value
                self.entry_startTime,
                self.entry_endTime,
                self.entry_timeInterval,
                self.entry_percentToRead
            ], "normal")

        multiple_measurements.singleton.fetch_measurements_metadata()

        self.entry_startTime.delete(0, 'end')
        self.entry_startTime.insert(
            0,
            multiple_measurements.singleton.get_single_measurement_metadata("time_of_first_measurement"))

        self.entry_endTime.delete(0, 'end')
        self.entry_endTime.insert(
            0,
            multiple_measurements.singleton.get_single_measurement_metadata("time_of_last_measurement"))
        self.entry_percentToRead.insert(0, "100")

        self.entry_timeInterval.delete(0, 'end')
        self.entry_timeInterval.insert(
            0,  # no minutes available for next line .. only seconds
            multiple_measurements.singleton.get_single_measurement_metadata("time_resolution").seconds // 60)

        self.cmbobox_timeIntervalUnit.current(0)  # possible here without state normal first

        fc.set_widget_state([
            # disable them again .. value stays though
            self.entry_startTime,
            self.entry_endTime,
            self.entry_timeInterval,
            self.entry_percentToRead
        ], "disabled")

    def read_measurements_to_objects(self):
        start_time = None
        if self.ckbox_startTime_value.get():
            start_time = self.entry_startTime.get()

        end_time = None
        if self.ckbox_endTime_value.get():
            end_time = self.entry_endTime.get()  # TODO checking if format is correct here or in reader?

        resolution_by_percentage = None
        if self.ckbox_percentToRead_value.get():
            if self.entry_percentToRead.get().isdigit():

                resolution_by_percentage = int(self.entry_percentToRead.get())

        resolution_by_time_interval = None
        if self.ckbox_timeInterval_value.get():
            if self.entry_timeInterval.get().isdigit():
                time_interval_unit = self.cmbobox_timeIntervalUnit.get()

                if time_interval_unit == "Minutes":
                    resolution_by_time_interval = dt.timedelta(minutes=int(self.entry_timeInterval.get()))
                elif time_interval_unit == "Hours":
                    resolution_by_time_interval = dt.timedelta(hours=int(self.entry_timeInterval.get()))
                elif time_interval_unit == "Days":
                    resolution_by_time_interval = dt.timedelta(days=int(self.entry_timeInterval.get()))

        read_in_measurements = reader.singleton.read_meterologic_file_to_objects(start_time,
                                                                                 end_time,
                                                                                 resolution_by_percentage,
                                                                                 resolution_by_time_interval
                                                                                 )

        info_bar_text_list = [
            "Measurements: " + str(read_in_measurements),
            "First: " + str(
                multiple_measurements.singleton.get_single_measurement_metadata("time_of_first_measurement")),
            "Last: " + str(multiple_measurements.singleton.get_single_measurement_metadata("time_of_last_measurement")),
            "Time resolution: " + str(multiple_measurements.singleton.get_single_measurement_metadata(
                "time_resolution").seconds // 60) + " minutes"
        ]

        info_bar.singleton["text"] = "\t".join(info_bar_text_list)
        gui_main.singleton.show_main_frame(frame_plot.PlotFrame)
