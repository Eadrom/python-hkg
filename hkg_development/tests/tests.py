#!/usr/bin/env python3

import unittest
import os
import random
import string

from hkg_development import hkg


class TestInitAndSetup(unittest.TestCase):

    def test_check_if_config_exists(self):
        test_config_path = '/tmp/.config/hkg/settings.conf'
        # Make sure there aren't any config files from previous testing
        if os.path.isfile(test_config_path):
            os.remove(test_config_path)
        # Test to see if correctly return False if file does not exist
        self.assertFalse(hkg.check_config_exists('/tmp'))
        # Make sure the test config directory exists
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)
        # Create an empty file at expected config path
        open(test_config_path, 'a').close()
        # Test to see if correctly return True if file exists
        self.assertTrue(hkg.check_config_exists('/tmp'))
        os.remove(test_config_path)

    def test_can_create_a_default_config(self):
        self.assertTrue(hkg.create_default_config('/tmp'))
        os.remove('/tmp/.config/hkg/settings.conf')

    def test_can_load_config_settings(self):
        hkg.create_default_config('/tmp/')
        hkg_config_data = hkg.load_config('/tmp')
        self.assertIn('SOURCES', hkg_config_data)
        self.assertIn('OPTIONS', hkg_config_data)
        os.remove('/tmp/.config/hkg/settings.conf')

    def test_add_and_remove_remotes(self):

        # Setup
        os.makedirs('/tmp/testhome/.config/hkg', exist_ok=True)

        # Test
        self.assertTrue(hkg.create_default_config('/tmp/testhome'))
        self.assertTrue(hkg.check_config_exists('/tmp/testhome'))
        self.assertTrue(hkg.add_repo('/tmp/testhome', 'http://127.0.0.1/tmp/hkg'))
        self.assertTrue(hkg.del_repo('/tmp/testhome', 'http://127.0.0.1/tmp/hkg'))
        self.assertFalse(hkg.del_repo('/tmp/testhome', 'https://sffennel.desktop.amazon.com/packages'))

        # Cleanup
        os.remove('/tmp/testhome/.config/hkg/settings.conf')
        os.rmdir('/tmp/testhome/.config/hkg')
        os.rmdir('/tmp/testhome/.config')
        os.rmdir('/tmp/testhome')

    def test_list_configured_repos(self):

        self.assertTrue(hkg.list_repo('~'))

    def test_scan_repo_for_new_packages(self):

        # Setup
        os.makedirs('/tmp/testrepo', exist_ok=True)
        hkg.create_repo('/tmp/testrepo')

        # Test
        self.assertTrue(hkg.update_repo('/tmp/testrepo'))

        # Cleanup
        os.remove('/tmp/testrepo/packages.hdb')
        os.rmdir('/tmp/testrepo')

    def test_print_readme(self):

        # Setup
        os.makedirs('/tmp/readmetest/.local/share/hkg/hkg/hkg/lib', exist_ok=True)
        tempwrite = open('/tmp/readmetest/.local/share/hkg/hkg/hkg/lib/readme.md', 'w')
        tempwrite.write('This is a readme file.')
        tempwrite.close()
        tempwrite = open('/tmp/readmetest/.local/share/hkg/packages.hdb', 'w')
        tempwrite.write('[INSTALLED]\nhkg = 0.1\n[AVAILABLE]\n\n')
        tempwrite.close()

        # Test
        self.assertTrue(hkg.print_readme('/tmp/readmetest'))

        # Cleanup
        os.remove('/tmp/readmetest/.local/share/hkg/hkg/hkg/lib/readme.md')
        os.rmdir('/tmp/readmetest/.local/share/hkg/hkg/hkg/lib/')
        os.rmdir('/tmp/readmetest/.local/share/hkg/hkg/hkg/')
        os.rmdir('/tmp/readmetest/.local/share/hkg/hkg/')
        os.remove('/tmp/readmetest/.local/share/hkg/packages.hdb')
        os.rmdir('/tmp/readmetest/.local/share/hkg/')
        os.rmdir('/tmp/readmetest/.local/share/')
        os.rmdir('/tmp/readmetest/.local/')
        os.rmdir('/tmp/readmetest/')


class TestPackaging(unittest.TestCase):

    def test_validate_directory_structure(self):
        # Setup the test directory structure
        os.makedirs('/tmp/testsrc/testsrc/lib', exist_ok=True)
        os.makedirs('/tmp/testsrc/testsrc/etc', exist_ok=True)
        open('/tmp/testsrc/metadata', 'a').close()
        open('/tmp/testsrc/testsrc/program.bin', 'a').close()
        
        # Check simplest possible package is OK
        self.assertTrue(hkg.validate_source_directory('/tmp/testsrc'))

        # Should fail since only metadata file should exist in base dir
        open('/tmp/testsrc/bad.file', 'a').close()
        self.assertFalse(hkg.validate_source_directory('/tmp/testsrc'))
        os.remove('/tmp/testsrc/bad.file')

        # Should fail since only one executable file should exist in source dir
        open('/tmp/testsrc/testsrc/bad.file', 'a').close()
        self.assertFalse(hkg.validate_source_directory('/tmp/testsrc'))
        os.remove('/tmp/testsrc/testsrc/bad.file')

        # Should pass with files in main/src/lib and main/src/etc
        open('/tmp/testsrc/testsrc/lib/stuff.lib', 'a').close()
        open('/tmp/testsrc/testsrc/etc/settings.conf', 'a').close()
        self.assertTrue(hkg.validate_source_directory('/tmp/testsrc'))
        os.remove('/tmp/testsrc/testsrc/lib/stuff.lib')
        os.remove('/tmp/testsrc/testsrc/etc/settings.conf')

        # Should fail since only src dir w/ same name is allowed in main/
        os.makedirs('/tmp/testsrc/stuff', exist_ok=True)
        self.assertFalse(hkg.validate_source_directory('/tmp/testsrc'))
        os.rmdir('/tmp/testsrc/stuff')

        # Should fail since only bin and etc are valid dirs in main/src/
        os.makedirs('/tmp/testsrc/testsrc/stuff', exist_ok=True)
        self.assertFalse(hkg.validate_source_directory('/tmp/testsrc'))
        os.rmdir('/tmp/testsrc/testsrc/stuff')

        # Clean up
        os.remove('/tmp/testsrc/metadata')
        os.remove('/tmp/testsrc/testsrc/program.bin')
        os.rmdir('/tmp/testsrc/testsrc/lib')
        os.rmdir('/tmp/testsrc/testsrc/etc')
        os.rmdir('/tmp/testsrc/testsrc')
        os.rmdir('/tmp/testsrc')

    def test_init_new_package_directory(self):

        # Make sure the function returns True and that each piece of the skeleton is actually created
        self.assertTrue(hkg.init_package_directory('/tmp/test_package'))
        self.assertTrue(os.path.isdir('/tmp/test_package'))
        self.assertTrue(os.path.isdir('/tmp/test_package/test_package'))
        self.assertTrue(os.path.isdir('/tmp/test_package/test_package/etc'))
        self.assertTrue(os.path.isdir('/tmp/test_package/test_package/lib'))
        self.assertTrue(os.path.isfile('/tmp/test_package/metadata'))
        self.assertTrue(os.path.isfile('/tmp/test_package/test_package/your_program.bin'))

        # Cleanup
        os.remove('/tmp/test_package/test_package/your_program.bin')
        os.remove('/tmp/test_package/metadata')
        os.rmdir('/tmp/test_package/test_package/etc')
        os.rmdir('/tmp/test_package/test_package/lib')
        os.rmdir('/tmp/test_package/test_package')
        os.rmdir('/tmp/test_package')

    def test_validate_metadata(self):
        
        # Create the test metadata file.  We'll manually edit the file's contents instead of using configparser.
        testfile = open('/tmp/metadata', 'w')
        testfile.write('[METADATA]\n')
        testfile.write('name = spam\n')
        testfile.write('version = 2.1\n')
        testfile.write('description = An example package\n')
        testfile.write('author_name = Eadrom\n')
        testfile.write('author_email = eadrom@example.com\n')
        testfile.write('website = http://example.com\n')
        testfile.close()

        # Test
        self.assertTrue(hkg.validate_metadata('/tmp/metadata'))

        # Cleanup
        os.remove('/tmp/metadata')

    def test_zip_files_to_disk_as_package(self):
        # Create a fake package
        hkg.init_package_directory('/tmp/sources/ziptest')
        open('/tmp/sources/ziptest/ziptest/lib/functions.so', 'a').close()
        open('/tmp/sources/ziptest/ziptest/etc/settings.conf', 'a').close()

        # Write some text to the files to give them some content
        tempwrite = open('/tmp/sources/ziptest/ziptest/lib/functions.so', 'a')
        for i in range(25):
            tempwrite.write(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(65)) + '\n')
        tempwrite.close()

        tempwrite = open('/tmp/sources/ziptest/ziptest/etc/settings.conf', 'a')
        for i in range(8):
            tempwrite.write(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30)) + '\n')
        tempwrite.close()

        tempwrite = open('/tmp/sources/ziptest/ziptest/your_program.bin', 'a')
        for i in range(200):
            tempwrite.write(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(79)) + '\n')
        tempwrite.close()

        self.assertTrue(hkg.create_package('/tmp/sources/ziptest'))

        # Clean up
        os.remove('/tmp/sources/ziptest/ziptest/your_program.bin')
        os.remove('/tmp/sources/ziptest/metadata')
        os.remove('/tmp/sources/ziptest/ziptest/lib/functions.so')
        os.remove('/tmp/sources/ziptest/ziptest/etc/settings.conf')
        os.rmdir('/tmp/sources/ziptest/ziptest/etc')
        os.rmdir('/tmp/sources/ziptest/ziptest/lib')
        os.rmdir('/tmp/sources/ziptest/ziptest')
        os.rmdir('/tmp/sources/ziptest')
        os.remove('/tmp/sources/ziptest.hkg')
        os.rmdir('/tmp/sources')

    def test_init_package_database(self):

        # Test just providing a target directory.
        self.assertTrue(hkg.init_package_database('/tmp/'))
        self.assertTrue(os.path.isfile('/tmp/packages.hdb'))
        os.remove('/tmp/packages.hdb')

        # Test providing the entire path for the package database.
        self.assertTrue(hkg.init_package_database('/tmp/packages.hdb'))
        self.assertTrue(os.path.isfile('/tmp/packages.hdb'))
        os.remove('/tmp/packages.hdb')

        # Test providing a non correct filename for the package database.
        self.assertTrue(hkg.init_package_database('/tmp/testdb'))
        self.assertTrue(os.path.isfile('/tmp/testdb/packages.hdb'))

        # Make sure contents of skeleton database are correct.
        tempread = open('/tmp/testdb/packages.hdb', 'r')
        self.assertTrue(tempread.read() == '[INSTALLED]\n\n[AVAILABLE]\n')
        tempread.close()
        os.remove('/tmp/testdb/packages.hdb')
        os.rmdir('/tmp/testdb')

    def test_validate_package_database(self):

        # Setup
        if os.path.isfile('/tmp/test.hdb'):
            os.remove('/tmp/test.hdb')
        tempwrite = open('/tmp/test.hdb', 'a')
        tempwrite.write('[INSTALLED]\n')
        tempwrite.write('scripta = 1.1\n')
        tempwrite.write('\n')
        tempwrite.write('[AVAILABLE]\n')
        tempwrite.write('scripta = 1.1\n')
        tempwrite.write('dostuff = 2.4\n')
        tempwrite.close()

        # Test
        self.assertTrue(hkg.validate_package_database('/tmp/test.hdb'))

        # Cleanup
        os.remove('/tmp/test.hdb')

    def test_update_package_database(self):

        # Setup
        if os.path.isfile('/tmp/test.hdb'):
            os.remove('/tmp/test.hdb')
        tempwrite = open('/tmp/test.hdb', 'a')
        tempwrite.write('[INSTALLED]\n')
        tempwrite.write('scripta = 1.1\n')
        tempwrite.write('\n')
        tempwrite.write('[AVAILABLE]\n')
        tempwrite.write('scripta = 1.1\n')
        tempwrite.write('dostuff = 2.4\n')
        tempwrite.close()

        # Test
        self.assertTrue(hkg.package_database_api('/tmp/test.hdb', 'update', 'AVAILABLE', 'scripta', '1.2'))
        self.assertTrue(hkg.package_database_api('/tmp/test.hdb', 'create', 'AVAILABLE', 'scriptz', '2.6'))
        self.assertTrue(hkg.package_database_api('/tmp/test.hdb', 'delete', 'AVAILABLE', 'scripta', '0'))
        self.assertFalse(hkg.package_database_api('/tmp/test.hdb', 'add', 'INSTALLED', 'stuffthing', '1.0'))
        self.assertTrue(hkg.package_database_api('/tmp/test.hdb', 'check', 'INSTALLED', 'scripta', '0'))
        self.assertFalse(hkg.package_database_api('/tmp/test.hdb', 'check', 'INSTALLED', 'blah', '0'))
        self.assertEquals(hkg.package_database_api('/tmp/test.hdb', 'version', 'AVAILABLE', 'dostuff', '0'), '2.4')

        # Cleanup
        os.remove('/tmp/test.hdb')

    def test_create_repository(self):

        # Setup
        os.makedirs('/tmp/testrepo', exist_ok=True)

        # Test
        self.assertTrue(hkg.create_repo('/tmp/testrepo'))
        self.assertTrue(os.path.isfile('/tmp/testrepo/packages.hdb'))
        self.assertTrue(hkg.validate_package_database('/tmp/testrepo/packages.hdb'))

        # Cleanup
        os.remove('/tmp/testrepo/packages.hdb')
        os.rmdir('/tmp/testrepo')


class TestInstallPackage(unittest.TestCase):

    # Might implement hash verification at some point
    def test_validate_package_file(self):
        
        pass

    def test_prep_findpkg_download_extract_makesymlink(self):

        # Test
        self.assertTrue(hkg.install_package('hkghello', ''))
        self.assertTrue(os.path.isfile(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello/hkghello.sh')))
        self.assertTrue(os.path.isdir(os.path.expanduser('~/.cache/hkg')))
        self.assertTrue(os.path.isdir(os.path.expanduser('~/.local/share/hkg')))
        self.assertTrue(os.path.isdir(os.path.expanduser('~/bin')))
        self.assertTrue(os.path.isfile(os.path.expanduser('~/.cache/hkg/hkghello.hkg')))
        self.assertTrue(os.path.isfile(os.path.expanduser('~/bin/hkghello')))
        self.assertFalse(hkg.install_package('hkghello', ''))

        # Cleanup
        os.remove(os.path.expanduser('~/.cache/hkg/hkghello.hkg'))
        os.rmdir(os.path.expanduser('~/.cache/hkg'))
        os.remove(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello/hkghello.sh'))
        os.remove(os.path.expanduser('~/.local/share/hkg/hkghello/metadata'))
        os.remove(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello/etc/settings.conf'))
        os.rmdir(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello/etc'))
        os.rmdir(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello/lib'))
        os.rmdir(os.path.expanduser('~/.local/share/hkg/hkghello/hkghello'))
        os.rmdir(os.path.expanduser('~/.local/share/hkg/hkghello'))
        os.remove(os.path.expanduser('~/.local/share/hkg/packages.hdb'))
        os.rmdir(os.path.expanduser('~/.local/share/hkg'))
        os.remove(os.path.expanduser('~/bin/hkghello'))

    # Could add this functionality so user doesn't have to manually edit .bashrc
    def test_configure_user_home_bin_dir_in_user_path(self):
        
        pass

    # Could test if the new executable that was installed has execute bit set properly for user
    def test_can_properly_run_newly_installed_executable_in_shell(self):
        
        pass


class TestRemovePackage(unittest.TestCase):

    def test_delete_package(self):

        # Setup
        self.assertTrue(hkg.install_package('hkghello', ''))

        # Test and Cleanup
        self.assertTrue(hkg.remove_package('hkghello'))


class TestUpdatePackage(unittest.TestCase):

    def test_update_package(self):

        self.assertTrue(hkg.update_package('all', False))
        pass

    def test_can_download_repo_package_databases(self):
        
        pass

    def test_can_compare_local_and_remote_package_databases(self):
        
        pass

    def test_can_pass_list_of_packages_needing_update_to_install_function(self):
        
        pass


class TestPackageInformation(unittest.TestCase):

    def test_list_packages(self):

        self.assertTrue(hkg.list_packages('http://sffennel.desktop.amazon.com/files/packages/hkg'))
        self.assertTrue(hkg.list_packages('all'))
        # Odd testing situation here
        # HKG works fine if the local package database is empty
        # However, this test errors out (not just fails, but errors out the interpreter) if there are no installed pkgs
        hkg.install_package('hkghello', '')
        self.assertTrue(hkg.list_packages('local'))
        hkg.remove_package('hkghello')
        self.assertFalse(hkg.list_packages('http://127.0.0.1/no/eggs/for/you'))

    def test_show_package_information(self):

        # Test against package in cache
        hkg.install_package('hkghello', '')
        self.assertTrue(hkg.package_info('hkghello'))
        hkg.remove_package('hkghello')

        # Test against package not in cache
        self.assertTrue(hkg.package_info('hkghello'))
        os.remove(os.path.expanduser('~/.cache/hkg/hkghello.hkg'))


if __name__ == '__main__':
    unittest.main()
