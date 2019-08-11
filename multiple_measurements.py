import datetime as dt


class MultipleMeasurements:
    def __init__(self):
        self.__all_single_measurement_objects = []
        self.__current_index_scope = set()  # current indexes that will be used are saved in here .. all by default

    def add_single_measurement(self, single_measurement_objects):
        self.__current_index_scope.add(len(self.__all_single_measurement_objects))
        self.__all_single_measurement_objects.append(single_measurement_objects)

    def calculate_energy_balance_for_all(self):
        for obj in self.__all_single_measurement_objects:
            obj.calculate_energy_balance()

    def get_all_of(self, attribute_name):
        return list(map(
            lambda obj: getattr(obj, attribute_name),
            # set messes with the order, sorted creates a list of the set
            [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]
        ))

    def reset_scope_to_all(self):
        self.__current_index_scope = set(range(len(self.__all_single_measurement_objects)))

    def change_measurement_resolution_by_time_interval(self, time_interval: dt.timedelta):
        """
        TODO
        :param time_interval:
        :return:
        """
        indexes_to_remove = set()
        reference_time = self.__all_single_measurement_objects[0].datetime

        for index in self.__current_index_scope:
            current_time = self.__all_single_measurement_objects[index].datetime

            if current_time - reference_time >= time_interval:
                reference_time = current_time
            else:
                indexes_to_remove.add(index)

        self.__current_index_scope.difference_update(indexes_to_remove)

    def change_measurement_resolution_by_percentage(self, percentage: int):
        """

        :param percentage: reaching from 0 to 100
        :return:
        """
        threshold = 0
        indexes_to_remove = set()

        for index in self.__current_index_scope:
            threshold += percentage
            if threshold >= 100:
                threshold = 0
            else:
                indexes_to_remove.add(index)  # if not a member, a KeyError is raised

        self.__current_index_scope.difference_update(indexes_to_remove)

    def get_measurement_amount(self):
        return len(self.__all_single_measurement_objects)

    def get_date_of_first_measurement(self):
        # this presupposes that the measurements are read in sorted ascending by date
        return self.__all_single_measurement_objects[0].datetime

    def get_date_of_last_measurement(self):
        # this presupposes that the measurements are read in sorted ascending by date
        return self.__all_single_measurement_objects[-1].datetime
