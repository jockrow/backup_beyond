####################################
# Author: Richard Martínez
# Created Date: 2017/08/24
####################################

import os
import re
import shutil
import subprocess
from datetime import datetime
import time

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # Python 2 fallback


def get_git_branch(repo_path):
    """Return the last part of the git branch_name name if it exists, else empty string."""
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

def main():
    config = ConfigParser(interpolation=None)
    config.read("BACKUP_BEYOND.ini")

    BCOMPARE_BIN = config.get("general", "BCOMPARE_BIN")
    FROM_BACKUP = config.get("backup", "FROM_BACKUP")
    FILTER = config.get("backup", "FILTER")
    FORMAT_MASK = config.get("backup", "FORMAT_MASK")
    # debugpy.wait_for_client()
    displayLog = config.get("backup", "displayLog")
    compress = config.get("backup", "compress")

    branch_name = get_git_branch(FROM_BACKUP)
    branch_name = branch_name + " " if branch_name else ""
    # if branch_name != "" branch_name + " "

    FORMAT_DATE = datetime.now().strftime(FORMAT_MASK)
    CURRENT_PATH = os.getcwd()
    BACKUP_NAME = re.sub(r".*[\\/]", "", CURRENT_PATH)
    BACKUP_COMPRESS = branch_name + BACKUP_NAME + " " + FORMAT_DATE

    print("Apply Filter and Creating Backup: " + BACKUP_COMPRESS + "...")
    start = time.time()

    # Build Beyond Compare command script
    # TODO:Mejorar el log para los tiempos reales junto con el comprimido
    if displayLog == "True":
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

    if compress == "True":
        print("Compressing Backup...")
        shutil.make_archive(BACKUP_COMPRESS, "zip", root_dir="./" + BACKUP_COMPRESS)
        shutil.rmtree(BACKUP_COMPRESS)

    end = time.time()
    print(f"Process completed took: {end - start:.2f} seconds")

    os.remove("bCompare")

if __name__ == "__main__":
    main()
