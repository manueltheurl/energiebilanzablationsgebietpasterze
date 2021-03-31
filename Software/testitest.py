import dill


class AOTHER:
    def __init__(self, d):
        self.x = d


class Test:
    x = [AOTHER(54), AOTHER(543)]*500

    @classmethod
    def add_stuff(cls):
        Test.x = [AOTHER(54), AOTHER(543)]*500

    @classmethod
    def save_class(cls, save_path):
        """
        Class method that saves the whole class including all class variables, not only an instance.
        A bit hacky but pretty nice.

        :param save_path: path to save the serialized class
        """
        with open(save_path, 'wb') as f:
            a = globals()
            dill.dump(globals()[cls.__name__], f)

    @classmethod
    def load_class(cls, load_path):
        """
        Class method to load the whole previously saved class. This method sets all the class variables to the values
        which were previously saved with the class.
        A bit hacky but pretty nice.

        :param load_path: path to load the serialized class from
        """
        with open(load_path, 'rb') as fd:
            globals()[cls.__name__] = dill.load(fd)
        return cls


def save_measurement_handler(save_path):
    with open(save_path, 'wb') as f:
        dill.dump(globals()[Test.__name__], f)  # saving the whole class, not an instance


def load_measurement_handler(load_path):
    with open(load_path, 'rb') as fd:  # loading the whole class, not an instance
        globals()["Test"] = dill.load(fd)  # a bit hacky but whatever

#
# sdf = "sdfasdf"
# Test.add_stuff()
#
# Test.save_class(sdf)
#
#
#
# Test.load_class(sdf)
#
#
# print(Test.x)