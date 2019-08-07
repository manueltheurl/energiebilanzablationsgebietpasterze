

class MultipleMeasurements:
    def __init__(self):
        self.__single_measurement_objects = []

    def add_single_measurement(self, single_measurement_objects):
        self.__single_measurement_objects.append(single_measurement_objects)

    def calculate_energy_balance_for_all(self):
        for obj in self.__single_measurement_objects:
            obj.calculate_energy_balance()

    def get_all_of(self, attribute_name):
        return list(map(lambda obj: getattr(obj, attribute_name), self.__single_measurement_objects))
