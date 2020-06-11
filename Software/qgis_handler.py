import sys
sys.path.append("/usr/share/qgis/python/plugins")
from qgis.core import  QgsApplication, QgsCoordinateReferenceSystem
from PyQt5.QtCore import QFileInfo
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsPoint

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
import numpy as np
import os
import shutil
import pickle

from height_level import HeightLevel


# TODO DOC in qgis hover toolbox plugin and id is displayed
# TODO DOC in Processing - History in qgis all the processings with parameters are listed!!


tmp_folder = "tmp"
output_folder = "outputData"
try:
    shutil.rmtree(tmp_folder)
    os.makedirs(tmp_folder)
except OSError:
    pass  # if file is currently in use or open in qgis e.g.

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

dem_name = "/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/DEMS/DEM_Pasterze_1998_5m/gg98bl05_ed.asc"
fileInfo = QFileInfo(dem_name)
baseName = fileInfo.baseName()
rlayer = QgsRasterLayer(dem_name, baseName)

glacier_shape = QgsVectorLayer("/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/gletscherumrisse/pasterze_2018.shp", "", "ogr")

print(rlayer.height())

if rlayer.bandCount() != 1:
    exit("Input raster layer has more than one band, what to do with the statistics now?")

""" Assign CRS to raster dem layer """

params_warpreproject = {
    'INPUT':'/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/DEMS/DEM_Pasterze_1998_5m/gg98bl05_ed.asc',
    'SOURCE_CRS':None,
    'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:31258'),
    'RESAMPLING':0,
    'NODATA':None,
    'TARGET_RESOLUTION':None,
    'OPTIONS':'',
    'DATA_TYPE':0,
    'TARGET_EXTENT':None,
    'TARGET_EXTENT_CRS':None,
    'MULTITHREADING':False,
    'EXTRA':'',
    'OUTPUT':'TEMPORARY_OUTPUT'
}

dem_raster = processing.run("gdal:warpreproject", params_warpreproject)

""" Clip DEM to glacier shape """
# processing.algorithmHelp("gdal:cliprasterbymasklayer")

params_rasterlayerstatistics = {
    'INPUT': dem_raster["OUTPUT"],
    "MASK": glacier_shape,#"/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/gletscherumrisse/pasterze_2018.shp",
    'SOURCE_CRS':None,
    'TARGET_CRS':None,
    'NODATA':None,
    'ALPHA_BAND':False,
    'CROP_TO_CUTLINE':True,
    'KEEP_RESOLUTION':False,
    'SET_RESOLUTION':False,
    'X_RESOLUTION':None,
    'Y_RESOLUTION':None,
    'MULTITHREADING':False,
    'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
    'DATA_TYPE':0,
    'EXTRA':'',
    'OUTPUT': f"{tmp_folder}/clipped_glacier_raster.tiff"
    # 'OUTPUT':'TEMPORARY_OUTPUT'
}  # temp output


#
# params_rasterlayerstatistics = {
#     'INPUT': fileName,
#     "MASK": glacier_shape,#"/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/gletscherumrisse/pasterze_2018.shp",
#     # 'BAND': 1,
#     # "ALPHA_BAND": False,
#     # "SOURCE_CRS": 31258,
#     # "TARGET_CRS": 31258,
#     # "CROP_TO_CUTLINE": True,
#     # "KEEP_RESOLUTION": False,  # TODO but probably True?
#     # "SET_RESOLUTION": False,
#     # "MULTITHREADING": False,
#     # 'DATA_TYPE': 7,
#     #     "NODATA": -1,
#     # "X_RESOLUTION": 5,
#     # "Y_RESOLUTION": 5,
#     'OUTPUT': f"{tmp_folder}/clipped_glacier_raster.tiff"  # has to be .tiff
# }

dem_raster = processing.run("gdal:cliprasterbymasklayer", params_rasterlayerstatistics)  # sadly not working


params_rasterlayerstatistics = {
    'INPUT': dem_raster["OUTPUT"],
    'BAND': 1,
}

# {'MAX', 'MEAN', 'MIN', 'RANGE', 'STD_DEV', 'SUM', 'SUM_OF_SQUARES'}
statistics = processing.run("qgis:rasterlayerstatistics", params_rasterlayerstatistics)

amount_of_levels = 20
height_levels = np.linspace(statistics["MIN"], statistics["MAX"], amount_of_levels + 1)
height_level_objects = [HeightLevel(height_levels[i], height_levels[i + 1]) for i in range(len(height_levels) - 1)]




# processing.algorithmHelp("gdal:polygonize")
total_glacier_area = 0
for height_level in height_level_objects:
    height_level: HeightLevel
    
    just_shape = True

    params_rastercalculator = {
        'LAYERS': [dem_raster["OUTPUT"]],
        "EXPRESSION": f'1/("clipped_glacier_raster@1">0{height_level.lower_border} and "clipped_glacier_raster@1"<{height_level.upper_border})',
        "OUTPUT": f"{tmp_folder}/height_level__{int(height_level.lower_border)}-{int(height_level.upper_border)}.tiff",  # has to be tiff
    }
    # processing.algorithmHelp("qgis:rastercalculator")
    raster_layer = processing.run("qgis:rastercalculator", params_rastercalculator)

    params_polygonize = {
        'INPUT': raster_layer["OUTPUT"],
        'BAND': 1,
        'OUTPUT': f"{tmp_folder}/height_level_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
    }
    vector_layer = processing.run("gdal:polygonize", params_polygonize)

    # processing.algorithmHelp("qgis:fieldcalculator")

    """ Fix geomtries first, else this can make problems """

    params_fixgeometries = {
        'INPUT': vector_layer["OUTPUT"],
        'OUTPUT': f"{output_folder}/height_level_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
    }

    vector_layer = processing.run("native:fixgeometries", params_fixgeometries)

    height_level.shape_layer = vector_layer["OUTPUT"]

    params_rastercalculator = {
        'INPUT': vector_layer["OUTPUT"],
        "FIELD_NAME": "area",
        "FIELD_TYPE": 0,  # for float
        "FIELD_LENGTH": 10,
        "FIELD_PRECISION": 3,
        "NEW_FIELD": True,
        "FORMULA": "area($geometry)",
        'OUTPUT': f"{tmp_folder}/height_level_with_area_{int(height_level.lower_border)}-{int(height_level.upper_border)}.shp"
    }

    vector_layer = processing.run("qgis:fieldcalculator", params_rastercalculator)

    vector_layer = QgsVectorLayer(vector_layer["OUTPUT"], "", "ogr")

    height_level.area = 0
    for feature in vector_layer.getFeatures():
        height_level.area += feature.attributes()[1]  # index 1, cause LN and new attribute AREA
        pass  # do something with feature

    print(f"Area in height level {int(height_level.lower_border)}-{int(height_level.upper_border)}: {height_level.area}")
    total_glacier_area += height_level.area

print("Total glacier area", total_glacier_area)

""" Reading of the radiation files """
directory_with_radiations = "/mnt/hdd/Data/Geodaesie/6_semester/Project_Pasterze/Data_for_Germ/Pasterze_Data/2020_Daten_Pasterze/Tägliche Gitter der mittleren direkten Sonneneinstrahlung/pasterze_grid"

point_station = QgsVectorLayer("inputData/AWS_Station.shp", "", "ogr")

radiations_at_station = dict()

for day in tqdm.tqdm(range(1, 366)):  # 366
    path_to_daily_grid = directory_with_radiations + f"/dir{str(day).zfill(3)}24.grid"

    """ Assign CRS to raster dem layer """
    params_warpreproject = {
        'INPUT': path_to_daily_grid,
        'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31258'),
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }

    projected_radiation_grid = processing.run("gdal:warpreproject", params_warpreproject)

    params_rastersampling = {
        'INPUT': point_station,
        'RASTERCOPY': projected_radiation_grid["OUTPUT"],
        'COLUMN_PREFIX': 'rvalue',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }

    point_station_radiation = processing.run("qgis:rastersampling", params_rastersampling)
    radiations_at_station[day] = list(point_station_radiation["OUTPUT"].getFeatures())[0].attributes()[1]

    """ Now get mean radiation for every high level """
    for height_level in height_level_objects:
        params_rasterlayerstatistics = {
            'INPUT': projected_radiation_grid["OUTPUT"],
            "MASK": height_level.shape_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        radiation_height_lvl_clip = processing.run("gdal:cliprasterbymasklayer", params_rasterlayerstatistics)  # sadly not working

        params_rasterlayerstatistics = {
            'INPUT': radiation_height_lvl_clip["OUTPUT"],
            'BAND': 1,
        }

        statistics = processing.run("qgis:rasterlayerstatistics", params_rasterlayerstatistics)
        height_level.mean_radiation[day] = statistics["MEAN"]

with open("pickle_radiations_at_station", 'wb') as f:
    pickle.dump(radiations_at_station, f)

with open("pickle_height_level_objects", 'wb') as f:
    pickle.dump(height_level_objects, f)
