import os
from shutil import move, rmtree, copyfile
from distutils.dir_util import copy_tree
import sys

PATH_TO_PYTHON_SCRIPTS = sys.executable.split("python")[0] + "Scripts\\"
PATH_TO_PYTHON_MODULES = "D:\\Data\\energiebilanzablationsgebietpasterze\\Software\\GUI"  # abs path .. bad but whatever
ONE_FILE_ONLY = False
EXE_NAME = "EXE_Glacier-Energy-Balance"
ASADMIN = 'asadmin'
SHOW_TERMINAL_IN_BACKGROUND = False

MAIN_CONTROLPANEL_FILE = os.path.dirname(os.path.realpath(__file__)) + "\\main.py"
ROOT_DIRECTORY = os.path.abspath(os.path.join(".", os.pardir))


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

        if os.path.isdir(ROOT_DIRECTORY + "\\" + EXE_NAME):
            rmtree(ROOT_DIRECTORY + "\\" + EXE_NAME)

        # delete old Controlpanel-new-exe folder in root directory if something went wrong and it wasnt moved to new dir
        try:
            mode = " -F" if ONE_FILE_ONLY else " -D"
            terminal = " - w" if SHOW_TERMINAL_IN_BACKGROUND else ""

            # "clean" for fresh reinstall without cache  .. and removed -p ' + PATH_TO_PYTHON_MODULES here
            os.system(
                'pushd ' + PATH_TO_PYTHON_SCRIPTS + ' && pyinstaller ' + terminal + '-p ' + PATH_TO_PYTHON_MODULES + ' --distpath '
                + ROOT_DIRECTORY + '  '
                + MAIN_CONTROLPANEL_FILE + mode + " -n " + EXE_NAME + " --clean")
        except:
            print('ERROR: something went wrong, creation not successfull')
            exit()

        copy_file_to(src=ROOT_DIRECTORY + "\\Software\\config.ini",
                     dest=ROOT_DIRECTORY + "\\" + EXE_NAME + "\\config.ini")

        print('INFO: Creation might have been successful')
        exit()
    else:
        print("Creation of exe is possible only on windows")


if __name__ == "__main__":
    create_exe()
