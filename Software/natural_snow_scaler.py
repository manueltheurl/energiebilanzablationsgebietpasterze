class NaturalSnowScaler:
    a_l = 0.7095
    b_l = -1044.16

    a_q = -0.000253
    b_q = -0.6637
    c_q = 797.47

    @classmethod
    def __linear(cls, z):
        return cls.a_l * z + cls.b_l

    @classmethod
    def __quadratic(cls, z):
        return cls.a_q ** 2 * z + cls.b_q * z + cls.c_q

    @classmethod
    def linear_scale_factor(cls, new_height, reference_height):
        return cls.__linear(new_height) / cls.__linear(reference_height)

    @classmethod
    def quadratic_scale_factor(cls, new_height, reference_height):
        return cls.__quadratic(new_height) / cls.__quadratic(reference_height)

    @classmethod
    def fixed_percentage_per_100_meter_scale_factor(cls, new_height, reference_height, percentage):
        # percentage ranging from 0.0 to 1.0
        return 1 + (new_height - reference_height) / 100 * (percentage)
