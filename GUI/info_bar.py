import tkinter as tk


class InfoBar(tk.Label):
    """
    TODO
    """
    singleton_created = False

    def __init__(self, parent):
        if InfoBar.singleton_created:
            raise Exception("InfoBar is a singleton")
        InfoBar.singleton_created = True

        tk.Label.__init__(self, parent, anchor="w")


singleton = None  # yet to be initialized
