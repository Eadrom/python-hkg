#!/usr/bin/env bash

# This script installs HKG into a user's home directory
# Process:
#     1.  Install script downloads an archived copy of HKG
#     2.  Install script then extracts the files from the archive
#     3.  Next, the install script calls HKG twice:
#         a.  $> ./hkg.py add repo $CORE_REPO_URL
#         b.  $> ./hkg.py install hkg
#     4.  Lastly, the install script deletes the temp copy of HKG

# Init
HKG_REPO="URL_GOES_HERE"
CORE_REPO_URL="$HKG_REPO/files/packages/hkg"
INSTALL_ARCHIVE_NAME="hkg_install_archive.tar"
DOWNLOAD_BIN="none"

clear
echo "Beginning installation of HKG, the home directory package manager."
echo ""

# Download the install version of HKG
# Check if WGET or CURL are available
echo "Looking for wget or curl binaries..."
if [ -e "/usr/bin/wget" ]; then
    echo "Found /usr/bin/wget and setting it as download agent."
    echo ""
    DOWNLOAD_BIN="/usr/bin/wget"
else
    if [ -e "/usr/bin/curl" ]; then
        echo "Found /usr/bin/curl and setting it as download agent."
        DOWNLOAD_BIN="/usr/bin/curl"
    fi
fi

# Make sure we found wget or curl and exit if not
if [ "$DOWNLOAD_BIN" == "none" ]; then
    echo "Unable to locate wget or curl where expected in \`/usr/bin/\`."
    echo "Exiting..."
    exit 1
fi

# Finally, download the HKG install archive
# Check that the user can write to the current directory
if [ -w "$PWD" ]; then
    echo "Finished pre-checks.  Beginning download..."
    echo ""
else
    echo "Unable to write to current working directory."
    echo "Please execute this installer in a directory your user can write to."
    echo "Exiting..."
    exit 1
fi

if [ "$DOWNLOAD_BIN" == "/usr/bin/wget" ]; then
    /usr/bin/wget "$CORE_REPO_URL"/"$INSTALL_ARCHIVE_NAME"
else
    /usr/bin/curl -O "$CORE_REPO_URL"/"$INSTALL_ARCHIVE_NAME"
fi

# Extract HKG from downloaded archive
# Check that tar is installed and available in user's $PATH
echo "Looking for \`tar\` utility..."
tar --help >/dev/null 2>&1
CHECK_EXIT_CODE="$?"
if [ "$CHECK_EXIT_CODE" == "0" ]; then
    echo "...successful."
    echo ""
else
    echo "Unable to find \`tar\` utility."
    echo "Exiting..."
    exit 1
fi

# Extract the HKG archive
echo "Extracting necessary files for install..."
tar xf "./$INSTALL_ARCHIVE_NAME"

# Check that the files we need have been extracted
if [ -e "./hkg/hkg.py" ] && [ -e "./hkg/lib/docopt.py" ]; then
    echo "...extraction complete."
    echo ""
else
    echo "There was a problem during extraction."
    echo "Exiting..."
fi

# Add CORE repo
echo "Adding CORE package repository..."
/usr/bin/env python3 -c "import os; os.system('./hkg/hkg.py repo add "$CORE_REPO_URL"')"
echo ""

# Install HKG
echo "Installing HKG..."
/usr/bin/env python3 -c "import os; os.system('./hkg/hkg.py install hkg')"
echo ""

# Cleanup
echo "Cleaning up..."
rm ./"$INSTALL_ARCHIVE_NAME"
rm -rf ./hkg

echo "Installation of HKG has been completed."
echo ""
sleep 2
hkg --help
exit 0
