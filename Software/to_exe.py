import os
from shutil import move, rmtree, copyfile
from distutils.dir_util import copy_tree
import sys

PATH_TO_PYTHON_SCRIPTS = sys.executable.split("python")[0] + "Scripts\\"
PATH_TO_PYTHON_MODULES = "..\\Libraries\\Python\\HostInterface\\"
ONE_FILE_ONLY = False
EXE_NAME = "Controlpanel-new-exe"
PROGRAM_NAME = "GUI_Windows"
ASADMIN = 'asadmin'

MAIN_CONTROLPANEL_FILE = os.path.dirname(os.path.realpath(__file__)) + "\\main.py"
ROOT_DIRECTORY = os.path.abspath(os.path.join(".", os.pardir))
APPLICATION_NAME = "Volterio_Controlpanel"
FINAL_SAVE_DIRECTORY = os.path.abspath(os.path.join(".", os.pardir)) + "\\" + APPLICATION_NAME + "\\files"


def copy_folder_to(src, dest):
    if not os.path.isdir(dest):
        # TODO delete if is as well
        copy_tree(src, dest)


def copy_file_to(src, dest):
    directories_to_file = "\\".join(dest.split("\\")[:-1])

    if not os.path.exists(directories_to_file):
        os.makedirs(directories_to_file)

    copyfile(src, dest)


def create_exe():
    """
    This function creates a folder Volterio_Controlpanel in root folder containing the executable controlpanel file
    The resources folder and the config files are copied automatically to that folder as well.
    A install.exe is also copied in that folder so that the program can be copied perfectly to the users machine
    Important also is -p PATH_TO_PYTHON_MODULES so that host.py gets recognized
    """

    if os.name != 'posix':
        # delete old Controlpanel-new-exe folder in root directory if something went wrong and it wasnt moved to new dir
        if os.path.isdir(ROOT_DIRECTORY + "\\" + EXE_NAME):
            rmtree(ROOT_DIRECTORY + "\\" + EXE_NAME)

        try:
            mode = " -F" if ONE_FILE_ONLY else " -D"

            # "clean" for fresh reinstall without cache
            os.system(
                'pushd ' + PATH_TO_PYTHON_SCRIPTS + ' && pyinstaller -p ' + PATH_TO_PYTHON_MODULES + ' --distpath '
                + ROOT_DIRECTORY + '  '
                + MAIN_CONTROLPANEL_FILE + mode + " -n " + EXE_NAME + " --clean")
        except:
            print('ERROR: something went wrong, creation not successfull')
            exit()

        # create application folder (Volterio_Controlpanel)
        if not os.path.isdir(ROOT_DIRECTORY + "\\" + APPLICATION_NAME):
            os.mkdir(ROOT_DIRECTORY + "\\" + APPLICATION_NAME)
        else:
            rmtree(ROOT_DIRECTORY + "\\" + APPLICATION_NAME)
            os.mkdir(ROOT_DIRECTORY + "\\" + APPLICATION_NAME)

        # ROOT_DIRECTORY is just "..\\", but if it should get changed any time soon, its easier to redefine root dir
        # new folders have to be added here, otherwise there is gonna be an import error
        copy_folder_to(src="configs", dest=ROOT_DIRECTORY + "\\" + EXE_NAME + "\\configs")
        copy_folder_to(src="firmware_updater", dest=ROOT_DIRECTORY + "\\" + EXE_NAME + "\\firmware_updater")
        copy_folder_to(src="resources", dest=ROOT_DIRECTORY + "\\" + EXE_NAME + "\\resources")

        # Finally move whole exe directory to new distination
        move(ROOT_DIRECTORY + "\\" + EXE_NAME, FINAL_SAVE_DIRECTORY + "\\" + EXE_NAME)

        # Copy other files to application folder as well (Volterio_Controlpanel)
        copy_file_to(src=ROOT_DIRECTORY + "\\Master-Board\\Software\\Robot\\Inc\\config.h",
                     dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME
                          + "\\files\\Master-Board\\Software\\Robot\\Inc\\config.h")
        copy_folder_to(src=ROOT_DIRECTORY + "\\Libraries\\ErrorsAndEvents",
                       dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME + "\\files\\Libraries\\ErrorsAndEvents")
        copy_folder_to(src=ROOT_DIRECTORY + "\\Libraries\\Motors",
                       dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME + "\\files\\Libraries\\Motors")
        copy_folder_to(src=ROOT_DIRECTORY + "\\Libraries\\Python",
                       dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME + "\\files\\Libraries\\Python")

        # copy the installation files
        copy_file_to(src="installation/install.exe",
                     dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME + "\\install.exe")
        copy_file_to(src="installation/files/config_installer.ini",
                     dest=ROOT_DIRECTORY + "\\" + APPLICATION_NAME + "\\files\\config_installer.ini")

        print('INFO: Creation might have been successful')
        exit()
    else:
        print("Creation of exe is possible only on windows")
