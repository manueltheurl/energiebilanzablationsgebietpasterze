import tkinter as tk


class ModelFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.config(bg="green")

        self.grid_propagate(False)
        button = tk.Button(self, text="blabla")
        button.pack()
