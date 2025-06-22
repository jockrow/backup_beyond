####################################
# Author: Richard Martínez
# Created Date: 2017/08/24
####################################
# TODO: poner el nombre del branch si existe
    # TODO: set the variable branch if the current FROM_BACKUP has a branch else put empty
# TODO: parametrizar una mascara
# TODO: abrir bcompare conmparando el backup con el original

import os
import re
import shutil
import zipfile
import subprocess
from datetime import datetime

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # Python 2 fallback


def get_git_branch(repo_path):
    """Return the last part of the git branch name if it exists, else empty string."""
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


def trim_path(path, parent_dir, dir_to_zip):
# TODO: Validate when the source doesn't exists
    archive_path = path.replace(parent_dir, "", 1)
    if parent_dir:
        archive_path = archive_path.replace(os.path.sep, "", 1)
    archive_path = archive_path.replace(dir_to_zip + os.path.sep, "", 1)
    return archive_path


def main():
    # Load config
    config = ConfigParser()
    config.read("BACKUP_BEYOND.ini")

    BCOMPARE_BIN = config.get("general", "BCOMPARE_BIN")
    FROM_BACKUP = config.get("backup", "FROM_BACKUP")
    FILTER = config.get("backup", "FILTER")
    displayLog = config.get("backup", "displayLog")
    compress = config.get("backup", "compress")

    # Get current git branch name from FROM_BACKUP path
    branch = get_git_branch(FROM_BACKUP)
    print(f"branch: {branch}")

    # Prepare backup names and paths
    FORMAT_DATE = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    CURRENT_PATH = os.getcwd()
    BACKUP_NAME = re.sub(r".*[\\/]", "", CURRENT_PATH)
    BACKUP_COMPRESS = BACKUP_NAME + " " + FORMAT_DATE

    print("Apply Filter and Creating Backup: " + BACKUP_COMPRESS + "...")

    # Build Beyond Compare command script
    if displayLog:
        displayLog = f'log normal "{CURRENT_PATH}{os.sep}backup.log" \n'
    else:
        displayLog = ""

    bCompareFile = (
        displayLog
        + f"filter {FILTER} \n"
        + 'load create:right "' + FROM_BACKUP + '" "' + CURRENT_PATH + os.sep + BACKUP_COMPRESS + '" \n'
        + "sync update:left->right"
    )

    with open("bCompare", "w") as file:
        file.write(bCompareFile)

    os.system(f'"{BCOMPARE_BIN}" @bCompare /silent')

    # Compress backup if needed
    if compress:
        print("Compressing Backup...")
        parent_dir, dir_to_zip = os.path.split(BACKUP_COMPRESS)

        outFile = zipfile.ZipFile(
            BACKUP_COMPRESS + ".zip", "w", compression=zipfile.ZIP_DEFLATED
        )
        for archiveDirPath, dirNames, fileNames in os.walk(BACKUP_COMPRESS):
            for fileName in fileNames:
                filePath = os.path.join(archiveDirPath, fileName)
                outFile.write(filePath, trim_path(filePath, parent_dir, dir_to_zip))
            if not fileNames and not dirNames:
                zipInfo = zipfile.ZipInfo(trim_path(archiveDirPath, parent_dir, dir_to_zip) + "/")
                outFile.writestr(zipInfo, "")
        outFile.close()
        shutil.rmtree(BACKUP_COMPRESS)

    os.remove("bCompare")


if __name__ == "__main__":
    main()
