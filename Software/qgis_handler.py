import sys
from qgis.core import QgsApplication

QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

sys.path.append("/usr/share/qgis/python/plugins")
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

from height_level import HeightLevel


# TODO DOC in qgis hover toolbox plugin and id is displayed
# TODO DOC in Processing - History in qgis all the processings with parameters are listed!!
# TODO DOC  # processing.algorithmHelp("qgis:rastercalculator")

class QGisHandler:
    def __init__(self):
        self.tmp_folder = "tmp"  # probably not even needed ..
        self.output_folder = "outputData"
        try:
            shutil.rmtree(self.tmp_folder)
            os.makedirs(self.tmp_folder)
        except FileNotFoundError:
            os.makedirs(self.tmp_folder)
        except OSError:
            print("Some file inside tmp folder seems to be open currently!")  # if file is currently in use or open in qgis e.g.

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def run(self, height_level_step_width, path_to_aws_station_point, path_to_dem, path_to_glacier_shape, path_to_winter_balance,
            path_to_directory_with_radiations):
        subfolder_name = f"height_level_step_width_{height_level_step_width}"

        params_warpreproject = {
            'INPUT': path_to_dem,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        dem_raster = self.warp_reproject(params_warpreproject)

        params_rasterlayerstatistics = {
            'INPUT': dem_raster,
            "MASK": path_to_glacier_shape,
            'OUTPUT': f"{self.tmp_folder}/clipped_glacier_raster.tiff"
        }

        dem_raster = self.clip_raster_by_mask_layer(params_rasterlayerstatistics)

        params_rasterlayerstatistics = {
            'INPUT': dem_raster,
            'BAND': 1,
        }

        statistics = self.raster_layer_statistics(params_rasterlayerstatistics)

        height_level_objects = HeightLevel.get_beautiful_height_levels_by_step(height_level_step_width, statistics["MIN"],
                                                                               statistics["MAX"])

        try:
            shutil.rmtree(f"{self.output_folder}/{subfolder_name}")
            os.makedirs(f"{self.output_folder}/{subfolder_name}")
        except FileNotFoundError:
            os.makedirs(f"{self.output_folder}/{subfolder_name}")
        except OSError:
            exit(
                "Some file inside tmp folder seems to be open currently!")  # if file is currently in use or open in qgis e.g.

        total_glacier_area = 0
        for height_level in height_level_objects:
            height_level: HeightLevel

            params_rastercalculator = {
                'LAYERS': [dem_raster],
                "EXPRESSION": f'1/("clipped_glacier_raster@1">{height_level.lower_border} and "clipped_glacier_raster@1"<{height_level.upper_border})',
                "OUTPUT": f"{self.tmp_folder}/height_level__{int(height_level.lower_border)}-{int(height_level.upper_border)}.tiff",
            }

            raster_layer = self.raster_calculator(params_rastercalculator)

            params_polygonize = {
                'INPUT': raster_layer,
                'BAND': 1,
                'OUTPUT': f"{self.tmp_folder}/height_level_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }
            vector_layer = self.polygonize(params_polygonize)

            """ Fix geometries first, else this can make problems """

            params_fixgeometries = {
                'INPUT': vector_layer,
                'OUTPUT': f"{self.output_folder}/{subfolder_name}/height_level_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }

            vector_layer = self.fix_geometries(params_fixgeometries)

            """ We have the shape now, lets clip raster again with it and get mean height (it is faster that way)"""

            params_rasterclipbyheightlevel = {
                'INPUT': dem_raster,
                "MASK": vector_layer,
                'OUTPUT': f"TEMPORARY_OUTPUT"
            }
            raster_dem_clip_with_height_level = self.clip_raster_by_mask_layer(params_rasterclipbyheightlevel)
            params_rasterlayerstatistics = {
                'INPUT': raster_dem_clip_with_height_level,
                'BAND': 1,
            }
            stats_height = self.raster_layer_statistics(params_rasterlayerstatistics)

            params_rasterclipwinterbalancebyheightlevel = {
                'INPUT': path_to_winter_balance,
                "MASK": vector_layer,
                'OUTPUT': f"TEMPORARY_OUTPUT"
            }
            raster_winterbalance_clip_with_height_level = self.clip_raster_by_mask_layer(params_rasterclipwinterbalancebyheightlevel)
            params_rasterlayerstatistics = {
                'INPUT': raster_winterbalance_clip_with_height_level,
                'BAND': 1,
            }
            stats_winter_balance_mean = self.raster_layer_statistics(params_rasterlayerstatistics)


            height_level.mean_height = stats_height["MEAN"]
            height_level.mean_winter_balance = stats_winter_balance_mean["MEAN"]
            height_level.shape_layer_path = vector_layer

            params_fieldcalculator = {
                'INPUT': vector_layer,
                "FIELD_NAME": "area",
                "FIELD_TYPE": 0,  # for float
                "FIELD_LENGTH": 10,
                "FIELD_PRECISION": 3,
                "NEW_FIELD": True,
                "FORMULA": "area($geometry)",
                'OUTPUT': f"{self.tmp_folder}/height_level_with_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
            }

            vector_layer = self.field_calculator(params_fieldcalculator)
            vector_layer = QgsVectorLayer(vector_layer, "", "ogr")

            height_level.area = 0
            for feature in vector_layer.getFeatures():
                height_level.area += feature.attributes()[1]  # index 1, cause LN and new attribute AREA

            print(
                f"Area in height level {int(height_level.lower_border)}-{int(height_level.upper_border)}: {height_level.area}")
            total_glacier_area += height_level.area

        print("Total glacier area", total_glacier_area)

        """ Reading of the radiation files """

        point_station = QgsVectorLayer(path_to_aws_station_point, "", "ogr")

        radiations_at_station = dict()

        for day in tqdm.tqdm(range(1, 366)):
            path_to_daily_grid = path_to_directory_with_radiations + f"/dir{str(day).zfill(3)}24.grid"

            """ Assign CRS to raster dem layer """
            params_warpreproject = {
                'INPUT': path_to_daily_grid,
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

            projected_radiation_grid = self.warp_reproject(params_warpreproject)

            params_rastersampling = {
                'INPUT': point_station,
                'RASTERCOPY': projected_radiation_grid,
                'COLUMN_PREFIX': 'rvalue',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

            point_station_radiation = self.raster_sampling(params_rastersampling)

            radiations_at_station[day] = list(point_station_radiation.getFeatures())[0].attributes()[1]

            """ Now get mean radiation for every high level """
            for height_level in height_level_objects:
                params_rasterlayerstatistics = {
                    'INPUT': projected_radiation_grid,
                    "MASK": height_level.shape_layer_path,
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }

                radiation_height_lvl_clip = self.clip_raster_by_mask_layer(params_rasterlayerstatistics)

                params_rasterlayerstatistics = {
                    'INPUT': radiation_height_lvl_clip,
                    'BAND': 1,
                }

                statistics = self.raster_layer_statistics(params_rasterlayerstatistics)
                height_level.mean_radiation[day] = statistics["MEAN"]

        with open(f"{self.output_folder}/{subfolder_name}/pickle_radiations_at_station.pkl", 'wb') as f:
            pickle.dump(radiations_at_station, f)

        with open(f"{self.output_folder}/{subfolder_name}/pickle_height_level_objects.pkl", 'wb') as f:
            pickle.dump(height_level_objects, f)

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


path_to_aws_station_point = "inputData/AWS_Station.shp"
path_to_dem = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/DEMS/DEM_Pasterze_2012_1m/DGM_1m_BMNM31_Gebiet_3_1.asc"
path_to_glacier_shape = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/gletscherumrisse/pasterze_2018.shp"
path_to_winter_balance = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/massenbilanzen/Winterbilanz_2016/wb_2016.tif"
path_to_directory_with_radiations = "../../Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/Tägliche Gitter der mittleren direkten Sonneneinstrahlung/pasterze_grid"

height_level_step_width = int(input("Enter height level step width: "))

QGisHandler().run(height_level_step_width, path_to_aws_station_point, path_to_dem, path_to_glacier_shape,
                  path_to_winter_balance, path_to_directory_with_radiations)
