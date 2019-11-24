import tkinter as tk
import GUI.gui_main_frame as gui_main_frame


class InfoBar:
    """
    TODO
    """
    singleton_created = False

    def __init__(self):
        if InfoBar.singleton_created:
            raise Exception("InfoBar is a singleton")
        InfoBar.singleton_created = True

        self.read = tk.Label(gui_main_frame.singleton, anchor="w")
        self.scope = tk.Label(gui_main_frame.singleton, anchor="w")
        self.sum = tk.Label(gui_main_frame.singleton, anchor="w")

    @staticmethod
    def pack_if_not_empty_else_forget(label, text):
        if text == "":
            label.pack_forget()
        else:
            label.pack(side="top", fill="both", padx=15)

    def change_read_info(self, text):
        self.read["text"] = "Read info:\t" + text
        self.pack_if_not_empty_else_forget(self.read, text)

    def change_scope_info(self, text):
        self.scope["text"] = "Scope info:\t" + text
        self.pack_if_not_empty_else_forget(self.scope, text)

    def change_sum_info(self, text):
        self.sum["text"] = "Sum info:\t" + text
        self.pack_if_not_empty_else_forget(self.sum, text)





singleton = None


def create_singleton():
    global singleton
    singleton = InfoBar()
