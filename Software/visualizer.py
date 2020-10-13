import os
import matplotlib.pyplot as plt
from config_handler import cfg
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
from measurement_handler import MeasurementHandler
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
from hydrologic_year import HydrologicYear
from matplotlib.ticker import MaxNLocator
from measurement import MeanStationMeasurement
import copy
import locale


matplotlib.rcParams.update({'font.size': float(cfg["plot_text_size"])})
matplotlib.rcParams['axes.formatter.use_locale'] = True
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

DAYS_365 = dt.timedelta(days=365)  # hours=5, minutes=48     365.2422 days in year approximately  dont change to that


class Visualizer:
    result_plot_path = cfg["RESULT_PLOT_PATH"]
    
    if not os.path.exists(result_plot_path):
        os.makedirs(result_plot_path)    

    title_dict = {
        "sw_radiation_in": "Short wave in",
        "sw_radiation_out": "Short wave out",
        "lw_radiation_in": "Long wave in",
        "lw_radiation_out": "Long wave out",
        "sensible_heat": "Sensible heat",
        "latent_heat": "Latent heat",
        "temperature": "Temperature",
        "precipitation_heat": "Precipitation heat",
        "total_energy_balance": "Total energy balance",
        "total_snow_depth": "Total Snow Height",
        "snow_depth_natural": "Natural Snow Height",
        "snow_depth_artificial": "Artificial Snow Height",
        "total_snow_water_equivalent": "Total snow water equivalent",
        "artificial_snow_water_equivalent": "Artificial snow water equivalent",
        "natural_snow_water_equivalent": "Natural snow water equivalent",
        "rel_moisture": "Relative moisture",
        "wind_speed": "Wind speed",
        "air_pressure": "Air pressure",
        "measured_ice_thickness": "Measured ice thickness",
        "cumulated_ice_thickness": "Cumulated ice thickness",
        "actual_melt_water_per_sqm": r"Actual melt water",
        "theoretical_melt_water_per_sqm": r"Theoretical melt water",
    }

    unit_dict = {
        "sw_radiation_in": r"$\frac{W}{m^2}$",
        "sw_radiation_out": r"$\frac{W}{m^2}$",
        "lw_radiation_in": r"$\frac{W}{m^2}$",
        "lw_radiation_out": r"$\frac{W}{m^2}$",
        "sensible_heat": r"$\frac{W}{m^2}$",
        "latent_heat": r"$\frac{W}{m^2}$",
        "temperature": r"$C^\circ$",
        "precipitation_heat": r"$\frac{W}{m^2}$",
        "total_energy_balance": r"$\frac{W}{m^2}$",
        "total_snow_depth": r"$m$",
        "snow_depth_natural": r"$m$",
        "snow_depth_artificial": r"$m$",
        "rel_moisture": r"$%$",
        "wind_speed": r"$\frac{m}{s}$",
        "air_pressure": r"$Pa$",
        "measured_ice_thickness": r"$m$",
        "cumulated_ice_thickness": r"$m$",
        "actual_melt_water_per_sqm": r"$l$",
        "theoretical_melt_water_per_sqm": r"$l$",
    }

    accumulate_plots = False
    show_plots = True

    fig = None
    ax = None

    plot_type_initialized = {
        "energy_balance": False,
        "trend": False,
        "temperature": False
    }

    @classmethod
    def change_result_plot_subfolder(cls, result_plot_subfolder):
        if not os.path.exists(cls.result_plot_path + '/' + result_plot_subfolder):
            os.makedirs(cls.result_plot_path + '/' + result_plot_subfolder)
        cls.result_plot_path = cls.result_plot_path + '/' + result_plot_subfolder

    @classmethod
    def _pretty_label(cls, key):
        try:
            return cls.title_dict[key]
        except KeyError:
            return key

    @classmethod
    def initialize_plot(cls, type_, figsize=(14, 9), create_ax=True):
        """
        :rtype: object
        """

        yet_to_initialize = True

        if type_ is not None:
            if cls.accumulate_plots:
                # close other plot types that are open
                for plot_type in cls.plot_type_initialized:
                    if type_ != plot_type:
                        if cls.plot_type_initialized[plot_type]:
                            cls.plot_type_initialized[plot_type] = False
                            plt.close()
                            break

                if cls.plot_type_initialized[type_]:
                    yet_to_initialize = False
                else:
                    cls.plot_type_initialized[type_] = True
            else:
                plt.close()  # should one be open

        if yet_to_initialize or not bool(cfg["PRO_VERSION"]):
            cls.fig = plt.figure(figsize=figsize)
            if create_ax:
                cls.ax = cls.fig.add_subplot(111)

    @classmethod
    def modify_axes(cls):
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..
        mondays = mdates.WeekdayLocator(mdates.MONDAY)

        # calculate time_spawn between first and last measurement
        time_spawn = dt.timedelta(days=cls.ax.get_xlim()[1] - cls.ax.get_xlim()[0])

        time_border_1 = dt.timedelta(days=3*365)
        time_border_2 = dt.timedelta(days=2*365)
        time_border_3 = dt.timedelta(days=150)
        time_border_4 = dt.timedelta(days=60)

        # major and ax title
        if time_spawn >= time_border_1:
            cls.ax.set_xlabel("Year")
            cls.ax.xaxis.set_major_locator(years)
            cls.ax.xaxis.set_major_formatter(year_labels)
        elif time_border_3 <= time_spawn <= time_border_1:  # 1 till 3 beware
            cls.ax.xaxis.set_major_locator(years)
            cls.ax.xaxis.set_major_formatter(year_labels)
            cls.ax.set_xlabel("Year")
            cls.ax.xaxis.set_tick_params(rotation=45, pad=15)  # only major are rotated
            cls.ax.xaxis.set_tick_params(which="minor", labelsize=float(cfg["plot_text_size_minor"]))  # only major are rotated
            cls.ax.xaxis.set_minor_locator(months)

            if time_border_3 <= time_spawn <= time_border_2:
                cls.ax.xaxis.set_minor_formatter(month_labels)
        elif time_border_4 <= time_spawn <= time_border_3:
            cls.ax.xaxis.set_major_locator(months)
            cls.ax.xaxis.set_major_formatter(month_labels)
            cls.ax.set_xlabel("Month")
            # cls.ax.xaxis.set_tick_params()  # only major are rotated
            cls.ax.xaxis.set_tick_params(which="minor")  # only major are rotated
            cls.ax.xaxis.set_minor_locator(mondays)

        # else even smaller take month as major, and days as minor maybe?

        # ELSE just take default tick and ticklabels

        cls.ax.grid(linestyle="--", alpha=0.5, which='major')
        cls.ax.grid(linestyle="--", alpha=0.4, which='minor')

    @classmethod
    def show_save_and_close_plot(cls, type_, save_name=None):
        if cls.show_plots or cfg["GUI"]:
            plt.tight_layout()
            plt.show()

        if save_name is not None:
            plt.savefig(cls.result_plot_path + "/" + save_name + ".png", dpi=cfg["PLOT_RESOLUTION"],
                        bbox_inches='tight')
            cls.plot_type_initialized = dict.fromkeys(cls.plot_type_initialized, False)

        if not cls.accumulate_plots or not bool(cfg["PRO_VERSION"]):
            plt.close()
            cls.plot_type_initialized = dict.fromkeys(cls.plot_type_initialized, False)

    @staticmethod
    def _color_generator():
        colors = ["blue", "red", "green", "dimgray", "rosybrown", "lightgray", "lightcoral", "darkorange",
                  "darkgoldenrod", "darkkhaki", "olive", "darkseagreen", "mediumaquamarine", "rebeccapurple", "pink",
                  "darkblue", "black"]
        i = 0
        while True:
            if i == len(colors):
                i = 0
            yield colors[i]
            i += 1

    @classmethod
    def plot_scatter_measured_and_component(cls, years_to_plot, component, save_name=None):
        # could be further generalized of course .. but this ist just needed for the thesis here

        cls.initialize_plot(None)

        marker_types = ["o", "x"]  # extend how you like .. currently only 2, cause only 2 years
        marker_colors = ["orange", "blue"]

        y_dates = MeasurementHandler.get_all_of("datetime",
                                                use_summed_measurements=True)

        actual_melt_water_per_sqm = MeasurementHandler.get_all_of(
            "actual_mm_we_per_d", use_summed_measurements=True)

        theoretical_melt_water_per_sqm = MeasurementHandler.get_all_of(
            component, use_summed_measurements=True)

        for date, actual, theoretical in zip(y_dates, actual_melt_water_per_sqm, theoretical_melt_water_per_sqm):
            if actual is not None and theoretical is not None:
                year_index = years_to_plot.index(date.year)

                cls.ax.scatter(actual, theoretical, marker=marker_types[year_index], c=marker_colors[year_index])

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

        cls.ax.plot(actual_melt_water_per_sqm,
                     poly1d_fn(actual_melt_water_per_sqm), linestyle="--", label="Regression line")

        if component == "theoretical_mm_we_per_d":
            max_value = max(actual_melt_water_per_sqm)
            cls.ax.plot([0, max_value], [0, max_value], linestyle="--", label="Line of unity")

            cls.ax.set_aspect("equal")
            cls.ax.set_ylabel("Modelled ablation [mm w.e./d]")
        elif component == "temperature":
            cls.ax.set_ylabel("Temperature [°C]")

        cls.ax.set_xlabel("Measured ablation [mm w.e./d]")

        # create legend entries
        for i, year in enumerate(years_to_plot):
            cls.ax.scatter(None, None, marker=marker_types[i], c=marker_colors[i], label=str(year))

        cls.ax.set_xlim(0, cls.ax.get_xlim()[1])
        cls.ax.set_ylim(0, cls.ax.set_ylim()[1])

        cls.ax.legend()
        cls.ax.grid(linestyle="--", alpha=0.5)

        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_scatter_measured_modelled_ablation(cls, tups, save_name=None, max_estimated_ablation_measures_percent=100, measured_per_day_has_to_be_above_mm=0):
        cls.initialize_plot(None)

        all_modelled_mm = []
        all_measured_mm = []
        all_total_snow_depths = []
        all_pegel_mm = []
        for tup in tups:
            start_time = tup[0]
            end_time = tup[1]
            pegel_measure = tup[2] / 100

            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(start_time, end_time)

            measurement_validities_valid = [
                x["relative_ablation_measured"] == MeanStationMeasurement.valid_states["valid"]
                for x in MeasurementHandler.get_all_of("measurement_validity", use_summed_measurements=True)]
            measured_percentage_estimated = (1-sum(measurement_validities_valid)/len(measurement_validities_valid))*100
            if measured_percentage_estimated > max_estimated_ablation_measures_percent:
                continue

            measured_ablations = MeasurementHandler.get_all_of("relative_ablation_measured",
                                                               use_summed_measurements=True)
            modelled_ablations = MeasurementHandler.get_all_of("relative_ablation_modelled",
                                                               use_summed_measurements=True)
            total_snow_depths = MeasurementHandler.get_all_of("total_snow_depth",
                                                              use_summed_measurements=True)

            for i in range(len(measured_ablations)):
                measured_ablations[i] = 0 if measured_ablations[i] is None else measured_ablations[i]
            for i in range(len(modelled_ablations)):
                modelled_ablations[i] = 0 if modelled_ablations[i] is None else modelled_ablations[i]

            time_spawn_in_days = (end_time - start_time).total_seconds() / 60 / 60 / 24

            for modelled, measured, total_snow_depth in zip(modelled_ablations, measured_ablations, total_snow_depths):
                if measured * 1000 >= measured_per_day_has_to_be_above_mm:
                    all_modelled_mm.append(modelled * 1000)
                    all_measured_mm.append(measured * 1000)
                    all_pegel_mm.append(pegel_measure / time_spawn_in_days * 1000)
                    all_total_snow_depths.append(total_snow_depth)

        all_measured_mm_no0 = []
        all_modelled_mm_no0 = []

        for meas, mod in zip(all_measured_mm, all_modelled_mm):
            if meas and mod:
                all_measured_mm_no0.append(meas)
                all_modelled_mm_no0.append(mod)

        for mes, mod, total_snow in zip(all_measured_mm, all_modelled_mm, all_total_snow_depths):
            color = "blue" if not total_snow else "red"
            cls.ax.scatter(mes, mod, color=color, s=2.5)
        cls.ax.scatter(None, None, color="blue", s=2.5, label="no snow laying")
        cls.ax.scatter(None, None, color="red", s=2.5, label="snow laying")

        z = np.polyfit(all_measured_mm, all_modelled_mm, 1)
        p = np.poly1d(z)
        cls.ax.plot(all_measured_mm, p(all_measured_mm), color="orange", ls="--", label="Trendline")

        z = np.polyfit(all_measured_mm_no0, all_modelled_mm_no0, 1)
        p = np.poly1d(z)
        cls.ax.plot(all_measured_mm_no0, p(all_measured_mm_no0), color="red", ls="--", label="Trendline no 0s")

        cls.ax.set_xlabel("Measured [mm]")
        cls.ax.set_ylabel("Modelled [mm]")
        cls.ax.set_xlim(-3, 300)
        cls.ax.set_ylim(-3, 300)
        cls.ax.plot([0, 300], [0, 300], color='green')
        cls.ax.grid()
        cls.ax.legend()
        cls.ax.set_title(save_name)
        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def get_string_out_of_components(cls, components):
        if len(components) == 4 and "sw_radiation_in" in components and "sw_radiation_out" in components and "lw_radiation_in" in components and "lw_radiation_out" in components:
            return "Net radiation (SW and LW)"
        elif len(components) == 1:
            return cls.title_dict[components[0]]
        else:
            return ", ".join([cls.title_dict[value_name] for value_name in components])

    @classmethod
    def get_unit_out_of_components(cls, components):
        units = set()
        for component in components:
            units.add(cls.unit_dict[component])
        if len(units) > 1:
            return "Multiple units!"
        elif not units:
            return ""
        else:
            return list(units)[0]

    @classmethod
    def plot_components(cls, components1: tuple, components2: tuple = None, cumulate_components1=False,
                        cumulate_components2=False, use_summed_measurements=False, save_name=None):
        cls.initialize_plot(None)

        color_generator = cls._color_generator()
        y_dates = MeasurementHandler.get_all_of("datetime",
                                                use_summed_measurements=use_summed_measurements)

        if cumulate_components1:
            x_vals = MeasurementHandler.get_cumulated_vals_of_components(
                components1, use_summed_measurements)
            cls.ax.plot(y_dates, x_vals, label=cls.get_string_out_of_components(components1), color=next(color_generator))
        else:
            for component in components1:
                try:
                    x_vals = MeasurementHandler.get_all_of(
                        component, use_summed_measurements=use_summed_measurements)
                    cls.ax.plot(y_dates, x_vals, label=cls._pretty_label(component), color=next(color_generator))
                except AttributeError:
                    print(component, "does not exist")

        cls.ax.legend(loc="upper left")
        cls.ax.set_ylabel(cls.get_unit_out_of_components(components1))

        if components2:
            ax2 = cls.ax.twinx()
            if cumulate_components2:
                x_vals = MeasurementHandler.get_cumulated_vals_of_components(
                    components2, use_summed_measurements)
                ax2.plot(y_dates, x_vals, label=cls.get_string_out_of_components(components2),
                             color=next(color_generator))
            else:
                for component in components2:
                    try:
                        x_vals = MeasurementHandler.get_all_of(
                            component, use_summed_measurements=use_summed_measurements)
                        ax2.plot(y_dates, x_vals, label=cls._pretty_label(component), color="orange")
                    except AttributeError:
                        print(component, "does not exist")
            ax2.legend(loc="upper right")
            ax2.set_ylabel(cls.get_unit_out_of_components(components2))
        cls.modify_axes()

        if int(cfg["PLOT_TITLE"]):
            title = cls.get_string_out_of_components(components1)
            if components2:
                title += "\n vs \n" + cls.get_string_out_of_components(components2)
            if use_summed_measurements:
                title += "\n Used summed measurements"
            plt.title(title)

        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_components_lvls(cls, height_level_objects, components1: tuple, components1_unit, components2: tuple = None,
                             components2_unit=None, factor=1, stack_fill=False, use_summed_measurements=True,
                             show_estimated_measurement_areas=False, save_name=None):

        cls.initialize_plot(None)

        color_generator = cls._color_generator()

        y_dates = MeasurementHandler.get_all_of("datetime",
                                                use_summed_measurements=use_summed_measurements)

        if len(height_level_objects) > 1 and len(components1) > 1:
            exit("Cannot visualize that, either one height lvl and multiple components or multiple height lvls and one"
                 "component")

        if len(components1) > 1:
            cls.ax.set_ylabel(f"Snow water equivalent [{components1_unit}]")  # TODO this actually a manual thing here, should be removed
        else:
            cls.ax.set_ylabel(f"{cls._pretty_label(components1[0])} [{components1_unit}]")

        i = 0
        for component in components1:
            # bad if more components
            for height_lvl in height_level_objects:
                height_lvl: HeightLevel
                x_vals = []
                for measure in height_lvl.simulated_measurements:
                    x_vals.append(getattr(measure, component)*factor)

                label = cls._pretty_label(component) if len(height_level_objects) == 1 else "Average elevation band " + str(int(height_lvl.height)) + "m a.s.l."
                color = next(color_generator)
                cls.ax.plot(y_dates, x_vals, label=label, color=color)
                if stack_fill:
                    cls.ax.fill(y_dates + [y_dates[-1]], x_vals + [0], color=color)  # hacky hack to fill till bottom
                i += 1

        if show_estimated_measurement_areas:
            zorder = 5 if stack_fill else -1
            for estimated_area in MeasurementHandler.get_time_frames_of_measure_types_with_at_least_one_with_state(
                    MeanStationMeasurement.valid_states["estimated"], ["temperature", "rel_moisture", "air_pressure",
                                                                       "wind_speed", "sw_radiation_in",
                                                                       "sw_radiation_out", "lw_radiation_in",
                                                                       "lw_radiation_out"]):

                rect = patches.Rectangle((estimated_area[0], cls.ax.get_ylim()[0]), estimated_area[1]-estimated_area[0], cls.ax.get_ylim()[1]-cls.ax.get_ylim()[0],
                                         edgecolor='none', facecolor='lightgray', zorder=zorder, alpha=1)
                cls.ax.add_patch(rect)
            cls.ax.add_patch(patches.Rectangle((0, 0), 0, 0, edgecolor='none', facecolor='lightgray',
                                                label="Gap-filled measurements"))

        cls.ax.legend(loc="upper left")  # fontsize=7

        cls.modify_axes()
        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_comparison_of_years(cls, meteorological_years, save_name=None):
        cls.initialize_plot(None)

        x_vals = []
        y_vals = []

        print("Table artificial snow production for neutral balance, yearly comparison:")
        print("[Year]\t[m^3]")
        last_year = None
        for year, meteorological_year in meteorological_years.items():
            if last_year is not None and last_year + 1 != year:  # TODO rework this, this is just a dirty quick way to implement the gap year, and works only if only one year is missing
                x_vals.append(cls.met_year_str(last_year+1))
                y_vals.append(0)
            meteorological_year: HydrologicYear
            x_vals.append(cls.met_year_str(year))
            y_vals.append(meteorological_year.overall_amount_of_snow_needed_in_cubic_meters/1000000)
            print(f"{year}\t{round(meteorological_year.overall_amount_of_snow_needed_in_cubic_meters, 1)}")
            last_year = year

        cls.ax.set_xlabel("Year")
        cls.ax.set_ylabel(r"Total volume of ASP necessary for neutral balance [$1.000.000~m^3$]")
        cls.ax.grid(zorder=1, ls="--", lw="0.5", axis="y")
        cls.ax.bar(x_vals, y_vals, align='center', alpha=0.6, color="blue", zorder=5)

        # cls.ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_compare_water_and_height(cls, years, meteorological_years, save_name=None):
        cls.initialize_plot(None)

        color_gen = cls._color_generator()

        for year in years:
            x_vals = []
            y_vals = []
            for height_level in meteorological_years[year].height_level_objects:
                meteorological_year: HydrologicYear
                x_vals.append(
                    height_level.get_mean_yearly_water_consumption_of_snow_canons_per_square_meter_in_liters()/1000)
                y_vals.append(height_level.height)

            label = cls.met_year_str(year) if len(years) > 1 else None
            cls.ax.plot(x_vals, y_vals, color=next(color_gen), zorder=5, label=label)

        cls.ax.set_xlabel("Average specific water required in elevation band [m w.e.]")
        cls.ax.set_ylabel(r"Mean elevation [m a.s.l.]")
        cls.ax.grid(zorder=1, ls="--", lw="0.5", axis="both")
        if len(years) > 1:
            cls.ax.legend()
        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_day_of_ice_exposures_for_year(cls, year, meteorological_years, radiations_at_station, resolution=0.0025, save_name=None):
        # TODO here and for the other plot could be drawn a line till 1. oct in the end
        cls.initialize_plot(None)

        meteorological_year = copy.deepcopy(meteorological_years[year])  # to not modify the original one
        meteorological_year: HydrologicYear

        MeasurementHandler.reset_scope_to_all()
        MeasurementHandler.change_measurement_resolution_by_start_end_time(
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
                    MeasurementHandler.simulate(height_level, radiations_at_station)

                    day_of_ice_exposure = height_level.get_time_of_first_ice_exposure_in_new_year()
                    if day_of_ice_exposure is None:
                        break
                    x_days_of_exposure.append(day_of_ice_exposure)
                    y_snowing_amounts.append(current_snowing_per_day*cfg["ARTIFICIAL_SNOW_SWE_FACTOR"]*1000)
                    current_amount_of_snowing_per_day += resolution

                cls.ax.plot(x_days_of_exposure, y_snowing_amounts,
                             label=cls._pretty_label("Average elevation band " + str(int(height_level.height)) + "m a.s.l."))
        cls.modify_axes()
        cls.ax.set_xlabel("Date of bare ice exposure")
        cls.ax.set_ylabel("Daily ASP when conditions permit [mm w.e.]")
        cls.ax.legend()
        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_day_of_ice_exposures_for_years_at_height(cls, meteorological_years, height, radiations_at_station, resolution=0.0025, save_name=None):
        cls.initialize_plot(None)

        for year, meteorological_year in meteorological_years.items():
            meteorological_year = copy.deepcopy(meteorological_years[year])  # to not modify the original one
            meteorological_year: HydrologicYear

            MeasurementHandler.reset_scope_to_all()
            MeasurementHandler.change_measurement_resolution_by_start_end_time(
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
                MeasurementHandler.simulate(height_level, radiations_at_station)

                day_of_ice_exposure = height_level.get_time_of_first_ice_exposure_in_new_year()
                if day_of_ice_exposure is None:
                    break
                # having the same year for all, 2020 as leap year, for not having problems with feb 29
                x_days_of_exposure.append(day_of_ice_exposure.replace(year=2020))
                y_snowing_amounts.append(current_snowing_per_day*cfg["ARTIFICIAL_SNOW_SWE_FACTOR"]*1000)
                current_amount_of_snowing_per_day += resolution

            cls.ax.plot(x_days_of_exposure, y_snowing_amounts,
                         label=cls.met_year_str(year))
        cls.modify_axes()
        cls.ax.set_xlabel("Date of bare ice exposure")
        cls.ax.set_ylabel("Daily ASP when conditions permit [mm w.e.]")
        cls.ax.set_xlim(dt.datetime(2020, 1, 15))
        cls.ax.legend()
        cls.show_save_and_close_plot(None, save_name=save_name)

    @classmethod
    def plot_pasterze(cls, meteorological_years_dict, years, aws_station=None, equality_line=None, only_tongue=False,
                      fix_lower_limit=None, fix_upper_limit=None, save_name=None):

        only_one_ax = True

        # TODO this is not so beautiful at all .. when time, take a look at this again

        axes = []
        if len(years) == 1:
            cls.initialize_plot(None)
            axes.append(cls.ax)
        elif len(years) > 1:
            cls.initialize_plot(None, figsize=(14, 11), create_ax=False)
            plt.subplots_adjust(wspace=0.1, hspace=0.03)
            for i in range(len(years)):
                # TODO for later if needed find out 22 or 33 or whatever
                axes.append(cls.fig.add_subplot(f"23{i+1}"))
                only_one_ax = False

        snr_cmap = matplotlib.cm.get_cmap('coolwarm')

        if only_tongue:
            if only_one_ax:
                ax_colorbar = cls.fig.add_axes([0.8, 0.11, 0.02, 0.76])  # left, bottom, width, height
            else:
                ax_colorbar = cls.fig.add_axes([0.93, 0.11, 0.02, 0.76])  # left, bottom, width, height
        else:
            ax_colorbar = cls.fig.add_axes([0.7, 0.11, 0.02, 0.76])  # left, bottom, width, height

        if not only_one_ax:
            if None in (fix_upper_limit, fix_lower_limit):
                exit("When plotting multiple years, fix limits have to be set!")
            upper_limit = fix_upper_limit
            lower_limit = fix_lower_limit

            norm = matplotlib.colors.Normalize(vmin=lower_limit, vmax=upper_limit)
            cb1 = matplotlib.colorbar.ColorbarBase(ax_colorbar, cmap=snr_cmap,
                                                   norm=norm,
                                                   orientation='vertical', extend="both")
            cb1.set_label(r'Elevation-averaged specific ASP necessary for neutral balance [m w.e.]')

        for ax, year in zip(axes, years):
            meteorological_year: HydrologicYear
            meteorological_year = meteorological_years_dict[year]

            if only_tongue:
                ax.set_xlim([402000, 405500])
                ax.set_ylim([214500, 218000])
            else:
                ax.set_xlim([398000, 405500])
                ax.set_ylim([212500, 225000])

            if only_one_ax:
                ax.set_ylabel("x [m]")
                ax.set_xlabel("y [m]")
            else:
                ax.get_xaxis().set_visible(False)
                ax.get_yaxis().set_visible(False)

            ax.set_aspect("equal")
            ax.grid(zorder=-2, ls="--", lw="0.5")

            vals_to_plot = [x.get_mean_yearly_water_consumption_of_snow_canons_per_square_meter_in_liters()/1000 for x in
                            meteorological_year.height_level_objects]

            # normalize value between 0 and max speed to 0 and 1 for cmap
            if only_one_ax:
                upper_limit = fix_upper_limit if fix_upper_limit is not None else max(vals_to_plot)
                lower_limit = fix_lower_limit if fix_lower_limit is not None else min(vals_to_plot)

                norm = matplotlib.colors.Normalize(vmin=lower_limit, vmax=upper_limit)
                cb1 = matplotlib.colorbar.ColorbarBase(ax_colorbar, cmap=snr_cmap,
                                                       norm=norm,
                                                       orientation='vertical', extend="both")
                cb1.set_label(r'Elevation-averaged specific ASP necessary for neutral balance [m w.e.]')

                if aws_station is not None:
                    ax.scatter(*shp.Reader(aws_station).shapes()[0].points[0], zorder=10, s=40, color="red",
                                    label="Weather Station")
            else:
                ax.set_title(cls.met_year_str(year))

            if equality_line is not None and not only_tongue:
                # line_of_equality = shp.Reader(equality_line).shapes()[0].points
                for line_part in shp.Reader(equality_line).shapes():
                    if not only_tongue:
                        xs = []
                        ys = []
                        for x, y in line_part.points:
                            xs.append(x)
                            ys.append(y)
                        ax.plot(xs, ys, lw=3, zorder=50, color="red")
                ax.plot(0, 0, lw=3, zorder=50, color="red", label="Common line of equality")

            for i, height_lvl in enumerate(meteorological_year.height_level_objects):
                height_lvl: HeightLevel

                shp_file = shp.Reader(height_lvl.shape_layer_path)

                for shape in shp_file.shapes():
                    color = snr_cmap(norm(vals_to_plot[i])) if vals_to_plot[i] else "white"
                    ax.add_patch(PolygonPatch(shape.__geo_interface__,
                                                   fc=color,
                                                   ec="gray"))
            if only_one_ax:
                if any([aws_station, equality_line]):
                    ax.legend()

        cls.show_save_and_close_plot(None, save_name=save_name)

    @staticmethod
    def met_year_str(year):
        """
        Converts year (2016) to 2016/17
        """
        return str(year)+'/'+str(int(year)+1)[2:4]

    @classmethod
    def plot_periodic_trend_eliminated_selected_option(cls, options, use_summed_measurements=False, keep_trend=True,
                                                       save_name=None):
        x_vals = MeasurementHandler.get_cumulated_vals_of_components(options, use_summed_measurements)
        cls.initialize_plot("trend")

        days_365 = dt.timedelta(days=365)  # 365.2422 days in year approximately

        y_dates = MeasurementHandler.get_all_of("datetime",
                                                use_summed_measurements=use_summed_measurements)

        if not y_dates or y_dates[-1] - y_dates[0] < days_365:
            print("Cant trend eliminate for data range less than one year")
            return

        diff_vals, diff_dates = cls.do_periodic_trend_elimination(x_vals, y_dates, keep_trend)

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        cls.ax.plot(diff_dates, diff_vals)
        cls.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        cls.ax.set_ylabel("Energy [W/m^2]")
        cls.modify_axes()

        if int(cfg["PLOT_TITLE"]):
            summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"
            title_used_options = ", ".join([cls.title_dict[value_name] for value_name in options])
        # cls.ax.set_title(title_used_options + " - Periodic trend eliminated" + summed_title_appendix)
        cls.show_save_and_close_plot("trend", save_name=save_name)

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
