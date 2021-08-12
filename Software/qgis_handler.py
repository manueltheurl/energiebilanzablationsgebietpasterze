import sys
from qgis.core import QgsApplication

QgsApplication.setPrefixPath('/usr', True)  # will be different in windows
qgs = QgsApplication([], False)
qgs.initQgis()

sys.path.append("/usr/share/qgis/python/plugins")  # will be different in windows

import processing
from processing.core.Processing import Processing
Processing.initialize()
from qgis.analysis import QgsNativeAlgorithms
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

"""  -------------------------------- START OF PROGRAM -----------------------------------   """
import tqdm
import os
import shutil
import pickle
from qgis.core import QgsVectorLayer, QgsCoordinateReferenceSystem


ONLY_TONGUE = True
NO_DEBRIS = False
HIGH_RES_RADIATION_GRIDS = True

# TODO DOC in qgis hover toolbox plugin and id is displayed
# TODO DOC in Processing - History in qgis all the processings with parameters are listed!!
# TODO DOC  # processing.algorithmHelp("qgis:rastercalculator")


class QGisHandler:
    tmp_folder = "tmp"  # probably not even needed ..
    output_folder = "outputData"
    try:
        shutil.rmtree(tmp_folder)
        os.makedirs(tmp_folder)
    except FileNotFoundError:
        os.makedirs(tmp_folder)
    except OSError:
        print("Some file inside tmp folder seems to be open currently!")  # if file is currently in use or open in qgis e.g.

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    """
    TODO ADD
        a = QgsRasterLayer(f'NETCDF:\"/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/KlimaMittel/RR/RR{year}.nc\":RR', 'mylayername')
    QgsProject().instance().addMapLayer(a)
    to add a layer
    add_layer_to_view
    so a netcdf can be used for example
    """

    @classmethod
    def run_resample_radiation_grids(cls):
        for day in tqdm.tqdm(range(1, 366)):
            processing.run("grass7:r.resamp.interp", {
                'input': f'/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/Tägliche Gitter der mittleren direkten Sonneneinstrahlung/pasterze_grid/dir{str(day).zfill(3)}24.grid',
                'method': 1, 'output': f'/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/Tägliche Gitter der mittleren direkten Sonneneinstrahlung/pasterze_grid/dir{str(day).zfill(3)}24_high_res.grid', 'GRASS_REGION_PARAMETER': None,
                'GRASS_REGION_CELLSIZE_PARAMETER': 5, 'GRASS_RASTER_FORMAT_OPT': '', 'GRASS_RASTER_FORMAT_META': ''})

    @classmethod
    def run_creating_height_levels(cls, height_level_step_width, path_to_aws_station_point, path_to_dem, path_to_glacier_shape,
                                   path_to_directory_with_radiations):
        from height_level import HeightLevel

        subfolder_name = f"height_level_step_width_{height_level_step_width}"

        if ONLY_TONGUE:
            subfolder_name += "_tongue"

        if NO_DEBRIS:
            subfolder_name += "_noDebris"

        if HIGH_RES_RADIATION_GRIDS:
            subfolder_name += "_radGridHighRes"

        params_warpreproject = {
            'INPUT': path_to_dem,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        dem_raster = cls.warp_reproject(params_warpreproject)

        params_rasterlayerstatistics = {
            'INPUT': dem_raster,
            "MASK": path_to_glacier_shape,
            # 'NODATA': 0,  # seems important
            'OUTPUT': f"{cls.tmp_folder}/clipped_glacier_raster.tiff"
        }

        dem_raster = cls.clip_raster_by_mask_layer(params_rasterlayerstatistics)

        params_rasterlayerstatistics = {
            'INPUT': dem_raster,
            'BAND': 1,
        }

        statistics = cls.raster_layer_statistics(params_rasterlayerstatistics)

        height_level_objects = HeightLevel.get_beautiful_height_levels_by_step(height_level_step_width, statistics["MIN"],
                                                                               statistics["MAX"])
        height_level_objects.pop(-1)
        try:
            shutil.rmtree(f"{cls.output_folder}/{subfolder_name}")
            os.makedirs(f"{cls.output_folder}/{subfolder_name}")
        except FileNotFoundError:
            os.makedirs(f"{cls.output_folder}/{subfolder_name}")
        except OSError:
            exit(
                "Some file inside tmp folder seems to be open currently!")  # if file is currently in use or open in qgis e.g.

        total_glacier_area = 0
        last_radiation_for_height_level_as_backup = None
        for height_level in height_level_objects:
            height_level: HeightLevel

            params_rastercalculator = {
                'LAYERS': [dem_raster],
                "EXPRESSION": f'1/("clipped_glacier_raster@1">{height_level.lower_border} and "clipped_glacier_raster@1"<{height_level.upper_border})',
                "OUTPUT": f"{cls.tmp_folder}/height_level__{int(height_level.lower_border)}-{int(height_level.upper_border)}.tiff",
            }

            raster_layer = cls.raster_calculator(params_rastercalculator)

            params_polygonize = {
                'INPUT': raster_layer,
                'BAND': 1,
                'OUTPUT': f"{cls.tmp_folder}/height_level_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }
            vector_layer = cls.polygonize(params_polygonize)

            """ Fix geometries first, else this can make problems """

            params_fixgeometries = {
                'INPUT': vector_layer,
                'OUTPUT': f"{cls.output_folder}/{subfolder_name}/height_level_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }

            vector_layer = cls.fix_geometries(params_fixgeometries)

            """ We have the shape now, lets clip raster again with it and get mean height (it is faster that way)"""

            params_rasterclipbyheightlevel = {
                'INPUT': dem_raster,
                "MASK": vector_layer,
                'OUTPUT': f"TEMPORARY_OUTPUT"
            }
            raster_dem_clip_with_height_level = cls.clip_raster_by_mask_layer(params_rasterclipbyheightlevel)
            params_rasterlayerstatistics = {
                'INPUT': raster_dem_clip_with_height_level,
                'BAND': 1,
            }
            stats_height = cls.raster_layer_statistics(params_rasterlayerstatistics)

            # params_rasterclipwinterbalancebyheightlevel = {
            #     'INPUT': path_to_winter_balance,
            #     "MASK": vector_layer,
            #     # 'NODATA': 0,  # seems important
            #     'OUTPUT': f"TEMPORARY_OUTPUT"
            # }
            # raster_winterbalance_clip_with_height_level = cls.clip_raster_by_mask_layer(params_rasterclipwinterbalancebyheightlevel)
            # params_rasterlayerstatistics = {
            #     'INPUT': raster_winterbalance_clip_with_height_level,
            #     'BAND': 1,
            # }
            # stats_winter_balance_mean = cls.raster_layer_statistics(params_rasterlayerstatistics)

            height_level.mean_height = stats_height["MEAN"]
            # height_level.mean_winter_balance = stats_winter_balance_mean["MEAN"]
            height_level.shape_layer_path = vector_layer

            # TODO DELETE FROM HERE
            params_fieldcalculator = {
                'INPUT': vector_layer,
                "FIELD_NAME": "area",
                "FIELD_TYPE": 0,  # for float
                "FIELD_LENGTH": 10,
                "FIELD_PRECISION": 3,
                "NEW_FIELD": True,
                "FORMULA": "area($geometry)",
                'OUTPUT': f"{cls.tmp_folder}/height_level_with_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }

            vector_layer = cls.field_calculator(params_fieldcalculator)
            vector_layer = QgsVectorLayer(vector_layer, "", "ogr")

            height_level.area = 0
            for feature in vector_layer.getFeatures():
                height_level.area += feature.attributes()[1]  # index 1, cause LN and new attribute AREA

            # TODO TILL HERE IF THIS LINE BELOW IS WORKING AS WELL
            height_level.area = cls.get_area_of_shapes(vector_layer)

            print(
                f"Area in height level {int(height_level.lower_border)}-{int(height_level.upper_border)}: {height_level.area}")
            total_glacier_area += height_level.area

        print("Total glacier area", total_glacier_area)

        """ Reading of the radiation files """

        point_station = QgsVectorLayer(path_to_aws_station_point, "", "ogr")

        radiations_at_station = dict()

        for day in tqdm.tqdm(range(1, 366)):
            if HIGH_RES_RADIATION_GRIDS:
                path_to_daily_grid = path_to_directory_with_radiations + f"/dir{str(day).zfill(3)}24_high_res.grid"
            else:
                path_to_daily_grid = path_to_directory_with_radiations + f"/dir{str(day).zfill(3)}24.grid"

            """ Assign CRS to raster dem layer """
            params_warpreproject = {
                'INPUT': path_to_daily_grid,
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

            projected_radiation_grid = cls.warp_reproject(params_warpreproject)

            params_rastersampling = {
                'INPUT': point_station,
                'RASTERCOPY': projected_radiation_grid,
                'COLUMN_PREFIX': 'rvalue',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

            point_station_radiation = cls.raster_sampling(params_rastersampling)

            radiations_at_station[day] = list(point_station_radiation.getFeatures())[0].attributes()[1]

            """ Now get mean radiation for every high level """
            for height_level in height_level_objects:
                params_rasterlayerstatistics = {
                    'INPUT': projected_radiation_grid,
                    "MASK": height_level.shape_layer_path,
                    # 'NODATA': 0,  # seems important
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }

                radiation_height_lvl_clip = cls.clip_raster_by_mask_layer(params_rasterlayerstatistics)


                params_rasterlayerstatistics = {
                    'INPUT': radiation_height_lvl_clip,
                    'BAND': 1,
                }

                try:
                    statistics = cls.raster_layer_statistics(params_rasterlayerstatistics)
                    height_level.mean_radiation[day] = statistics["MEAN"]
                except:  # QgsProcessingException
                    exit(f"Could not compute mean radiation for {height_level} maybe area is just too small or "
                         f"resolution of grid file too coarse!")

        with open(f"{cls.output_folder}/pickle_radiations_at_station.pkl", 'wb') as f:
            pickle.dump(radiations_at_station, f)

        with open(f"{cls.output_folder}/{subfolder_name}/pickle_height_level_objects.pkl", 'wb') as f:
            pickle.dump(height_level_objects, f)

    @classmethod
    def run_creating_dvol_file(cls, input_files_folder, years):
        out_sub_folder = "/dvol"
        if not os.path.exists(cls.output_folder + out_sub_folder):
            os.makedirs(cls.output_folder + out_sub_folder)

        if not input_files_folder.endswith("/"):
            input_files_folder += "/"

        with open(cls.output_folder + out_sub_folder + "/dvol_pas.dat", "w") as f:
            f.write("year date area max-elev min-elev dvol(mio.m3) dhmean(m)\n")

            last_dhmean = 0
            last_volume = 0

            for i in range(len(years)):
                print("Looking at year", years[i])
                params_clip = {
                    'INPUT': input_files_folder + f"dem_{years[i]}.asc",
                    "MASK": input_files_folder + f"pasterze_{years[i]}.shp",
                    'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                    'NODATA': 0,  # seems important
                    'OUTPUT': cls.tmp_folder + f"/clip_dem_{years[i]}_by_shape_{years[i]}.tiff"
                }
                clip_current_dem_by_current_shape = cls.clip_raster_by_mask_layer(params_clip)

                """ get Area """
                # Could be extracted like this as well, but other method matches the results better (dhmean * area)
                # area = cls.get_area_of_shapes(input_files_folder + f"pasterze_{years[i]}.shp")

                params_rasterlayerstatistics = {
                    'INPUT': clip_current_dem_by_current_shape,
                    'BAND': 1,
                    'LEVEL': 0,
                    'METHOD': 2,
                }
                area = cls.rastersurfacevolume(params_rasterlayerstatistics)["AREA"]

                params_rasterlayerstatistics = {
                    'INPUT': clip_current_dem_by_current_shape,
                    'BAND': 1,
                }
                current_dem_stats = cls.raster_layer_statistics(params_rasterlayerstatistics)

                if i < len(years)-1:
                    params_clip = {
                        'INPUT': input_files_folder + f"dem_{years[i+1]}.asc",
                        "MASK": input_files_folder + f"pasterze_{years[i]}.shp",
                        'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                        'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                        'NODATA': 0,  # seems important
                        'OUTPUT': cls.tmp_folder + f"/clip_dem_{years[i+1]}_by_shape_{years[i]}.tiff"
                    }
                    clip_next_dem_by_current_shape = cls.clip_raster_by_mask_layer(params_clip)

                    params_rastercalculator = {
                        'LAYERS': [clip_current_dem_by_current_shape, clip_next_dem_by_current_shape],
                        "EXPRESSION": f'"clip_dem_{years[i+1]}_by_shape_{years[i]}@1"-"clip_dem_{years[i]}_by_shape_{years[i]}@1"',
                        "OUTPUT": cls.output_folder + out_sub_folder + f'/dem_diff_{years[i+1]}_{years[i]}.tiff',
                    }
                    dem_diff = cls.raster_calculator(params_rastercalculator)

                    params_rasterlayerstatistics = {
                        'INPUT': dem_diff,
                        'BAND': 1,
                    }
                    dem_diff_stats = cls.raster_layer_statistics(params_rasterlayerstatistics)

                    params_rasterlayerstatistics = {
                        'INPUT': dem_diff,
                        'BAND': 1,
                        'LEVEL': 0,
                        'METHOD': 2,
                    }
                    volume = cls.rastersurfacevolume(params_rasterlayerstatistics)["VOLUME"]

                f.write(f"{years[i]}  {years[i]}0000  {round(area/1000000, 6)}   {round(current_dem_stats['MAX'], 1)}  "
                        f"{round(current_dem_stats['MIN'], 1)}  {round(last_volume/1000000, 4)}  {last_dhmean}\n")

                print(f"{years[i]}  {years[i]}0000  {round(area/1000000, 6)}   {round(current_dem_stats['MAX'], 1)}  "
                        f"{round(current_dem_stats['MIN'], 1)}  {round(last_volume/1000000, 4)}  {last_dhmean}")

                if i < len(years):
                    last_dhmean = round(dem_diff_stats['MEAN'], 3)
                    last_volume = volume

    @classmethod
    def get_area_of_shapes(cls, path_of_shapefile):
        params_fieldcalculator = {
            'INPUT': path_of_shapefile,
            "FIELD_NAME": "area",
            "FIELD_TYPE": 0,  # for float
            "FIELD_LENGTH": 10,
            "FIELD_PRECISION": 3,
            "NEW_FIELD": True,
            "FORMULA": "area($geometry)",
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        vector_layer = cls.field_calculator(params_fieldcalculator)
        area = 0
        for feature in vector_layer.getFeatures():
            area += feature.attributes()[feature.fieldNameIndex("AREA")]
        return area

    @staticmethod
    def rastersurfacevolume(config_dict):
        # Can be used to extract raster area
        # 'AREA', 'PIXEL_COUNT', 'VOLUME'
        return processing.run("native:rastersurfacevolume", config_dict)

    @staticmethod
    def warp_reproject(config_dict):
        """ Assign CRS to raster dem layer """
        return processing.run("gdal:warpreproject", config_dict)["OUTPUT"]

    @staticmethod
    def clip_raster_by_mask_layer(config_dict):
        """ Clip DEM to glacier shape """
        return processing.run("gdal:cliprasterbymasklayer", config_dict)["OUTPUT"]

    @staticmethod
    def raster_layer_statistics(config_dict):
        # {'MAX', 'MEAN', 'MIN', 'RANGE', 'STD_DEV', 'SUM', 'SUM_OF_SQUARES'}
        return processing.run("qgis:rasterlayerstatistics", config_dict)

    @staticmethod
    def raster_calculator(config_dict):
        if not config_dict["OUTPUT"].endswith(".tiff"):
            exit("Output of raster_calculator needs to be .tiff file")
        return processing.run("qgis:rastercalculator", config_dict)["OUTPUT"]

    @staticmethod
    def polygonize(config_dict):
        return processing.run("gdal:polygonize", config_dict)["OUTPUT"]

    @staticmethod
    def fix_geometries(config_dict):
        return processing.run("native:fixgeometries", config_dict)["OUTPUT"]

    @staticmethod
    def field_calculator(config_dict):
        return processing.run("qgis:fieldcalculator", config_dict)["OUTPUT"]

    @staticmethod
    def raster_sampling(config_dict):
        return processing.run("qgis:rastersampling", config_dict)["OUTPUT"]


if __name__ == "__main__":
    # QGisHandler().run_resample_radiation_grids()
    # input()
    # path_to_aws_station_point = "inputData/AWS_Station.shp"
    # path_to_dem = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/DEMS/DEM_Pasterze_2012_1m/DGM_1m_BMNM31_Gebiet_3_1.asc"
    # if ONLY_TONGUE and not NO_DEBRIS:
    #     path_to_glacier_shape = "inputData/pas_tongue_2018.shp"
    # elif ONLY_TONGUE and NO_DEBRIS:
    #     path_to_glacier_shape = "inputData/pas_tongue_2018_no_debris18.shp"
    # else:
    #     path_to_glacier_shape = "inputData/pasterze_2018.shp"
    #
    # # path_to_winter_balance = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/massenbilanzen/Winterbilanz_2016/wb_2016.tif"
    # path_to_directory_with_radiations = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/Tägliche Gitter der mittleren direkten Sonneneinstrahlung/pasterze_grid"
    # height_level_step_width = int(input("Enter height level step width: "))
    # QGisHandler.run_creating_height_levels(height_level_step_width, path_to_aws_station_point, path_to_dem, path_to_glacier_shape,
    #                                          path_to_directory_with_radiations)

    # QGisHandler().run_creating_dvol_file(
    #     "/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/auto_dvol_generation/inputData",
    #     (1850, 1969, 1998, 2012))

    # print(QGisHandler().get_area_of_shapes("/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/GitRepo/Software/inputData/pasterze_2018.shp"))
    print(QGisHandler().get_area_of_shapes("/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/GitRepo/Software/inputData/pas_tongue_2018.shp"))
    #
    # params_rasterlayerstatistics = {
    #     'INPUT': "/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/GitRepo/Software/inputData/DEL_Ras_shape_tongue.tif",
    #     'BAND': 1,
    #     'LEVEL': 0,
    #     'METHOD': 2,
    # }
    # print(QGisHandler().rastersurfacevolume(params_rasterlayerstatistics)["AREA"])
