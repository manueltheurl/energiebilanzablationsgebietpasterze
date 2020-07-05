import os
import matplotlib.pyplot as plt
from manage_config import cfg
import matplotlib.dates
import matplotlib.cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.markers import MarkerStyle
import os
from matplotlib import patches
from operator import sub
import datetime as dt
# from matplotlib import rc
# rc('text', usetex=True)
import multiple_measurements
import scipy
import scipy.stats
import numpy as np
from scipy import optimize
import functions as fc
import calendar
from height_level import HeightLevel
import shapefile as shp
from descartes import PolygonPatch
import matplotlib.colors
import matplotlib.colorbar
from height_level import MeteorologicalYear
from matplotlib.ticker import MaxNLocator
from single_measurement import MeanMeasurement
import copy

matplotlib.rcParams.update({'font.size': float(cfg["plot_text_size"])})

DAYS_365 = dt.timedelta(days=365)  # hours=5, minutes=48     365.2422 days in year approximately  dont change to that


class Visualize:
    singleton_created = False

    def __init__(self, result_plot_path=cfg["RESULT_PLOT_PATH"]):
        if Visualize.singleton_created:
            raise Exception("Reader is a singleton")
        Visualize.singleton_created = True

        if not os.path.exists(result_plot_path):
            os.makedirs(result_plot_path)

        self.result_plot_path = result_plot_path

        self.title_dict = {
            "sw_radiation_in": "Short wave in",
            "sw_radiation_out": "Short wave out",
            "lw_radiation_in": "Long wave in",
            "lw_radiation_out": "Long wave out",
            "sensible_heat": "Sensible heat",
            "latent_heat": "Latent heat",
            "precipitation_heat": "Precipitation heat",
            "total_energy_balance": "Total energy balance",
            "total_snow_depth": "Total Snow Height",
            "snow_depth_natural": "Natural Snow Height",
            "snow_depth_artificial": "Artificial Snow Height",
            "theoretical_melt_water_per_sqm": "Theoretical Melt Water",
            "total_snow_water_equivalent": "Total snow water equivalent",
            "artificial_snow_water_equivalent": "Artificial snow water equivalent",
            "natural_snow_water_equivalent": "Natural snow water equivalent",
        }

        self.accumulate_plots = False
        self.show_plots = False

        self.fig = None
        self.ax = None

    plot_type_initialized = {
        "energy_balance": False,
        "trend": False,
        "temperature": False
    }

    def change_result_plot_subfolder(self, result_plot_subfolder):
        if not os.path.exists(self.result_plot_path + '/' + result_plot_subfolder):
            os.makedirs(self.result_plot_path + '/' + result_plot_subfolder)
        self.result_plot_path = self.result_plot_path + '/' + result_plot_subfolder

    def _pretty_label(self, key):
        try:
            return self.title_dict[key]
        except KeyError:
            return key

    def initialize_plot(self, type_):
        """
        :rtype: object
        """

        yet_to_initialize = True

        if type_ is not None:
            if self.accumulate_plots:
                # close other plot types that are open
                for plot_type in self.plot_type_initialized:
                    if type_ != plot_type:
                        if self.plot_type_initialized[plot_type]:
                            self.plot_type_initialized[plot_type] = False
                            plt.close()
                            break

                if self.plot_type_initialized[type_]:
                    yet_to_initialize = False
                else:
                    self.plot_type_initialized[type_] = True
            else:
                plt.close()  # should one be open

        if yet_to_initialize or not bool(cfg["PRO_VERSION"]):
            self.fig = plt.figure(figsize=(14, 9))
            self.ax = self.fig.add_subplot(111)

    def modify_axes(self):
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..
        mondays = mdates.WeekdayLocator(mdates.MONDAY)

        # calculate time_spawn between first and last measurement
        time_spawn = dt.timedelta(days=self.ax.get_xlim()[1] - self.ax.get_xlim()[0])

        time_border_1 = dt.timedelta(days=3*365)
        time_border_2 = dt.timedelta(days=2*365)
        time_border_3 = dt.timedelta(days=150)
        time_border_4 = dt.timedelta(days=60)

        # major and ax title
        if time_spawn >= time_border_1:
            self.ax.set_xlabel("Year")
            self.ax.xaxis.set_major_locator(years)
            self.ax.xaxis.set_major_formatter(year_labels)
        elif time_border_3 <= time_spawn <= time_border_1:  # 1 till 3 beware
            self.ax.xaxis.set_major_locator(years)
            self.ax.xaxis.set_major_formatter(year_labels)
            self.ax.set_xlabel("Year")
            self.ax.xaxis.set_tick_params(rotation=45, pad=15)  # only major are rotated
            self.ax.xaxis.set_tick_params(which="minor", labelsize=float(cfg["plot_text_size_minor"]))  # only major are rotated
            self.ax.xaxis.set_minor_locator(months)

            if time_border_3 <= time_spawn <= time_border_2:
                self.ax.xaxis.set_minor_formatter(month_labels)
        elif time_border_4 <= time_spawn <= time_border_3:
            self.ax.xaxis.set_major_locator(months)
            self.ax.xaxis.set_major_formatter(month_labels)
            self.ax.set_xlabel("Month")
            # self.ax.xaxis.set_tick_params()  # only major are rotated
            self.ax.xaxis.set_tick_params(which="minor")  # only major are rotated
            self.ax.xaxis.set_minor_locator(mondays)

        # else even smaller take month as major, and days as minor maybe?

        # ELSE just take default tick and ticklabels

        self.ax.grid(linestyle="--", alpha=0.5, which='major')
        self.ax.grid(linestyle="--", alpha=0.4, which='minor')

    def show_save_and_close_plot(self, type_, save_name=None):
        if self.show_plots or cfg["GUI"]:
            plt.tight_layout()
            plt.show()

        if save_name is not None:
            plt.savefig(self.result_plot_path + "/" + save_name + ".png", dpi=cfg["PLOT_RESOLUTION"],
                        bbox_inches='tight')
            self.plot_type_initialized = dict.fromkeys(self.plot_type_initialized, False)

        if not self.accumulate_plots or not bool(cfg["PRO_VERSION"]):
            plt.close()
            self.plot_type_initialized = dict.fromkeys(self.plot_type_initialized, False)

    def plot_total_energy_balance(self, use_summed_measurements=False, ablation_or_water_equivalent=False,
                                  save_name=None):
        self.initialize_plot("energy_balance")

        x_vals = multiple_measurements.singleton.get_all_of("total_energy_balance",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label="Energy Balance")

        if ablation_or_water_equivalent is not False:  # is false if None of the both
            second_ax = self.ax.twinx()

            if ablation_or_water_equivalent == "show_ablation":
                second_ax_vals = multiple_measurements.singleton.get_all_of(
                    "cumulated_ablation", use_summed_measurements=use_summed_measurements)

                second_ax.plot(y_dates, second_ax_vals, label="Ablation", color="red")
                second_ax.set_ylabel("Ablation [m]")

                # hack .. but will always start at the upper left, so this is legitim
                y_lims = second_ax.get_ylim()
                second_ax.set_ylim([y_lims[0], y_lims[1]+0.5])

                main_title = "Total Energy balance with Ablation"

            elif ablation_or_water_equivalent == "show_water_equivalent":
                if use_summed_measurements:  # has to be summed here for now
                    actual_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                        "actual_mm_we_per_d", use_summed_measurements=use_summed_measurements)

                    theoretical_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                        "theoretical_mm_we_per_d", use_summed_measurements=use_summed_measurements)

                    second_ax.plot(y_dates, actual_melt_water_per_sqm, color="red", label="Measured Meltwater")
                    second_ax.plot(
                        y_dates, theoretical_melt_water_per_sqm, color="green", label="Modelled Meltwater")

                    # calculate correlation coefficient
                    if save_name is not None:

                        actual_melt_water_per_sqm, theoretical_melt_water_per_sqm = fc.remove_none_in_lists(
                            [actual_melt_water_per_sqm, theoretical_melt_water_per_sqm])

                        print(save_name, "correlation coefficient:",
                              round(float(np.ma.corrcoef(actual_melt_water_per_sqm, theoretical_melt_water_per_sqm)[0][1]), 2))

                second_ax.set_ylabel("Water equivalent [mm/d]")
                second_ax.set_ylim(0, second_ax.get_ylim()[1])
                main_title = "Total Energy balance with actual and theoretical Ablation as water equivalent"

            else:
                return  # shouldnt get there

            self.ax.legend(loc="upper left")
            second_ax.legend(loc="upper right")
        else:
            main_title = "Total Energy balance"
            self.ax.legend()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"
        # self.ax.set_title(main_title + summed_title_appendix)
        self.ax.set_ylabel("Energy [W/m^2]")
        self.modify_axes()
        
        self.show_save_and_close_plot("energy_balance", save_name=save_name)

    @staticmethod
    def _color_generator():
        colors = ["blue", "red", "green", "dimgray", "lightgray", "rosybrown", "lightcoral", "darkorange",
                  "darkgoldenrod", "darkkhaki", "olive", "darkseagreen", "mediumaquamarine", "rebeccapurple", "pink",
                  "darkblue", "black"]
        i = 0
        while True:
            if i == len(colors):
                i = 0
            yield colors[i]
            i += 1

    def plot_scatter_measured_and_component(self, years_to_plot, component, save_name=None):
        # could be further generalized of course .. but this ist just needed for the thesis here

        self.initialize_plot(None)

        marker_types = ["o", "x"]  # extend how you like .. currently only 2, cause only 2 years
        marker_colors = ["orange", "blue"]

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=True)

        actual_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
            "actual_mm_we_per_d", use_summed_measurements=True)

        theoretical_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
            component, use_summed_measurements=True)

        for date, actual, theoretical in zip(y_dates, actual_melt_water_per_sqm, theoretical_melt_water_per_sqm):
            if actual is not None and theoretical is not None:
                year_index = years_to_plot.index(date.year)

                self.ax.scatter(actual, theoretical, marker=marker_types[year_index], c=marker_colors[year_index])

        # get rid of none values
        actual_melt_water_per_sqm, theoretical_melt_water_per_sqm = fc.remove_none_in_lists(
            [actual_melt_water_per_sqm, theoretical_melt_water_per_sqm])

        actual_melt_water_per_sqm = np.array(actual_melt_water_per_sqm, dtype=np.float)
        theoretical_melt_water_per_sqm = np.array(theoretical_melt_water_per_sqm, dtype=np.float)

        # regression line

        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(actual_melt_water_per_sqm,
                                                                             theoretical_melt_water_per_sqm)

        poly1d_fn = np.poly1d([slope, intercept])

        print("Scatter measured and modelled w.e. slope:", round(slope, 2), "intercept", round(intercept, 2))

        # poly1d_fn is now a function which takes in x and returns an estimate for y

        self.ax.plot(actual_melt_water_per_sqm,
                     poly1d_fn(actual_melt_water_per_sqm), linestyle="--", label="Regression line")

        if component == "theoretical_mm_we_per_d":
            max_value = max(actual_melt_water_per_sqm)
            self.ax.plot([0, max_value], [0, max_value], linestyle="--", label="Line of unity")

            self.ax.set_aspect("equal")
            self.ax.set_ylabel("Modelled ablation [mm w.e./d]")
        elif component == "temperature":
            self.ax.set_ylabel("Temperature [°C]")

        self.ax.set_xlabel("Measured ablation [mm w.e./d]")

        # create legend entries
        for i, year in enumerate(years_to_plot):
            self.ax.scatter(None, None, marker=marker_types[i], c=marker_colors[i], label=str(year))

        self.ax.set_xlim(0, self.ax.get_xlim()[1])
        self.ax.set_ylim(0, self.ax.set_ylim()[1])

        self.ax.legend()
        self.ax.grid(linestyle="--", alpha=0.5)

        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_single_component(self, component, component_unit, use_summed_measurements=False, save_name=None):
        self.initialize_plot(None)

        x_vals = multiple_measurements.singleton.get_all_of(component,
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label=component)

        self.ax.legend(loc="upper left")

        self.ax.set_ylabel(component_unit)
        self.modify_axes()

        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_components(self, components1: tuple, components1_unit, components2: tuple = None, components2_unit = None, use_summed_measurements=False, save_name=None):
        self.initialize_plot(None)

        color_generator = self._color_generator()

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        for component in components1:
            x_vals = multiple_measurements.singleton.get_all_of(component,
                                                                 use_summed_measurements=use_summed_measurements)
            self.ax.plot(y_dates, x_vals, label=self._pretty_label(component), color=next(color_generator))

        self.ax.legend(loc="upper left")
        self.ax.set_ylabel(components1_unit)

        if components2 is not None:
            ax2 = self.ax.twinx()
            for component in components2:
                x_vals = multiple_measurements.singleton.get_all_of(component,
                                                                    use_summed_measurements=use_summed_measurements)
                ax2.plot(y_dates, x_vals, label=self._pretty_label(component), color="orange")
                ax2.legend(loc="upper right")
                ax2.set_ylabel(components2_unit)

        self.modify_axes()
        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_components_lvls(self, meteorological_year, components1: tuple, components1_unit, components2: tuple = None,
                             components2_unit=None, use_summed_measurements=True,
                             show_estimated_measurement_areas=False, save_name=None):

        self.initialize_plot(None)
        meteorological_year: MeteorologicalYear

        color_generator = self._color_generator()

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        i = 0
        for component in components1:
            # bad if more components
            self.ax.set_ylabel(f"{self._pretty_label(component)} [{components1_unit}]")
            for height_lvl in meteorological_year.height_level_objects:
                if i % 6 == 0:

                    height_lvl: HeightLevel
                    x_vals = []
                    for measure in height_lvl.simulated_measurements:
                        x_vals.append(getattr(measure, component))

                    self.ax.plot(y_dates, x_vals, label=self._pretty_label("Lvl mid height: " + str(int(height_lvl.height)) + "m"),
                                 color=next(color_generator))

                i += 1

        if show_estimated_measurement_areas:
            for estimated_area in multiple_measurements.singleton.get_time_frames_of_valid_state_for_scope(MeanMeasurement.valid_states["estimated"]):
                rect = patches.Rectangle((estimated_area[0], self.ax.get_ylim()[0]), estimated_area[1]-estimated_area[0], self.ax.get_ylim()[1]-self.ax.get_ylim()[0],
                                         edgecolor='none', facecolor='lightgray')
                self.ax.add_patch(rect)
            self.ax.add_patch(patches.Rectangle((0, 0), 0, 0, edgecolor='none', facecolor='lightgray',
                                                label="Estimated measurements"))

        self.ax.legend(loc="upper left", fontsize=7)

        self.modify_axes()
        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_comparison_of_years(self, meteorological_years, save_name=None):
        self.initialize_plot(None)

        x_vals = []
        y_vals = []

        for year, meteorological_year in meteorological_years.items():
            meteorological_year: MeteorologicalYear
            self.ax.scatter(year, meteorological_year.overall_amount_of_water_needed_in_liters/1000000, color="black")
            x_vals.append(year)
            y_vals.append(meteorological_year.overall_amount_of_water_needed_in_liters/1000000)

        self.ax.plot(x_vals, y_vals)

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Overall Water needed [1.000.000 liters]")
        self.ax.grid(zorder=-2, ls="--", lw="0.5")

        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_day_of_ice_exposures_for_year(self, year, meteorological_years, radiations_at_station, resolution=0.0025, save_name=None):
        self.initialize_plot(None)

        meteorological_year = copy.deepcopy(meteorological_years[year])  # to not modify the original one
        meteorological_year: MeteorologicalYear

        self.ax.set_xlabel(str(year))
        self.ax.set_ylabel("Amount of artificial snowing per day if possible [cm]")

        multiple_measurements.singleton.reset_scope_to_all()
        multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
            dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

        for i, height_level in enumerate(meteorological_year.height_level_objects):
            current_amount_of_snowing_per_day = 0
            x_days_of_exposure = []
            y_snowing_amounts = []

            if i % 6 == 0:
                height_level: HeightLevel
                while True:
                    current_snowing_per_day = current_amount_of_snowing_per_day
                    height_level.clear_simulated_measurements()
                    height_level.artificial_snowing_per_day = current_snowing_per_day
                    multiple_measurements.singleton.simulate(height_level, radiations_at_station)

                    day_of_ice_exposure = height_level.get_time_of_first_ice_exposure_in_new_year()
                    if day_of_ice_exposure is None:
                        break
                    x_days_of_exposure.append(day_of_ice_exposure)
                    y_snowing_amounts.append(current_snowing_per_day)
                    current_amount_of_snowing_per_day += resolution

                self.ax.plot(x_days_of_exposure, y_snowing_amounts,
                             label=self._pretty_label("Date of ice exposure at height " + str(int(height_level.height)) + "m"))
        self.modify_axes()
        self.ax.legend()
        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_day_of_ice_exposures_for_years_at_height(self, meteorological_years, height, radiations_at_station, resolution=0.0025, save_name=None):
        self.initialize_plot(None)

        for year, meteorological_year in meteorological_years.items():
            meteorological_year = copy.deepcopy(meteorological_years[year])  # to not modify the original one
            meteorological_year: MeteorologicalYear

            self.ax.set_ylabel("Amount of artificial snowing per day if possible [cm]")

            multiple_measurements.singleton.reset_scope_to_all()
            multiple_measurements.singleton.change_measurement_resolution_by_start_end_time(
                dt.datetime(year, 10, 1), dt.datetime(year + 1, 9, 30))

            height_level = meteorological_year.get_height_level_close_to_height(height)
            current_amount_of_snowing_per_day = 0
            x_days_of_exposure = []
            y_snowing_amounts = []

            height_level: HeightLevel
            while True:
                current_snowing_per_day = current_amount_of_snowing_per_day
                height_level.clear_simulated_measurements()
                height_level.artificial_snowing_per_day = current_snowing_per_day
                multiple_measurements.singleton.simulate(height_level, radiations_at_station)

                day_of_ice_exposure = height_level.get_time_of_first_ice_exposure_in_new_year()
                if day_of_ice_exposure is None:
                    break
                # having the same year for all, 2020 as leap year, for not having problems with feb 29
                x_days_of_exposure.append(day_of_ice_exposure.replace(year=2020))
                y_snowing_amounts.append(current_snowing_per_day)
                current_amount_of_snowing_per_day += resolution

            self.ax.plot(x_days_of_exposure, y_snowing_amounts,
                         label=self._pretty_label(f"{year} date of ice exposure"))
        self.modify_axes()
        self.ax.set_xlim(dt.datetime(2020, 1, 15))
        self.ax.legend()
        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_shape(self, meteorological_year, aws_station=None, equality_line=None, only_tongue=False,
                   fix_lower_limit=None, fix_upper_limit=None, save_name=None):
        self.initialize_plot(None)
        meteorological_year: MeteorologicalYear

        if only_tongue:
            self.ax.set_xlim([402000, 405500])
            self.ax.set_ylim([214500, 218000])
            ax_colorbar = self.fig.add_axes([0.84, 0.11, 0.02, 0.76])  # left, bottom, width, height
        else:
            self.ax.set_xlim([398000, 405500])
            self.ax.set_ylim([212500, 225000])
            ax_colorbar = self.fig.add_axes([0.7, 0.11, 0.02, 0.76])  # left, bottom, width, height

        self.ax.set_ylabel("x [m]")
        self.ax.set_xlabel("y [m]")

        self.ax.set_aspect("equal")

        self.ax.grid(zorder=-2, ls="--", lw="0.5")

        snr_cmap = matplotlib.cm.get_cmap('winter_r')

        vals_to_plot = [x.get_mean_yearly_water_consumption_of_snow_canons_per_square_meter_in_liters() for x in
                        meteorological_year.height_level_objects]

        # normalize value between 0 and max speed to 0 and 1 for cmap

        upper_limit = fix_upper_limit if fix_upper_limit is not None else max(vals_to_plot)
        lower_limit = fix_lower_limit if fix_lower_limit is not None else min(vals_to_plot)

        norm = matplotlib.colors.Normalize(vmin=lower_limit, vmax=upper_limit)

        cb1 = matplotlib.colorbar.ColorbarBase(ax_colorbar, cmap=snr_cmap,
                                               norm=norm,
                                               orientation='vertical', extend="max")
        cb1.set_label(r'Mean yearly water consumption of snow canons in liters per $m^2$')

        if aws_station is not None:
            self.ax.scatter(*shp.Reader(aws_station).shapes()[0].points[0], zorder=10, s=40, color="red",
                            label="Weather Station")

        if equality_line is not None:
            line_of_equality = shp.Reader(equality_line).shapes()[0].points

            if not only_tongue:
                xs = []
                ys = []
                for x, y in line_of_equality:
                    xs.append(x)
                    ys.append(y)
                self.ax.plot(xs, ys, lw=3, zorder=50, label="Common line of equality")

        for i, height_lvl in enumerate(meteorological_year.height_level_objects):
            height_lvl: HeightLevel

            shp_file = shp.Reader(height_lvl.shape_layer_path)

            for shape in shp_file.shapes():
                color = snr_cmap(norm(vals_to_plot[i])) if vals_to_plot[i] else "white"
                self.ax.add_patch(PolygonPatch(shape.__geo_interface__,
                                               fc=color,
                                               ec="gray"))

        if not not any([aws_station, equality_line]):
            self.ax.legend()

        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_temperature_and_water_equivalent(self, use_summed_measurements=False, save_name=None):
        self.initialize_plot("temperature")

        x_vals = multiple_measurements.singleton.get_all_of("snow_depth",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label="Temperature")

        second_ax = self.ax.twinx()

        if use_summed_measurements:  # has to be summed here for now
            actual_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                "actual_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

            theoretical_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                "theoretical_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

            second_ax.plot(y_dates, actual_melt_water_per_sqm, color="red", label="Measured Meltwater")
            second_ax.plot(
                y_dates, theoretical_melt_water_per_sqm, color="green", label="Modelled Meltwater")

        second_ax.set_ylabel("l/m^2 per " + multiple_measurements.singleton.get_time_resolution(of="summed",
                                                                                            as_beautiful_string=True))
        self.ax.legend(loc="upper left")
        second_ax.legend(loc="upper right")      

        self.modify_axes()
        self.ax.set_ylabel("Temperature [°C]")
        self.show_save_and_close_plot("temperature", save_name=save_name)

    def plot_energy_balance_components(self,
                                       options, use_summed_measurements=False, save_name=None):
        x_vals, y_dates = multiple_measurements.singleton.get_vals_and_dates_of_selected_options(options, use_summed_measurements)

        self.initialize_plot("energy_balance")

        if len(options) == 4 and "sw_radiation_in" in options and "sw_radiation_out" in options and "lw_radiation_in" in options and "lw_radiation_out" in options:
            title_used_options = "Net radiation (SW and LW)"
        else:
            title_used_options = ", ".join([self.title_dict[value_name] for value_name in options])

        self.ax.plot(y_dates, x_vals,
                     zorder=3, label=title_used_options, linewidth=2)

        self.ax.legend(loc="upper right")

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        # self.ax.set_title(title_used_options + " - Energy input" + summed_title_appendix)
        self.ax.set_ylabel("Energy [W/m^2]")
        self.modify_axes()
        self.show_save_and_close_plot("energy_balance", save_name=save_name)

    @staticmethod
    def do_periodic_trend_elimination(x_vals, y_dates, keep_trend):
        # find first actual date where there are values
        reference_index_first_good_measurement = 0
        for i in range(len(x_vals)):
            if x_vals[i] is not None:
                reference_index_first_good_measurement = i
                break

        reference_index_current_measurement = reference_index_first_good_measurement

        if not keep_trend:  # periodic and trend is eliminated by taking always previous year
            diff_vals = list()
            diff_dates = list()
            for x_val, y_date in zip(x_vals[reference_index_first_good_measurement:],
                                     y_dates[reference_index_first_good_measurement:]):
                if None not in [x_val, y_date]:
                    if y_date >= y_dates[reference_index_current_measurement] + DAYS_365:
                        diff_vals.append(x_val - x_vals[reference_index_current_measurement])
                        diff_dates.append(y_date)

                        reference_index_current_measurement += 1

        else:  # trend is not eliminated by taking always the first year as reference
            diff_vals = list()
            diff_dates = list()
            start_date = y_dates[reference_index_first_good_measurement]
            leap_days = dt.timedelta(days=0)

            for x_val, y_date in zip(x_vals[reference_index_first_good_measurement:],
                                     y_dates[reference_index_first_good_measurement:]):
                if None not in [x_val, y_date]:
                    years_passed = int((y_date - start_date).total_seconds() / DAYS_365.total_seconds())
                    if fc.value_changed(years_passed, "years_passed"):
                        if calendar.isleap(y_date.year) and y_date.month <= 2 and y_date.day < 29:
                            leap_days += dt.timedelta(days=1)
                        reference_index_current_measurement = reference_index_first_good_measurement

                    if years_passed >= 1:
                        if y_date >= y_dates[reference_index_current_measurement] + DAYS_365 * years_passed + leap_days:
                            if x_vals[reference_index_current_measurement] is not None:  # can happen .. take it
                                diff_vals.append(x_val - x_vals[reference_index_current_measurement])
                                diff_dates.append(y_date)

                            reference_index_current_measurement += 1
        return diff_vals, diff_dates

    def plot_periodic_trend_eliminated_total_energy_balance(self, use_summed_measurements=False, keep_trend=True,
                                                            save_name=None):
        x_vals = multiple_measurements.singleton.get_all_of("total_energy_balance",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)
        self.initialize_plot("trend")

        if y_dates[-1] - y_dates[0] < DAYS_365:
            print("Cant trend eliminate for data range less than one year")
            return

        diff_vals, diff_dates = self.do_periodic_trend_elimination(x_vals, y_dates, keep_trend)

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, diff_vals)
        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.set_ylabel("Energy [W/m^2]")
        self.modify_axes()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        # self.ax.set_title("Total energy balance - Periodic trend eliminated" + summed_title_appendix)
        self.show_save_and_close_plot("trend", save_name=save_name)

    def plot_periodic_trend_eliminated_selected_option(self, options, use_summed_measurements=False, keep_trend=True,
                                                       save_name=None):
        x_vals, y_dates = multiple_measurements.singleton.get_vals_and_dates_of_selected_options(options, use_summed_measurements)
        self.initialize_plot("trend")

        days_365 = dt.timedelta(days=365)  # 365.2422 days in year approximately

        if y_dates[-1] - y_dates[0] < days_365:
            print("Cant trend eliminate for data range less than one year")
            return

        diff_vals, diff_dates = self.do_periodic_trend_elimination(x_vals, y_dates, keep_trend)

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, diff_vals)
        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.set_ylabel("Energy [W/m^2]")
        self.modify_axes()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        title_used_options = ", ".join([self.title_dict[value_name] for value_name in options])
        # self.ax.set_title(title_used_options + " - Periodic trend eliminated" + summed_title_appendix)
        self.show_save_and_close_plot("trend", save_name=save_name)


singleton = Visualize()
