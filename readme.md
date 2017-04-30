# HKG

HKG is a simple package manager for sharing self-contained scripts and utilities that are installed in and run from a normal, unpriviledged user account's home directory.

### Features:
* Install, update, and remove packages
* Easily create .hkg packages and manage a package repository
* Simple requirements for hosting a repository

### Possible Future Features:
* Search for packages available in your configured repositories to see what is available to install
* Package integrity verification via hash comparisons
* Package signing
* Dependency resolution - HKG packages
* Dependency resolution - OS packages

### Installation
* Linux - Supported
    * Need Python 3.x and python3-requests
        * `$> sudo apt-get install python3 python3-requests`
    * Make sure `~/bin/` is in your $PATH
        * Edit `~/.profile` (or file applicable to your distro) and add or uncomment the following three lines:
            * `if [ -d "$HOME/bin" ] ; then`
            * `  PATH="$HOME/bin:$PATH"`
            * `fi`
        * Log out and back in or source `~/.profile` to get correctly setup `$PATH`
    * Bootstrap and Install (WIP)
        * Two options to install.  Use only one of them.
            * Curl the install script into BASH
                * `$> curl $HKG_REPO/files/packages/hkg/hkg-install.sh | env bash`
            * Download the script and then execute it via BASH
                * `wget $HKG_REPO/files/packages/hkg/hkg-install.sh`
                * `bash ./hkg-install.sh`

* MacOS - Supported
    * Need Python 3.x and python3-requests (pip)
        * Python3 - `https://www.python.org/downloads/mac-osx/`
        * `$> sudo pip3 install requests`
    * Make sure `~/bin/` is in your $PATH
        * Edit `/etc/profile` and add or uncomment the following three lines:
            * `if [ -d "${HOME}/bin" ] ; then`
            * `  PATH="${HOME}/bin:${PATH}"`
            * `fi`
        * Log out and back in or source `~/.profile` to get correctly setup `$PATH`
    * Bootstrap and Install (WIP)
        * Two options to install.  Use only one of them.
            * Curl the install script into BASH
                * `$> curl $HKG_REPO/files/packages/hkg/hkg-install.sh | env bash`
            * Download the script and then execute it via BASH
                * `wget $HKG_REPO/files/packages/hkg/hkg-install.sh`
                * `bash ./hkg-install.sh`

* Windows (Cygwin) - Supported
    * Install cygwin and select following packages during install prompts
        * `python3`, `python3-requests`, and `python3-setuptools`
    * Make sure `~/bin/` is in your $PATH
        * Edit `~/.bash_profile` and add or uncomment the following three lines:
            * `if [ -d "${HOME}/bin" ] ; then`
            * `  PATH="${HOME}/bin:${PATH}"`
            * `fi`
        * Close out your cygwin session / terminals or log out and log back in
    * Bootstrap and Install (WIP)
        * Two options to install.  Use only one of them.
            * Curl the install script into BASH
                * `$> curl $HKG_REPO/files/packages/hkg/hkg-install.sh | env bash`
            * Download the script and then execute it via BASH
                * `wget $HKG_REPO/files/packages/hkg/hkg-install.sh`
                * `bash ./hkg-install.sh`

* Windows (Native) - Currently NOT Supported
    * Base Python3 install includes all imports except `requests`
    * To install `requests`, open a command prompt and run `pip3 install requests`
    * Looks like adding and removing repos and installing and removing packages work
    * Default executable directory `~/bin/` is not in Window user's $PATH (this is an expected behavior)
    * Executable files in `~/bin/` (symlinks) don't work correctly
    * Due to excellent support under Cygwin, there are currently no plans support HKG under a native Windows environment

### Commands:
* Install the `foo` package
    * `$> hkg install foo`
* Remove the `foo` package
    * `$> hkg remove foo`
* Update the `foo` package
    * `$> hkg update foo`
* Update all installed packages
    * `$> hkg update all`
* Update the `foo` package and don't save any files in package's `etc` directory
    * `$> hkg update --no-preserve foo`
* Add a package repository
    * `$> hkg repo add http://packages.example.com/hkg/`
* Delete a package repository
    * `$> hkg repo del  http://packages.example.com/hkg/`
* List all configured package repositories
    * `$> hkg list repos`
* Initialize a new, empty package repository
    * `$> hkg repo init /var/www/html/hkg`
* Update contents of a package repository
    * `$> hkg repo update /var/www/html/hkg`
* Create a new package from a specified source directory tree
    * `$> hkg package /home/eadrom/git/foo/`
* Create a skeleton source directory tree for a new package
    * `$> hkg package init /tmp/foo`
* List packages
    * In a specific configured remote repository
        * `$> hkg list packages http://packages.example.com/hkg/`
    * In all configured remote repositories
        * `$> hkg list packages all`
    * Locally installed packages
        * `$> hkg list packages local`
* Print out a package's metadata
    * `$> hkg info foo`
* Print out HKG's README
    * `$> hkg readme`
* Print out version number for user's installed copy of HKG
    * `$> hkg --version`
* Print out HKG usage information
    * `$> hkg -h` or `$> hkg --help`


### HKG Packaging Specifications
* All package names must be lowercase alphabetic
* Versions are to be $MAJOR.$MINOR
* It is preferential, but not enforced, that a package does not create files outside of its individual ./lib or ./etc directories or the system's /tmp directory
* The webroot of a package repository should allow the user running hkg to create or maintain the repository files to write files to that location
* In order to run executables installed by hkg without specifying full path to executable, ~/bin will need to be in the user's PATH
    * You can check if this is setup by seeing if the full path to `~/bin` is in your `$PATH` by executing `$> echo $PATH`
    * To add `~/bin` to your `$PATH`, add `PATH="$HOME/bin:$PATH"` to your `~/.profile`
* When updating packages, any files in a package's `etc` directory will be saved as `$FILENAME.hkg_old` so that the user can merge their custom configurations and settings if needed
* Be sure to document and implement error checking for any dependencies your HKG packages require.  HKG does not (currently) perform any build or runtime dependency management.

### Create a Package:
A .hkg contains a simple meta-data / configuration file and directory containing your files.  Below is an example.

/tmp/spam
├── spam
│   ├── bin.sh
│   ├── etc
│   │   └── settings.conf
│   └── lib
│       ├── assets
│       │   ├── art1.ascii
│       │   └── art2.ascii
│       └── functions.sh
└── metadata

### Packaging
Command to create a package is also very simple.  The following example uses the above example directory tree.  Built packages are output into same directory as the top-level directory of the package being built.
`$> hkg package /tmp/spam`
`/tmp/spam.hkg`

### Metadata File Format
HKG will create an example metadata file when `hkg package init /create/package/skel/here` is run.  Package developers will need to manually edit this file and fill in the correct metadata.
Version incrementation is done manually and it is critical that developers/packagers increment the version when packaging a new release of a program.  HKG relies on this metadata when building and updating the repository side package database.

`[METADATA]`
`name = spam`
`version = 2.1`
`description = An example package`
`author_name= Eadrom`
`author_email = eadrom@example.com`
`website = http://example.com`
