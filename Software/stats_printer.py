from config_handler import cfg
from measurement_handler import MeasurementHandler
from measurement import MeanStationMeasurement


class Statistics:
    @staticmethod
    def compare_pegel_measured_and_modelled_for_time_intervals(tups, heading=None, max_estimated_ablation_measures_percent=100):
        """
        tups include starttime, endtime and pegel
        """
        if heading is not None:
            print(heading)

        print("Time span, Modeled [m], Pegel measure [m], Diff [mm/d], Pressure transducer measure [m], Diff [mm/d], % estimated")

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
                for x in MeasurementHandler.get_all_of("measurement_validity", use_mean_measurements=True)]

            measured_percentage_estimated = (1-sum(measurement_validities_valid)/len(measurement_validities_valid))*100

            if measured_percentage_estimated > max_estimated_ablation_measures_percent:
                continue

            measured_ablations = MeasurementHandler.get_all_of("relative_ablation_measured",
                                                               use_mean_measurements=True)
            modelled_ablations = MeasurementHandler.get_all_of("relative_ablation_modelled",
                                                               use_mean_measurements=True)
            total_snow_depths = MeasurementHandler.get_all_of("total_snow_depth",
                                                              use_mean_measurements=True)

            datetimes = MeasurementHandler.get_all_of("datetime",
                                                      use_mean_measurements=True)

            # when fixing measurements, then this should be close to zero all the time
            # amount_of_nones_in_measured_ablation = sum(x is None for x in measured_ablations)

            for i in range(len(measured_ablations)):
                measured_ablations[i] = 0 if measured_ablations[i] is None else measured_ablations[i]
            for i in range(len(modelled_ablations)):
                modelled_ablations[i] = 0 if modelled_ablations[i] is None else modelled_ablations[i]

            modelled_ablation = sum(modelled_ablations)
            measured_ablation = sum(measured_ablations)

            time_spawn_in_days = (end_time - start_time).total_seconds() / 60 / 60 / 24

            for modelled, measured, total_snow_depth in zip(modelled_ablations, measured_ablations, total_snow_depths):
                all_modelled_mm.append(modelled * 1000)
                all_measured_mm.append(measured * 1000)
                all_pegel_mm.append(pegel_measure / time_spawn_in_days * 1000)
            all_total_snow_depths.extend(total_snow_depths)

            # create tabular line
            cols = [f"{start_time.strftime('%d.%m.%Y')} - {end_time.strftime('%d.%m.%Y')}",
                    str(round(modelled_ablation, 3)),
                    str(round(pegel_measure, 3)),
                    str(round((pegel_measure - modelled_ablation) * 1000 / time_spawn_in_days, 1)),
                    str(round(measured_ablation, 3)),
                    str(round((measured_ablation - modelled_ablation) * 1000 / time_spawn_in_days, 1)),
                    str(round(measured_percentage_estimated, 2))]

            print(",".join(cols))

        # create tabulars last line with summed values
        all_modelled_m = sum(all_modelled_mm) / 1000
        all_pegel_m = sum(all_pegel_mm)/1000
        all_measured_m = sum(all_measured_mm)/1000
        overall_time_spawn_in_days = (tups[-1][1] - tups[0][0]).total_seconds() / 60 / 60 / 24

        cols = ["",
                str(round(all_modelled_m, 3)),
                str(round(all_pegel_m, 3)),
                str(round((all_pegel_m - all_modelled_m) * 100 / overall_time_spawn_in_days, 1)),
                str(round(all_measured_m, 3)),
                str(round((all_measured_m - all_modelled_m) * 100 / overall_time_spawn_in_days, 1))]

        print(",".join(cols))
