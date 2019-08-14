import tkinter as tk
from tkinter import filedialog
from reader import Reader
from multiple_measurements import MultipleMeasurements
from tkinter import ttk
import datetime as dt


class ReadFrame(tk.Frame):
    # static variables/ class variables
    obj_multipleMeasurement = MultipleMeasurements()

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.reader = Reader()

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

        self.btn_readFilesToObjects = tk.Button(self,
                                                text="Read in defined measurements",
                                                command=self.read_measurements_to_objects,
                                                state="disabled")
        self.btn_readFilesToObjects.pack()

    def toggle_resolution_by_percentage(self):
        widgets_to_toggle_state = [
            self.entry_percentToRead
        ]

        self.set_widget_state(widgets_to_toggle_state, self.ckbox_percentToRead_value.get())

    def toggle_resolution_by_time_interval(self):
        widgets_to_toggle_state = [
            self.entry_timeInterval,
            self.cmbobox_timeIntervalUnit
        ]

        self.set_widget_state(widgets_to_toggle_state, self.ckbox_timeInterval_value.get())

    @staticmethod
    def set_widget_state(widgets: list, state):
        if state or state == "normal":
            for widget in widgets:
                widget["state"] = "normal"

        elif not state or state == "disabled":
            for widget in widgets:
                widget["state"] = "disabled"

    def select_file(self):
        selected_path = tk.filedialog.askopenfilename(filetypes=(("Csv Files", "*.csv"), ("all files", "*.*")))

        if selected_path != "":
            self.file_path = selected_path
            self.lbl_chosenFile['text'] = selected_path
            self.reader.add_file_path(selected_path)

            # TODO check starttime and endtime and resolution and autofill that values

            # TODO own class for setting normal .. maybe in functions file
            self.set_widget_state([
                self.ckbox_percentToRead,
                self.ckbox_timeInterval,
                self.btn_readFilesToObjects
            ], "normal")

            self.entry_percentToRead.insert(0, "100")

    def read_measurements_to_objects(self):
        percentage = int(self.entry_percentToRead.get()) if self.entry_percentToRead.get().isdigit() else 100

        time_interval = self.entry_timeInterval.get()

        if time_interval.isdigit():
            time_interval_unit = self.cmbobox_timeIntervalUnit.get()

            if time_interval_unit == "Minutes":
                time_interval = dt.timedelta(minutes=int(time_interval))
            elif time_interval_unit == "Hours":
                time_interval = dt.timedelta(hours=int(time_interval))
            elif time_interval_unit == "Days":
                time_interval = dt.timedelta(days=int(time_interval))
            else:
                time_interval = None

        else:
            time_interval = None

        self.reader.read_meterologic_file_to_objects(
            self.obj_multipleMeasurement,
            resolution_by_percentage=percentage,
            resolution_by_time_interval=time_interval)
