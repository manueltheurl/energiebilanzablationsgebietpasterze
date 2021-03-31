import configparser


class Config:
    def __init__(self):
        """
        Class that manages the parsing of the configurations set in the config.ini file
        """
        self.manager = None  # GLOBAL variable that gets set at program start, refers to the main class itself
        self.__conf = configparser.ConfigParser()
        self.__conf.read(["config.ini"])

    def __getitem__(self, item):
        """
        allows getting a configuration out of the config.ini file by simply typing cfg["DESIRED_CONFIG"].
        Config can include comma separated lists, integers, floats and strings. They will be returned from this fx
        as these types already.
        :param item: the DESIRED_CONFIG
        :return: List, Float, Int or String
        """
        configuration = self.__conf["DEFAULT"][item]  # just default for now .. easy access possible

        if ',' in configuration:
            return configuration.split(',')

        if configuration.isdigit():
            return int(configuration)

        try:
            return float(configuration)
        except ValueError:
            return configuration


cfg = Config()
