#!/usr/bin/env python3

import os
import configparser
import tarfile
import requests
import shutil
from lib import docopt


def check_config_exists(prefix):
    """Checks if the configuration file and needed directories exist where expected

    Args:
        prefix:  Directory where .config/hkg/settings.conf lives

    Returns:
        True if config exists at file path and False if not

    """
    # Make sure download and install directories exist
    if not os.path.isdir(os.path.expanduser('~/.cache/hkg')):
        print('Cache directory does not exist.  Creating `~/.cache/hkg/`.')
        os.makedirs(os.path.expanduser('~/.cache/hkg'), exist_ok=True)
    if not os.path.isdir(os.path.expanduser('~/.local/share/hkg')):
        print('Install directory does not exist.  Creating `~/.local/share/hkg/`.')
        os.makedirs(os.path.expanduser('~/.local/share/hkg'), exist_ok=True)
    if not os.path.isdir(os.path.expanduser('~/bin')):
        print('User bin directory does not exist.  Creating `~/bin/`.')
        print('Please check your $PATH to make sure `~/bin/` is in your user\'s path.')
        os.makedirs(os.path.expanduser('~/bin'), exist_ok=True)

    config_path = os.path.normpath(os.path.expanduser(prefix)) + '/.config/hkg/settings.conf'

    return os.path.isfile(config_path)


def create_default_config(prefix):
    """Writes a generic configuration file to disk

    Args:
        prefix:  Directory where .config/hkg/settings.conf lives

    Returns:
        True if write is successful and False if not

    """
    config_data = configparser.ConfigParser(delimiters='=')
    config_path = os.path.expanduser(prefix) + '/.config/hkg/settings.conf'
    # Make sure the 'hkg' directory exists
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    config_data['SOURCES'] = {}
    config_data['OPTIONS'] = {}
    write_config = open(config_path, 'w')
    config_data.write(write_config)
    write_config.close()
    return check_config_exists(prefix)


def load_config(prefix):
    """Opens the config file and returns values as a dictionary of dictionaries

    Args:
        prefix:  Directory where .config/hkg/settings.conf lives

    Returns:
        Dictionary of dictionaries containing configuration information

    """
    raw_config_data = configparser.ConfigParser(delimiters='=')
    parsed_config_data = {}
    config_path = os.path.expanduser(prefix) + '/.config/hkg/settings.conf'
    raw_config_data.read(config_path)
    for section in raw_config_data.sections():
        parsed_config_data[section] = {}
        for option in raw_config_data.options(section):
            parsed_config_data[section][option] = raw_config_data.get(section, option)
    return parsed_config_data


def parse_args():
    """Parses the command line arguments and parameters provided when hkg is executed

    Args:

    Returns:
         Dictionary containing arguments as keys

    """
    docstring = """HKG - a simple package manager for your home directory

    Usage:
      hkg install <package_name>
      hkg remove <package_name>
      hkg update [--no-preserve] (<package_name> | all)
      hkg info <package_name>
      hkg repo (add | del) <repo_url>
      hkg repo (init | update) <path_to_repo>
      hkg list (repos | packages (<repo_url> | all | local))
      hkg package [init] <path_to_package_tree>
      hkg readme
      hkg (-h | --help)
      hkg --version

    Options:
      -h --help     Show this screen.
      --version     Show version.
    """

    # This bit of code prevents HKG version info to not be hard-coded into the python code and instead use pkg metadata
    # If we don't have a local package database already created, we'll need to make a new default one
    if not os.path.isfile(os.path.expanduser('~/.local/share/hkg/packages.hdb')):
        init_package_database(os.path.expanduser('~/.local/share/hkg'))
    # Check if HKG has been installed
    if package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'check', 'INSTALLED', 'hkg', ''):
        # Set version using local package database info
        hkg_version = package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'version',
                                           'INSTALLED', 'hkg', '')
        hkg_version = 'HKG - ' + hkg_version
    else:
        # Tell user they need to install HKG in order for --version to pull
        hkg_version = 'Please install HKG to gain access to version information.'

    #
    return docopt.docopt(docstring, version=hkg_version)


def install_package(pkg_name, source_override):
    """Download and install a .hkg package

    Args:
        pkg_name:  name of the package to install
        source_override:  specify a specific source repository to use instead of cycling through configured repo's

    Returns:
        Boolean:  True if package was successfully downloaded and installed into user's home directory
                 False if there was an error anywhere along the way

    """
    # TODO
    # Check if package is in cache and if that package is same version as what is in repo, install from cache instead

    # Check to see if this package is already installed and exit if so
    if os.path.isfile(os.path.expanduser('~/.local/share/hkg/packages.hdb')):
        if package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'),
                                'check', 'INSTALLED', pkg_name, '0'):
            print('Package `%s` is already installed.\nExiting...' % pkg_name)
            return False

    # Make sure download and install directories exist
    if not os.path.isdir(os.path.expanduser('~/.cache/hkg')):
        print('Cache directory does not exist.  Creating `~/.cache/hkg/`.')
        os.makedirs(os.path.expanduser('~/.cache/hkg'), exist_ok=True)
    if not os.path.isdir(os.path.expanduser('~/.local/share/hkg')):
        print('Install directory does not exist.  Creating `~/.local/share/hkg/`.')
        os.makedirs(os.path.expanduser('~/.local/share/hkg'), exist_ok=True)
    if not os.path.isdir(os.path.expanduser('~/bin')):
        print('User bin directory does not exist.  Creating `~/bin/`.')
        print('Please check your $PATH to make sure `~/bin/` is in your user\'s path.')
        os.makedirs(os.path.expanduser('~/bin'), exist_ok=True)

    # Download package
    # Load list of sources from config
    config_data = load_config(os.path.expanduser('~'))
    if source_override == '':
        sources = list(config_data['SOURCES'].keys())
    else:
        sources = [source_override]

    # Iterate through list of sources and download the package databases
    for i in range(0, len(sources)):
        # Check that package database for the name of the package being installed
        try:
            remote_db = requests.get(sources[i] + '/packages.hdb')
        except ConnectionError:
            continue
        remote_pkg_data = configparser.ConfigParser(delimiters='=')
        remote_pkg_data.read_string(remote_db.text)
        # If the package we want to install is in that list download it and proceed to decompress step
        if pkg_name in list(remote_pkg_data['AVAILABLE'].keys()):
            print('Located %s in repo %s!' % (pkg_name, sources[i]))
            print('Downloading %s/%s.hkg' % (sources[i], pkg_name))
            pkg_download = requests.get(sources[i] + '/' + pkg_name + '.hkg')
            write_pkg_path = os.path.expanduser('~/.cache/hkg') + '/' + pkg_name + '.hkg'
            write_pkg = open(write_pkg_path, 'wb')
            for chunk in pkg_download.iter_content(1048576):  # 1MB (1024*1024) chunks
                write_pkg.write(chunk)
            write_pkg.close()
            break
    else:
        print('Package `%s` was not found on any configured, reachable repositories.' % pkg_name)
        print('Please try a different name or add additional repositories.')
        return False

    # Decompress package to target
    write_pkg = tarfile.open(write_pkg_path, 'r')
    # Need to test here more to make sure that all files are extracted as the user that's running hkg
    # Need to make sure the files retain their chmod values as well
    # Looks like it's all good, but just note that if there are issues, this command could be culprit
    write_pkg.extractall(path=os.path.expanduser('~/.local/share/hkg'))

    # Create symbolic link
    bin_target = os.listdir(os.path.expanduser('~/.local/share/hkg/' + pkg_name + '/' + pkg_name))
    bin_target.remove('etc')
    bin_target.remove('lib')
    if len(bin_target) is not 1:
        print('Package is malformed and executable was not able to be located.')
        return False
    else:
        print(bin_target[0])
        if os.path.exists(os.path.expanduser('~/bin/') + pkg_name) is True:
            print('Unable to create symlink due to filename already existing.')
            print('Please make following path available and then remove and re-install package.')
            print(os.path.expanduser('~/bin/') + pkg_name)
            print('Package will remain broken until it has been removed and installed again.')
        else:
            os.symlink(os.path.expanduser('~/.local/share/hkg/' + pkg_name + '/' + pkg_name + '/' + bin_target[0]),
                       os.path.expanduser('~/bin/') + pkg_name)

    # Update local package database
    # If we don't have a local package database already created, we'll need to make a new default one
    if not os.path.isfile(os.path.expanduser('~/.local/share/hkg/packages.hdb')):
        init_package_database(os.path.expanduser('~/.local/share/hkg'))
    # Now we'll need to parse the newly installed package's metadata to get the version number
    metadata = configparser.ConfigParser(delimiters='=')
    metadata.read(os.path.expanduser('~/.local/share/hkg/') + pkg_name + '/' + 'metadata')
    pkg_installed_version = metadata['METADATA']['version']
    # Now we have enough info to run a package update call
    package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'create', 'INSTALLED', pkg_name,
                         pkg_installed_version)

    # Should we get to this point, we've been able to install successfully!
    print('Package `%s` successfully installed!' % pkg_name)
    return True


def remove_package(pkg_name):
    """Remove a package and its files from a user's home directory

    Args:
        pkg_name:  Name of the package to remove

    Returns:
        Boolean:  True if able to remove package and its files, False if unable to remove package and its files

    """
    # Check to see if a package database exists and exit if not
    if not os.path.isfile(os.path.expanduser('~/.local/share/hkg/packages.hdb')):
        print('Package database does not exist.  Cannot delete without a package database.')
        return False

    # Check to see if this package is not installed and exit if so
    if not package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'check', 'INSTALLED',
                                pkg_name, '0'):
        print('Package `%s` is not installed.\nExiting...' % pkg_name)
        return False

    # Update local package database
    package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'delete', 'INSTALLED', pkg_name, '0')
    print('Package `%s` removed from local package database.' % pkg_name)

    # Remove files
    # Make sure that pkg_name isn't an empty string, or we might delete the entire hkg installed packages directory
    # That would be "Bad"
    if bool(pkg_name):
        shutil.rmtree(os.path.expanduser('~/.local/share/hkg/') + pkg_name)
    if os.path.isfile(os.path.expanduser('~/.cache/hkg/' + pkg_name + '.hkg')):
        os.remove(os.path.expanduser('~/.cache/hkg/' + pkg_name + '.hkg'))
    if os.path.islink(os.path.expanduser('~/bin/') + pkg_name):
        os.unlink(os.path.expanduser('~/bin/') + pkg_name)
    print('Package `%s` files deleted.' % pkg_name)

    return True


def update_package(pkg_name, no_preserve_flag):
    """Installs latest version of a package that can be found in configured remote repositories

    Args:
        pkg_name:  name of package to be updated; if this is 'all' then we'll try to update all installed packages

    Returns:
        Boolean:  True if able to update packages, False if unable to update packages for a given reason

    """
    # Check that we have a package database
    if not os.path.isfile(os.path.expanduser('~/.local/share/hkg/packages.hdb')):
        print('Not able to locate package database.  Exiting...')
        return False

    # Load up the user's local package database
    local_pkg_db = configparser.ConfigParser(delimiters='=')
    local_pkg_db.read(os.path.expanduser('~/.local/share/hkg/packages.hdb'))

    # Load up te user's repo list
    config_data = load_config(os.path.expanduser('~'))
    sources = list(config_data['SOURCES'].keys())

    if pkg_name == 'all':
        packages_to_check = list(local_pkg_db['INSTALLED'].keys())
    else:
        packages_to_check = [pkg_name]

    post_update_cleanup = False

    # Iterate through each installed package and check if any remote has an updated version
    for p in packages_to_check:
        # Cycle through each source and download the remote pkg db
        for s in sources:
            try:
                remote_db = requests.get(s + '/packages.hdb')
            except ConnectionError:
                continue
            remote_pkg_data = configparser.ConfigParser(delimiters='=')
            remote_pkg_data.read_string(remote_db.text)
            # If the package is in the remote's pkg db...
            if p in list(remote_pkg_data['AVAILABLE'].keys()):
                # ...check to see if the remote's version is newer than the locally installed version
                if remote_pkg_data['AVAILABLE'][p] > local_pkg_db['INSTALLED'][p]:
                    print('We need to update `%s`' % p)
                    # Get list of package's etc files
                    pkg_etc_files = os.listdir(os.path.expanduser('~/.local/share/hkg/%s/%s/etc' % (p, p)))
                    # If there's any files in the package etc directory, we need to move them temporarily
                    if len(pkg_etc_files) > 0 and no_preserve_flag is False:
                        post_update_cleanup = True
                        print('Old package `./etc/` files saved as `$FILENAME.hkg_old`.')
                        print('Please merge any customized configuration files or settings as needed.')
                        print('Files located in %s' % os.path.expanduser('~/.local/share/hkg/%s/%s/etc/' % (p, p)))
                        os.makedirs(os.path.expanduser('~/.cache/hkg/temp'), exist_ok=True)
                        for f in pkg_etc_files:
                            os.rename(os.path.expanduser('~/.local/share/hkg/%s/%s/etc/' % (p, p)) + f,
                                      os.path.expanduser('~/.cache/hkg/temp/') + '%s.hkg_old' % f)

                    # Remove the old, currently installed package
                    remove_package(p)
                    # Install package from currently iterated source location via override
                    install_package(p, s)

                    # If there were any files copied out of the package etc directory, copy them back
                    if post_update_cleanup is True:
                        pkg_etc_files = os.listdir(os.path.expanduser('~/.cache/hkg/temp/'))
                        for f in pkg_etc_files:
                            os.rename(os.path.expanduser('~/.cache/hkg/temp/') + '%s' % f,
                                      os.path.expanduser('~/.local/share/hkg/%s/%s/etc/%s' % (p, p, f)))
                        # Cleanup any files we saved
                        shutil.rmtree(os.path.expanduser('~/.cache/hkg/temp'))

    return True


def add_repo(prefix, repo_url):
    """Adds a remote repository to user's HKG configuration file

    Args:
        prefix:  Filesystem path to where `.config/hkg/settings.conf` is located.  This is usually just `~/`.
        repo_url:  The URL to add

    Returns:
        Boolean:  True if able to add the repo and False if not able to add the repo

    """
    # Load the config data
    config_data = configparser.ConfigParser(delimiters='=')
    config_path = os.path.expanduser(prefix) + '/.config/hkg/settings.conf'
    config_data.read(config_path)

    # Add new enabled repo to SOURCES list
    config_data['SOURCES'][repo_url] = 'enabled'

    # Write new config to file (overwrites old data)
    write_config = open(config_path, 'w')
    config_data.write(write_config)
    write_config.close()

    print('Remote `%s` added to sources list.' % repo_url)

    return True


def del_repo(prefix, repo_url):
    """Removes a remote repository from user's HKG configuration file

    Args:
        prefix:  Filesystem path to where `.config/hkg/settings.conf` is located.  This is usually just `~/`.
        repo_url:  The URL to remove

    Returns:
        Boolean:  True if able to remove the repo and False if not able to remove the repo

    """
    # Load the config data
    config_data = configparser.ConfigParser(delimiters='=')
    config_path = os.path.expanduser(prefix) + '/.config/hkg/settings.conf'
    config_data.read(config_path)

    # Delete the repo from SOURCES list
    if repo_url in list(config_data['SOURCES']):
        del config_data['SOURCES'][repo_url]
    else:
        print('Source repo not in config data.')
        return False

    # Write new config to file (overwrites old data)
    write_config = open(config_path, 'w')
    config_data.write(write_config)
    write_config.close()

    print('Remote `%s` removed from sources list.' % repo_url)

    return True


def list_repo(prefix):
    """List all the package repositories configured in user's configuration file

    Args:
        prefix:  Filesystem path to where `.config/hkg/settings.conf` is located.  This is usually just `~/`.

    Returns:
        Boolean:  True if able to find config file and print list of repos, False if not able to find and list repos

    """
    # Check if we have a config file in expected location
    if not os.path.isfile(os.path.expanduser(prefix) + '/.config/hkg/settings.conf'):
        print('Unable to find configuration file at %s/.config/hkg/settings.conf' % os.path.expanduser(prefix))
        return False

    # Load the config data
    config_data = configparser.ConfigParser(delimiters='=')
    config_path = os.path.expanduser(prefix) + '/.config/hkg/settings.conf'
    config_data.read(config_path)

    # Print the list of repo's
    for i in range(0, len(list(config_data['SOURCES']))):
        print('Source %d:  %s' % (i+1, list(config_data['SOURCES'])[i]))

    return True


def create_repo(repo_location):
    """Initialize an empty package repository at target location

    Args:
        repo_location:  filesystem path to where the repository is to be created

    Returns:
        Boolean:  True if able to initialize the repository, False if not able to create the needed files

    """
    if os.path.isabs(repo_location) is not True:
        repo_location = os.path.abspath(repo_location)

    return init_package_database(repo_location)


def update_repo(repo_location):
    """Look through packages in a repo directory and check if they are in the repo's pkg db and updates the pkg db

    Args:
        repo_location:  Filesystem path to where the HKG repository lives; should have a *.hdb file in it

    Returns:
        Boolean:  True if database update completed and False if update was not able to be completed

    """
    # Make sure we have a package database to work with
    if not os.path.isfile(repo_location + '/packages.hdb'):
        print('Unable to find `packages.hdb` in `%s`.  Exiting...' % repo_location)
        return False

    # Get a list of all .hkg files in the repo directory and clean up our list of packages
    repo_pkg_list = os.listdir(repo_location)
    repo_pkg_list.remove('packages.hdb')
    # Checks all files in our list and if the last 4 characters are not '.hkg', drop that file from our list
    # Only run this check if there are more files in the repo directory than just the package database file
    if len(repo_pkg_list) > 0:
        for i in range(0, len(repo_pkg_list)):
            if repo_pkg_list[i][-4:] != '.hkg':
                repo_pkg_list.remove(repo_pkg_list[i])

    # Initialize dictionary that's going to hold a list of all the packages in the package repo dir and their version
    repo_pkg_version_dict = {}

    # Peek inside package's and load the metadata of each package and build a dict with package_name:version
    for i in repo_pkg_list:
        repo_pkg_archive = tarfile.open(repo_location + '/' + i, 'r')
        repo_pkg_metadata_object = repo_pkg_archive.extractfile(repo_pkg_archive.getmember('./' + i[:-4] + '/metadata'))
        repo_pkg_metadata_content = repo_pkg_metadata_object.read()
        repo_pkg_archive.close()
        repo_pkg_data = configparser.ConfigParser(delimiters='=')
        repo_pkg_data.read_string(str(repo_pkg_metadata_content, 'utf-8'))
        repo_pkg_version_dict[i[:-4]] = repo_pkg_data['METADATA']['version']

    # One by one, check each `package = version` of the .hkg files in the repo directory with what is in AVAILABLE list
    for i in list(repo_pkg_version_dict.keys()):
        # If the package is not in AVAILABLE, add it
        if not package_database_api(repo_location + '/packages.hdb', 'check', 'AVAILABLE', i, '-1'):
            package_database_api(repo_location + '/packages.hdb', 'create', 'AVAILABLE', i, repo_pkg_version_dict[i])
            print('Found new package!  Added `%s` to repository database.' % i)
        # If the package is in AVAILABLE and version is higher than in AVAILABLE, update the version in AVAILABLE
        # PEP8 makes this section ugly to read
        elif repo_pkg_version_dict[i] > package_database_api(
                                                                repo_location + '/packages.hdb', 'version',
                                                                'AVAILABLE', i, '-1'):
                package_database_api(repo_location + '/packages.hdb', 'update', 'AVAILABLE', i,
                                     repo_pkg_version_dict[i])
                print('Found new version of `%s`.  Updated available version in repository database.' % i)

    # Now we need to check if there are any packages in the package database that no longer exist in the repo directory
    repo_pkg_db = configparser.ConfigParser(delimiters='=')
    repo_pkg_db.read(repo_location + '/packages.hdb')
    for i in list(repo_pkg_db['AVAILABLE'].keys()):
        if i not in list(repo_pkg_version_dict.keys()):
            package_database_api(repo_location + '/packages.hdb', 'delete', 'AVAILABLE', i, '-1')
            print('Package `%s` no longer available.  Deleted `%s` from repository database.' % (i, i))

    return True


def create_package(source_location):
    """Creates zip archive of package files

    Args:
        source_location:  path on filesystem to top of source directory

    Returns:
        Boolean:  True if successfully able to create package and write to disk, False if not able to create package

    """
    # Path sanitation to weed out problems with relative paths.
    source_location = os.path.expanduser(source_location)
    if os.path.isabs(source_location) is not True:
        source_location = os.path.abspath(source_location)

    # Check to make sure metadata is properly formatted
    if validate_metadata(os.path.normpath(os.path.expanduser(source_location)) + '/metadata') is not True:
        print('Metadata improperly formatted.  Aborting package creation.')
        return False

    # Change our current working directory to the directory that package's top level directory lives in
    # We do this so that when decompressing, we don't replicate any of the higher level directories that might have
    #     existed where the package was created.
    # Kind of a hackish solution and I'd like a cleaner implementation that doesn't require changing the CWD.
    os.chdir(os.path.dirname(os.path.normpath(os.path.expanduser(source_location))))

    # Create the archive, note that this will overwrite any existing file w/ the same name
    with tarfile.open(os.path.normpath(os.path.expanduser(source_location)) + '.hkg', "w:gz") as new_package:
        new_package.add('./' + os.path.basename(os.path.normpath(source_location)) + '/')
    new_package.close()

    # Small check to make sure we did write the file and it's where and named what we're expecting
    if os.path.isfile(os.path.normpath(source_location) + '.hkg') is True:
        print('Successfully created package in `%s`.' % source_location)
        return True
    else:
        return False


def validate_source_directory(source_location):
    """Perform some basic validation on the directory that the user is wanting to use to create a package

    Args:
        source_location:  filesystem directory that contains the metadata file and source files

    Returns:
        Boolean:  True if everything looks good, False if there's anything out of basic hkg packaging specification

    """
    check_status_1 = False
    check_status_2 = False

    # One file named meta data in base directory
    # Source directory with same name as base directory in base directory
    if len(os.listdir(source_location)) == 2:
        if 'metadata' in os.listdir(source_location):
            if os.path.basename(os.path.normpath(source_location)) in os.listdir(source_location):
                check_status_1 = True

    # Inside the source directory, one file that is executable and two
    #   directories, 'etc' and 'lib'
    if len(os.listdir(source_location + '/' + os.path.basename(os.path.normpath(source_location)))) == 3:
        if 'etc' in os.listdir(source_location + '/' + os.path.basename(os.path.normpath(source_location))):
            if 'lib' in os.listdir(source_location + '/' + os.path.basename(os.path.normpath(source_location))):
                check_status_2 = True

    # All other files and directories must be in either
    #   source/etc or source/lib

    # Returns True if both series of checks pass
    return check_status_1 and check_status_2


def init_package_directory(source_location):
    """Create the basic files and directories for a new package.

    Args:
        source_location:  where to create the new package framework

    Returns:
        Boolean:  True if successful and False if not able to create files and directories

    """
    init_success = False
    
    if os.path.isabs(source_location) is not True:
        source_location = os.path.abspath(source_location)

    try:
        # Creating the needed directories and files
        os.makedirs(os.path.normpath(source_location), exist_ok=True)
        os.makedirs(os.path.normpath(source_location) + '/' + os.path.basename(os.path.normpath(source_location)),
                    exist_ok=True)
        os.makedirs(os.path.normpath(source_location) + '/' + os.path.basename(os.path.normpath(source_location))
                    + '/etc', exist_ok=True)
        os.makedirs(os.path.normpath(source_location) + '/' + os.path.basename(os.path.normpath(source_location))
                    + '/lib', exist_ok=True)
        open(os.path.normpath(source_location) + '/metadata', 'a').close()
        open(os.path.normpath(source_location) + '/' + os.path.basename(os.path.normpath(source_location))
             + '/your_program.bin', 'a').close()

        # Create the basic metadata entries
        metadata = configparser.ConfigParser(delimiters='=')
        metadata_path = os.path.normpath(source_location) + '/metadata'
        metadata['METADATA'] = {
            'name': 'your_program',
            'version': 0.0,
            'description': 'A brief description of your program goes here.',
            'author_name': 'your_name',
            'author_email': 'your_email@example.com',
            'website': 'http://example.com'
        }
        metadata_file = open(metadata_path, 'w')
        metadata.write(metadata_file)
        metadata_file.close()

        init_success = True
        print('\nSuccessfully create skeleton package at \'%s\'.' % source_location)
        print('\nREMEMBER TO UPDATE THE METADATA!')
    except OSError:
        print('\nUnable to create files at \'%s\'.')
        print('Please check path and/or permissions.')
        init_success = False

    return init_success


def validate_metadata(metadata_path):
    """Parse package metadata and check if contents are valid.

    Args:
        metadata_path:  path to metadata file

    Returns:
        Boolean:  True if metadata is valid, False if metadata is invalid

    """
    metadata_is_valid = False
    metadata = configparser.ConfigParser(delimiters='=')
    metadata.read(metadata_path)
    metadata_data = {}
    for section in metadata.sections():
        metadata_data[section] = {}
        for option in metadata.options(section):
            metadata_data[section][option] = metadata.get(section, option)
    if len(list(metadata_data.keys())) == 1:
        if list(metadata_data.keys())[0] == 'METADATA':
            if len(list(metadata_data['METADATA'].keys())) == 6:
                if 'name' in list(metadata_data['METADATA'].keys()) \
                    and 'version' in list(metadata_data['METADATA'].keys()) \
                        and 'description' in list(metadata_data['METADATA'].keys()) \
                            and 'author_name' in list(metadata_data['METADATA'].keys()) \
                                and 'author_email' in list(metadata_data['METADATA'].keys()) \
                                    and 'website' in list(metadata_data['METADATA'].keys()):
                                        metadata_is_valid = True

    return metadata_is_valid


def init_package_database(db_location):
    """Create a skeleton package database

    Args:
        db_location:  filesystem path where you want the database file to be written to

    Returns:
        Boolean:  True if able to write database file, False if not able to write database file

    """
    try:
        if os.path.isdir(db_location) is True:
            newdb = open(os.path.normpath(db_location) + '/packages.hdb', 'a')
            print('Creating new package database at \'%s\'.' % (os.path.normpath(db_location) + '/packages.hdb'))
        elif os.path.basename(db_location) == 'packages.hdb':
            newdb = open(db_location, 'a')
            print('Creating new package database at \'%s\'.' % db_location)
        else:
            os.makedirs(db_location, exist_ok=True)
            newdb = open(os.path.normpath(db_location) + '/packages.hdb', 'a')
            print('Creating new package database at \'%s\'.' % (os.path.normpath(db_location) + '/packages.hdb'))

        newdb.write('[INSTALLED]\n')
        newdb.write('\n')
        newdb.write('[AVAILABLE]\n')

        return True

    except OSError:
        print('Unable to create new package database at \'%s\'.' % db_location)
        print('Check path and/or permissions.')

        return False


def validate_package_database(db_location):
    """Validate package database conforms to hkg specifications

    Args:
         db_location:  filesystem path where the database exists

    Returns:
        Boolean:  True if package database conforms to spec, False if it does not

    """
    testdb = configparser.ConfigParser(delimiters='=')
    testdb.read(db_location)
    db_data = testdb._sections
    db_is_valid = False

    # Make sure there are only 2 sections
    if len(list(db_data.keys())) == 2:
        # Make sure they are named correctly
        if 'INSTALLED' in list(db_data.keys()) and 'AVAILABLE' in list(db_data.keys()):
            # Make sure all the package names in each section are lowercase letters and only lowercase letters
            if all(package_name.islower() for package_name in list(db_data['INSTALLED'].keys())) \
                and all(package_name.islower() for package_name in list(db_data['AVAILABLE'].keys())) \
                    and all(package_name.isalpha() for package_name in list(db_data['INSTALLED'].keys())) \
                    and all(package_name.isalpha() for package_name in list(db_data['AVAILABLE'].keys())):
                            # Make sure each package version is in \d.\d format
                            # Note:  Changing the '1' to a '2' in the replace() methods will allow \d.\d.\d version-ing
                            if all(package_ver.replace('.', '', 1).isdigit() for package_ver in
                                    list(db_data['INSTALLED'].values())) \
                                    and all(package_ver.replace('.', '', 1).isdigit() for package_ver in
                                            list(db_data['AVAILABLE'].values())):
                                            # All tests have passed!
                                            db_is_valid = True

    return db_is_valid


def package_database_api(db_location, db_action, db_section, db_pkgname, db_pkgver):
    """Change the contents of a database entry for a package

    Args:
        db_location:  filesystem location of package database
        db_action:  what are we doing to the database? updating an entry, adding a new package, deleting, etc.
        db_section:  are we dealing with INSTALLED packages or AVAILABLE packages?
        db_pkgname:  the name of the package whose entry is being changed
        db_pkgver:  0 for entry deletion or non-zero for pkg being installed or available version change

    Returns:
        Boolean:  True if update operation completed successfully or false if it failed

    """
    pkg_db = configparser.ConfigParser(delimiters='=')
    pkg_db.read(db_location)

    if db_action == 'create':
        # Add a new entry in a section
        pkg_db[db_section][db_pkgname] = db_pkgver
        pkg_db_file = open(db_location, 'w')
        pkg_db.write(pkg_db_file)
        pkg_db_file.close()
        return True

    elif db_action == 'delete':
        # Delete an existing entry from a section
        pkg_db[db_section][db_pkgname] = db_pkgver
        pkg_db_file = open(db_location, 'w')
        del pkg_db[db_section][db_pkgname]
        pkg_db.write(pkg_db_file)
        pkg_db_file.close()
        return True

    elif db_action == 'update':
        # Change the version for an existing package in a section
        # Might be able to combine 'create' and 'update' actions...
        pkg_db[db_section][db_pkgname] = db_pkgver
        pkg_db_file = open(db_location, 'w')
        pkg_db.write(pkg_db_file)
        pkg_db_file.close()
        return True

    elif db_action == 'check':
        # Returns True if package name exists in specified section of package database, False if not found
        return db_pkgname in list(pkg_db[db_section].keys())

    elif db_action == 'version':
        # Returns the version number of the package name requested
        return pkg_db[db_section][db_pkgname]

    elif db_action == 'list':
        # Returns a list of all packages listed under specified section
        return list(pkg_db[db_section].keys())

    else:
        # Didn't get a valid db_action value so fail out of the function
        return False


def list_packages(pkg_source):
    """List the packages that are available at the specified location

    Args:
        pkg_source:  either a remote repo that's configured, 'all' remote repos, or 'local' for all installed packages

    Returns:
        Boolean:  True if able to list packages from specified source, False if not

    """
    config_data = load_config(os.path.expanduser('~'))

    # List packages from the local package database
    if pkg_source == 'local':
        source_list = package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'), 'list',
                                           'INSTALLED', 'none', 'none')

        print('Packages installed locally:')
        for i in source_list:
            print('%s : %s' % (i, package_database_api(os.path.expanduser('~/.local/share/hkg/packages.hdb'),
                  'version', 'INSTALLED', i, None)))

        return True

    # List packages from remote package databases
    elif pkg_source in list(config_data['SOURCES'].keys()) or pkg_source == 'all':
        if pkg_source == 'all':
            source_list = list(config_data['SOURCES'].keys())
        else:
            source_list = [pkg_source]

        for s in source_list:

            # Download the remote repo's package database
            try:
                remote_db = requests.get(s + '/packages.hdb')
            except ConnectionError:
                print('Unable to connect to requested repository.')
                return False

            # Load and parse the package database
            remote_pkg_data = configparser.ConfigParser(delimiters='=')
            remote_pkg_data.read_string(remote_db.text)

            # Print out using 'package_name : package_version' formatting
            print('Packages available at %s:' % s)
            for i in list(remote_pkg_data['AVAILABLE'].keys()):
                print('%s : %s' % (i, remote_pkg_data['AVAILABLE'][i]))

        return True

    else:
        print('It appears `%s` is not a valid or configured repository.' % pkg_source)
        return False


def package_info(pkg_name):
    """Prints out the metadata information for a specified package

    Args:
        pkg_name:  The name of the package to display the metadata for

    Returns:
        Boolean:  True if package metadata was found and able to be printed, False if not

    """
    # Check cache to see if package has already been downloaded
    print('Checking cache for package `%s`...' % pkg_name)
    if os.path.isfile(os.path.expanduser('~/.cache/hkg/%s.hkg' % pkg_name)):
        print('Package found in cache.')
    else:
        # Download package if not in cache
        print('Package not found in cache.  Attempting to download package...')
        config_data = load_config(os.path.expanduser('~'))
        sources = list(config_data['SOURCES'].keys())

        # Iterate through list of sources and download the package databases
        for i in range(0, len(sources)):
            # Check that package database for the name of the package being installed
            try:
                remote_db = requests.get(sources[i] + '/packages.hdb')
            except ConnectionError:
                continue
            remote_pkg_data = configparser.ConfigParser(delimiters='=')
            remote_pkg_data.read_string(remote_db.text)
            # If the package we want to install is in that list download it and proceed to decompress step
            if pkg_name in list(remote_pkg_data['AVAILABLE'].keys()):
                print('Located %s in repo %s!' % (pkg_name, sources[i]))
                print('Downloading %s/%s.hkg' % (sources[i], pkg_name))
                pkg_download = requests.get(sources[i] + '/' + pkg_name + '.hkg')
                write_pkg_path = os.path.expanduser('~/.cache/hkg') + '/' + pkg_name + '.hkg'
                write_pkg = open(write_pkg_path, 'wb')
                for chunk in pkg_download.iter_content(1048576):  # 1MB (1024*1024) chunks
                    write_pkg.write(chunk)
                write_pkg.close()
                break
        else:
            print('Package `%s` was not found on any configured, reachable repositories.' % pkg_name)
            print('Please try a different name or add additional repositories.')
            return False

    # Open package in memory and read in metadata
    pkg_archive = tarfile.open(os.path.expanduser('~/.cache/hkg') + '/' + pkg_name + '.hkg', 'r')
    pkg_metadata_object = pkg_archive.extractfile(pkg_archive.getmember('./' + pkg_name + '/metadata'))
    pkg_metadata_content = pkg_metadata_object.read()
    pkg_archive.close()
    pkg_data = configparser.ConfigParser(delimiters='=')
    pkg_data.read_string(str(pkg_metadata_content, 'utf-8'))

    # Print contents of metadata file
    for i in list(pkg_data['METADATA'].keys()):
        print('%s : %s' % (i, pkg_data['METADATA'][i]))

    return True


def print_readme(prefix):
    """Print out in the terminal the contents of HKG's README file

    Returns:
        Boolean:  True if README file found and printed out, False if not able to print README

    """
    # Expect README file to be at this location
    readme_path = os.path.normpath(os.path.expanduser(prefix)) + '/.local/share/hkg/hkg/hkg/lib/readme.md'

    # Check if HKG is installed
    if package_database_api(os.path.normpath(os.path.expanduser(prefix)) + '/.local/share/hkg/packages.hdb', 'check',
                            'INSTALLED', 'hkg', '') is True:
        # Check that the README file is where we expect
        if os.path.exists(readme_path):
            print('README file located.')
            readme_file = open(readme_path, 'r')
            readme_contents = readme_file.read()
            print(readme_contents)
            return True
        else:
            print('Unable to locate README file at expected path:')
            print(readme_path)
            return False
    else:
        print('Please install HKG to view contents of HKG\'s README.')
        return False

if __name__ == '__main__':

    # Load HKG settings
    config_prefix = '~'
    # If config file doesn't exist where expected, create it with default settings
    if check_config_exists(config_prefix) is not True:
        print('Configuration file not found.\nCreating default configuration file at `~/.config/hkg/settings.conf`.\n')
        create_default_config(config_prefix)

    # Load user's HKG settings into memory
    load_config(config_prefix)

    # Parse command line arguments and load them into a dictionary
    args = parse_args()

    # Process flags, arguments, and switches
    if args['install'] is True and args['<package_name>'] is not None:
        print('Installing package:  %s' % args['<package_name>'])
        install_package(args['<package_name>'], '')

    elif args['remove'] is True and args['<package_name>'] is not None:
        print('Removing package:  %s' % args['<package_name>'])
        remove_package(args['<package_name>'])

    elif args['update'] is True and args['<package_name>'] is not None:
        print('Updating package:  %s' % args['<package_name>'])
        update_package(args['<package_name>'], args['--no-preserve'])

    elif args['info'] is True and args['<package_name>'] is not None:
        print('Displaying metadata for package:  %s' % args['<package_name>'])
        package_info(args['<package_name>'])

    elif args['repo'] is True and args['add'] is True and args['<repo_url>'] is not None:
        print('Adding repo with URL:  %s' % args['<repo_url>'])
        add_repo('~', args['<repo_url>'])

    elif args['repo'] is True and args['del'] is True and args['<repo_url>'] is not None:
        print('Deleting repo with URL:  %s' % args['<repo_url>'])
        del_repo('~', args['<repo_url>'])

    elif args['repo'] is True and args['init'] is True and args['<path_to_repo>'] is not None:
        print('Creating HKG repo at path:  %s' % args['<path_to_repo>'])
        create_repo(args['<path_to_repo>'])

    elif args['repo'] is True and args['update'] is True and args['<path_to_repo>'] is not None:
        print('Updating repo database at path:  %s' % args['<path_to_repo>'])
        update_repo(args['<path_to_repo>'])

    elif args['list'] is True and args['repos'] is True:
        print('Listing all configured repo URL\'s:')
        list_repo('~')

    elif args['list'] is True and args['packages'] is True and args['<repo_url>'].lower() is 'local':
        print('Listing all locally installed packages:')
        list_packages(args['<repo_url>'])

    elif args['list'] is True and args['packages'] is True and args['<repo_url>'].lower() is 'all':
        print('Listing packages available from all configured repositories:')
        list_packages(args['<repo_url>'])

    elif args['list'] is True and args['packages'] is True and args['<repo_url>'] is not None:
        print('Listing packages available from repo at:  %s' % args['<repo_url>'])
        list_packages(args['<repo_url>'])

    elif args['package'] is True and args['init'] is True and args['<path_to_package_tree>'] is not None:
        print('Creating new package skeleton at path:  %s' % args['<path_to_package_tree>'])
        init_package_directory(args['<path_to_package_tree>'])

    elif args['package'] is True and args['init'] is False and args['<path_to_package_tree>'] is not None:
        print('Packaging source tree at path:  %s' % args['<path_to_package_tree>'])
        create_package(args['<path_to_package_tree>'])

    elif args['readme'] is True:
        print('Fetching contents of HKG\'s README...')
        print_readme('~')

    else:
        print('No valid argument sets were able to be parsed.')
        print('Please see `hkg --help` for usage information.')
