import configparser


class Config:
    def __init__(self):
        self.manager = None  # GLOBAL variable that gets set at program start, refers to the main class itself
        self.__conf = configparser.ConfigParser()
        self.__conf.read(["config.ini"])

    def __getitem__(self, item):
        configuration = self.__conf["DEFAULT"][item]  # just default for now .. easy access possible
        if configuration.isdigit():
            return int(configuration)

        return configuration


cfg = Config()
