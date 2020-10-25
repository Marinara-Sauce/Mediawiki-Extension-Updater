"""
Title: Automatic Extension Updater
Language: Python 3.8
Filename: extension_updater.py
Description: This program downloads the latest version of all the extensions in a previous mediawiki directory, extracts,
and installs them into a new mediawiki installation. After it's finished, it leaves a text file containing all the
extensions, and any problems
Author: Dan Bliss
"""

import os
from os import path
import platform

import requests
import argparse

# Global Const Variables
version = "1_35"  # Must be formatted as 1_<Version Number>

# Directories
old_extensions_folder = ''  # Leads to the old extensions folder, with all the extensions already downloaded
new_extensions_folder = ''  # Leads to the new extensions folder, where all the updated extensions will be placed

downloadFolder = ""  # Folder to place all downloaded tars in


class DownloadedExtension:
    """
    This class contains information on a downloaded extension. It currently contains the name, and the error code, if any
    The error will be left as None if installed successfully
    Error is an int, and the int partains to the type of error.
    Error 1 - Extension Already in Mediawiki
    Error 2 - Extension could not be found on Mediawiki
    """
    def __init__(self, name, error):
        self.name = name
        self.error = error


# Run a command
def run_command(cmd: str):
    """
    Runs a command on the os. Changes / to \ if running on windows
    :param cmd: The command to run
    :return: None
    """
    if platform.system() == 'Windows':
        cmd = cmd.replace("/", "\\") # Windows uses \ for directories, replace if running on windows

    os.system(cmd)


# Fetches the directory locations, passes them into the global variables above
def prompt_directory_locations():
    """
    Goes unused. Prompts the user for locations of the old and new mediawiki directories, and makes sure they are
    valid directories by making sure the WikiEditor folder exists. Once the folders are confirmed, it sets the global
    variables for each folder to be used in later functions.
    :return: None
    """
    while True:
        global old_extensions_folder
        old_extensions_folder = input("Enter the path to the old extensions folder"
                                      + " (This contains all the old extensions. Ex: mediawiki-1.34.0/extensions): ")

        if path.exists(f"{old_extensions_folder}/WikiEditor"):
            break

        print("This is not a valid ")

    while True:
        global new_extensions_folder
        new_extensions_folder = input("Enter the path to the new extensions folder"
                                + " (This will contain all the updated extensions. Ex: mediawiki-1.35.0/extensions): ")

        if path.exists(f"{new_extensions_folder}/WikiEditor"):
            break

        print("This is not a valid ")


def get_dir_locations_from_args(args):
    """
    Gets the directory location from the system arguments using argparse. Once directories and the version is fetched,
    it makes sure that the directories are valid, and exits the program if they aren't
    :param args: The arguments
    :return: None
    """
    global old_extensions_folder
    global new_extensions_folder

    if not path.exists(f"{args.old}/WikiEditor"):
        print("The path: " + args.old + " is not a valid extension path!")
        exit()

    if not path.exists(f"{args.new}/WikiEditor"):
        print("The path: " + args.new + " is not a valid extension path!")
        exit()

    if "1_" not in args.version:
        print("Invalid version format! (Ex: 1_35)")
        exit()

    old_extensions_folder = args.old
    new_extensions_folder = args.new


# Sets up the new directory for downloading and extracting
def setup_new_directory():
    """
    Sets up the DownloadedTars folder for extensions to download into. Sets the global variable downloadFolder after
    this is finished.
    ;precondition: new_extension_folder is not None
    :return: None
    """
    run_command("mkdir " + new_extensions_folder + "/DownloadedTars")
    global downloadFolder
    downloadFolder = new_extensions_folder + "/DownloadedTars"


def get_old_extension_list():
    """
    Gets a list of all the extensions in the old extension folder.
    ;precondition: old_extensions_folder is not None
    :return: A list of every extension name
    """
    extensions = []
    folders = os.walk(old_extensions_folder)
    for x in os.walk(old_extensions_folder):
        directories = x[1]
        for dir in directories:
            extensions.append(dir)
        break
        # Probably not the best way to go about this, but it works

    return extensions


# Downloads and extracts an specified extension
def download_and_extract_extension(name: str):
    """
    Downloads and extracts an extension. First it makes a HTTP request to the specific URL that the extension is hosted
    at for Mediawiki to generate a snapshot of the extension. It then parses the HTML response for the download link.
    It gets the filename, and uses wget to download the extension. Once that is done, it extracts the tar into the
    downloaded folder, and deletes the tar
    :param name: The name of the extension
    ;precondition: new_extensions_folder, old_extensions_folder, and version is not null
    :return: The error code, if any
    """
    print("Currently Downloading: " + name)
    # Check if the extension is already installed
    if path.exists(new_extensions_folder + "/" + name):
        print("Extension " + name + " is already installed!")
        return 1

    r = requests.get(f"https://www.mediawiki.org/wiki/Special:ExtensionDistributor?extdistname={name}&extdistversion=REL{version}")
    html = r.text  # Gets the HTTP as a string for processing. The URL for download is located here...

    # Check if the page actually exists
    if "No such extension" in html:
        print("The extension " + name + " does not exist!")
        return 2

    download_url = None
    for line in html.splitlines():
        if line.startswith("<dl>"):
            # We have our line with the download link, remove everything we can
            download_url = line.replace('<dl><dd><a rel="nofollow" class="external free" href="', '')
            download_url = download_url.split('">')[0]
            break

    tar_name = download_url.split("/")[5]

    print("Received File: " + tar_name + ". Attempting to download and extract")
    # Download the extension onto the hard drive
    run_command(f"wget -P {downloadFolder} {download_url}")
    # After it's finished downloading, extract it into the extension folder
    run_command(f"tar -xzf {downloadFolder}/{tar_name} -C {new_extensions_folder}")
    # Extension is done installing, and has been extracted. Delete it
    run_command(f"rm {downloadFolder}/{tar_name}")

    return None


def install_all_extensions(extensions):
    """
    Installs all the extensions from a previous version.
    :param extensions: A list of extensions to install
    :return: A list of the installed_extensions class
    """
    installed_extensions = []

    for extension in extensions:
        # Downloads and installs all extensions, logs any errors in the array
        installed_extensions.append(DownloadedExtension(extension, download_and_extract_extension(extension)))

    print("Finished installing all extensions!")
    return installed_extensions


def output_to_text(installed_extensions):
    """
    Outputs the result of an update to a text file
    :param installed_extensions: A list of the installed_extensions class
    :return: None
    """
    print("Logging to Installed_Extensions.txt...")
    doc = open("Installed_Extensions.txt", "a")
    for ex in installed_extensions:
        error = "Success!"

        if ex.error == 2:
            error = "Page does not exist!"
        if ex.error == 1:
            error = "Extension Already installed!"

        doc.write(f"{ex.name} - {error}\n")

    doc.close()


# Main Function
def main(args):
    """
    The main method
    :param args: args
    :return: None
    """
    # Setup args
    parser = argparse.ArgumentParser()
    parser.add_argument("old", help="The directory containing all the old extensions. "
                                    + "These extensions will have the latest version installed into the new directory. "
                                    + "Example: \"mediawiki-1.34.0/extensions\"")

    parser.add_argument("new", help="The directory that all the new extensions will install to. "
                                    + "Example: \"mediawiki-1.35.0/extensions\"")

    parser.add_argument("version", help="The extension version to download. Example of the format is \"1_35\"")

    # Gets the directory locations from the arguments
    get_dir_locations_from_args(parser.parse_args())
    setup_new_directory()  # Sets up the directory to download all the tars into
    # Downloads and installs all the extensions, outputs to text file
    output_to_text(install_all_extensions(get_old_extension_list()))
    run_command(f"rmdir {downloadFolder}")  # Removes the DownloadedTars folder


if __name__ == '__main__':
    main(None)

