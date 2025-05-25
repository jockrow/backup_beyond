####################################
# Author: Richard Martínez
# Created Date: 2017/08/24
####################################
# TODO: poner el nombre del branch si existe
    # TODO: set the variable branch if the current FROM_BACKUP has a branch else put empty
# TODO: parametrizar una mascara
# TODO: abrir bcompare conmparando el backup con el original

from datetime import datetime
import os
import re
import shutil
import zipfile
import subprocess


def get_git_branch(repo_path):
    try:
        branch_name = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )

        parts = re.split(r'[/\.]', branch_name)
        branch_name = parts[-1]

    except subprocess.CalledProcessError:
        branch_name = ""
    return branch_name


# branch = get_git_branch("/Users/richard/devs/Projects/backCountPages")
# TODO: Validate when the source doesn't exists
branch = get_git_branch("D:/devs/Booster/InfoCorp/TimeControl/InfoWeb3.Api")
# branch = get_git_branch("D:/devs/python/backup_beyond")


print(f"branch: {branch}")


try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

config = ConfigParser()
config.read("BACKUP_BEYOND.ini")

BCOMPARE_BIN = config.get("general", "BCOMPARE_BIN")
FROM_BACKUP = config.get("backup", "FROM_BACKUP")
FILTER = config.get("backup", "FILTER")
displayLog = config.get("backup", "displayLog")
compress = config.get("backup", "compress")

FORMAT_DATE = str(datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
CURRENT_PATH = str(os.getcwd())
BACKUP_NAME = re.sub(r".*[\\/]", "", CURRENT_PATH)
BACKUP_COMPRESS = BACKUP_NAME + " " + FORMAT_DATE

print("Apply Filter and Creating Backup: " + BACKUP_COMPRESS + "...")
if displayLog:
    displayLog = 'log normal "' + CURRENT_PATH + os.sep + 'backup.log" \n'
else:
    displayLog = ""
bCompareFile = (
    displayLog + ""
    "filter " + FILTER + " \n"
    "load create:right"
    + ' "'
    + FROM_BACKUP
    + '" "'
    + CURRENT_PATH
    + os.sep
    + BACKUP_COMPRESS
    + '" \n'
    "sync update:left->right"
)
file = open("bCompare", "w")
file.write(bCompareFile)
file.close()
os.system('"' + BCOMPARE_BIN + '" @bCompare /silent')

if compress:
    print("Compressing Backup...")
    parentDir, dirToZip = os.path.split(BACKUP_COMPRESS)

    def trimPath(path):
        archivePath = path.replace(parentDir, "", 1)
        if parentDir:
            archivePath = archivePath.replace(os.path.sep, "", 1)
        archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
        return archivePath

    outFile = zipfile.ZipFile(
        BACKUP_COMPRESS + ".zip", "w", compression=zipfile.ZIP_DEFLATED
    )
    for archiveDirPath, dirNames, fileNames in os.walk(BACKUP_COMPRESS):
        for fileName in fileNames:
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))
        if not fileNames and not dirNames:
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
            outFile.writestr(zipInfo, "")
    outFile.close()
    shutil.rmtree(BACKUP_COMPRESS)

os.remove("bCompare")

