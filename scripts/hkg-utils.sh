#!/usr/bin/env bash

# Provides several utilities to developers and package repository maintainers.
# All remote connections are via SSH; key-based auth is encouraged.
# Default is to prompt for input but a -s flag will allow users to provide all
#     required input as arguments.

# Features:
# * Initialize a remote repository with a basic package database and the files
#   needed for users to install HKG
# * Deploy HKG to a repository; this will build a HKG package from the 
#   ../hkg_package/ directory, upload the package and latest installer to 
#   specified repository, and update the package database on the repository to
#   reflect the new version of HKG that was just uploaded.

USAGE="
$(basename "$0") [-h] [-v] [-s] [-i] -k ssh_key -n hostname -p repo_path

where:
     -h  show this help text
     -v  verbose output mode
     -s  script mode; will not prompt for missing input
     -i  initialize repository
     -k  filepath to user's ssh key
     -n  repository's hostname
     -p  filepath on the repository host where the root of the repository sits
"

# Arguments:
# * `-v`:  Verbose mode; print additional information to the console
# * `-s`:  Run in script mode and don't prompt for input
# * `-i`:  Initialize a repository and then build and push an update
# * `-k`:  filepath to user's SSH key
# * `-n`:  hostname for the server where the repository lives
# * `-p`:  filepath on the remote server where the repository lives
VERBOSE=false
AS_SCRIPT=false
INIT_REPO=false
FAILED_INIT=false
INSTALL_ARCHIVE_NAME="hkg_install_archive.tar"
CMD_OUTPUT=""

while getopts ":hvsik:n:p:" opt ; do
    case $opt in
        h)
            echo "$USAGE"
            exit 0
            ;;
        v)
            VERBOSE=true
            ;;
        s)            
            AS_SCRIPT=true
            ;;
        i)
            INIT_REPO=true
            ;;
        k)
            REPO_KEY=$OPTARG
            ;;
        n)
            REPO_HOST=$OPTARG
            ;;
        p)
            REPO_PATH=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument."
            exit 1
    esac
done

printv ()
{
    if [ "$VERBOSE" = true ]; then
        echo $1
    fi
}

sshcmd ()
{
    printv "SSHCMD:  $1"
    if [ "$VERBOSE" = true ]; then
        ssh -i "$REPO_KEY" "$REPO_HOST" bash -c "'$1'"
    else
        ssh -i "$REPO_KEY" "$REPO_HOST" bash -c "'$1'" >/dev/null 2>&1
    fi
}

sshmv ()
{
    printv "SSHMV:  $1"
    if [ "$VERBOSE" = true ]; then
        scp -i "$REPO_KEY" "$1" "$REPO_HOST:$REPO_PATH/"
    else
        scp -i "$REPO_KEY" "$1" "$REPO_HOST:$REPO_PATH/" >/dev/null 2>&1
    fi
}

printv "Argument Overview:"
printv "Verbose mode on."

if [ "$AS_SCRIPT" = false ]; then
    echo "Running in non-script mode."
else
    printv "Running in script mode."
fi

if [ "$INIT_REPO" = true ]; then
    printv "Initialize mode set."
else
    printv "Running in update mode."
fi

if [ -z "$REPO_KEY" ]; then
    echo "Missing required argument:  \`-k\`"
    FAILED_INIT=true
else
    printv "Using key located at:  $REPO_KEY"
fi

if [ -z "$REPO_HOST" ]; then
    echo "Missing required argument:  \`-n\`"
    FAILED_INIT=true
else
    printv "Connecting to host:  $REPO_HOST"
fi

if [ -z "$REPO_PATH" ]; then
    echo "Missing required argument:  \`-p\`"
    FAILED_INIT=true
else
    printv "Working with repo at:  $REPO_PATH"
    printv ""
fi

# Make sure script is being run from where it expects to be run from
if [ -e "./hkg_package/hkg/hkg/hkg.py" ]; then
    printv "Verified script executed from git root."
    printv ""
else
    echo "Please execute this script from the git root directory."
    echo "If you are running this script from the git root directory and are still seeing this error, the structure of your local HKG git repository may be corrupted.  Please try pulling down a clean clone and try again."
    echo "Exiting..."
    exit 1
fi

if [ ! -e "/tmp/hkgpkgbuild" ]; then
    printv "Package build directory not found.  Creating at \`/tmp/hkgpkgbuild\`..."
    mkdir /tmp/hkgpkgbuild
    printv "...complete."
    printv ""
fi

if [ "$(ls -A /tmp/hkgpkgbuild)" ]; then
    printv "Package build directory not clean and needs to be scrubbed."
    printv ""
    if [ "$AS_SCRIPT" = true ]; then
        printv "Scrubbing build directory..."
        rm -rf /tmp/hkgpkgbuild/*
        printv "...complete."
        printv ""
    else
        echo "Ok to delete contents of \`/tmp/hkgpkgbuild/\`? [y/n]"
        read SCRUB_OK
        if [ "$SCRUB_OK" == "y" ] || [ "$SCRUB_OK" == "Y" ] || [ "$SCRUB_OK" == "yes" ] || [ "$SCRUB_OK" == "YES" ]; then
            printv "Scrubbing build directory..."
            rm -rf /tmp/hkgpkgbuild/*
            printv "...complete."
            printv ""
        else
            echo "Please verify contents of \`/tmp/hkgpkgbuild\` to allow for deletion."
            echo "Exiting..."
            exit 1
        fi
    fi
else
    printv "Package build directory is clean."
    printv ""
fi

if [ ! -e "/tmp/hkgtarbuild" ]; then
    printv "Archive build directory not found.  Creating at \`/tmp/hkgtarbuild\`..."
    mkdir /tmp/hkgtarbuild
    printv "...complete."
    printv ""
fi

if [ "$FAILED_INIT" = true ]; then
    echo "$USAGE"
    exit 1
fi

printv "Script initilization complete!"
printv ""

# Handle repository initialization
if [ "$INIT_REPO" = true ]; then
    # Create the package database
    printv "Creating package database file..."
    sshcmd 'touch '"$REPO_PATH"'/packages.hdb'
    printv "...complete."
    printv ""

    printv "Writing default [INSTALLED] section to package database..."
    sshcmd 'echo "[INSTALLED]" > '"$REPO_PATH"'/packages.hdb'
    sshcmd 'echo "" >> '"$REPO_PATH"'/packages.hdb'
    printv "...complete."
    printv ""

    printv "Writing default [AVAILABLE] section to package database..."
    sshcmd 'echo "[AVAILABLE]" >> '"$REPO_PATH"'/packages.hdb'
    sshcmd 'echo "hkg = 0.0" >> '"$REPO_PATH"'/packages.hdb'
    sshcmd 'echo "" >> '"$REPO_PATH"'/packages.hdb'
    printv "...complete."
    printv ""

    printv "Repository package database successfully initialized at $REPO_PATH."
    printv ""
fi

# Upload the install script to the package repository
printv "Uploading installation script to repository..."        
sshmv './scripts/hkg-install.sh'
printv "...complete."
printv ""
   
# Create the HKG install archive
printv "Building HKG installation archive..."
tar cf "/tmp/hkgtarbuild/$INSTALL_ARCHIVE_NAME" --directory="./hkg_package/hkg/" ./hkg
printv "...complete."
printv ""

# Upload the HKG install archive to the package repository
printv "Uploading HKG installation archive to repository..."
sshmv '/tmp/hkgtarbuild/'"$INSTALL_ARCHIVE_NAME"''
printv "...complete."
printv ""

# Pull out the version number of HKG that we will be pushing to the repository
printv "Querying metadata for version..."
HKG_VER=$(grep "version" ./hkg_package/hkg/metadata | cut -d "=" -f2 | tr -d '[[:space:]]')
printv "Version found: $HKG_VER"
printv ""

printv "Copying HKG source tree to build directory..."
cp -r ./hkg_package/hkg /tmp/hkgpkgbuild/
printv "...complete."
printv ""

# Invoke HKG executable to build the HKG package
printv "Building HKG package..." 
if [ "$VERBOSE" = true ]; then
    /usr/bin/env python3 -c "import os; os.system('./hkg_package/hkg/hkg/hkg.py package /tmp/hkgpkgbuild/hkg')"
else
    /usr/bin/env python3 -c "import os; os.system('./hkg_package/hkg/hkg/hkg.py package /tmp/hkgpkgbuild/hkg')" >/dev/null 2>&1
fi
printv "...complete."
printv ""

# Copy new HKG package to repository
printv "Uploading new HKG package to repository..."
sshmv '/tmp/hkgpkgbuild/hkg.hkg'
printv "...complete."
printv ""

# Update repository's package database with new HKG version
printv "Updating repository package database with latest HKG version..."
sshcmd "sed -i \"s/^hkg =.*/hkg = ${HKG_VER}/\" ${REPO_PATH}/packages.hdb"
printv "...complete."
printv ""

echo "Deployment complete."
exit 0
