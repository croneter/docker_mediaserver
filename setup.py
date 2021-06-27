# -*- coding: utf-8 -*-
import sys
import os
import copy
import re
import errno

from scripts import common

ENCODING = 'utf-8'
# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123


# If your environment variables don't stick after re-login or reboot, you
# might need to change the file '.bashrc'
BASH_FILE = os.path.join(os.environ['HOME'], '.bashrc')

CONFIG_SUBFOLDERS = (
    'letsencrypt',
    'keycloak_db',
    'organizr',
    'bazarr',
    'deluge',
    'hydra2',
    'lidarr',
    'pihole/log',
    'pihole/etc/dnsmasq.d',
    'plex',
    'portainer',
    'radarr',
    'sabnzbd',
    'sonarr',
    'tdarr',
    'makemkv'
)
DOWNLOAD_SUBFOLDERS = (
    'complete',
    'incomplete',
    'watch'
)

VAR_LIST = {
    'TZ': None,
    'PUID': None,
    'GROUP_ID_DOWNLOADERS': None,
    'HTPC_DOMAIN': None,
    'HTPC_LETSENCRYPT_EMAIL': None,
    'HTPC_KEYCLOAK_REALM': None,
    # Paths
    'HTPC_CONFIG_DIR': None,
    'HTPC_COMPLETED_DIR': None,
    'HTPC_INCOMPLETE_DIR': None,
    'HTPC_WATCH_DIR': None,
    'HTPC_MOVIE_DIR': None,
    'HTPC_SHOW_DIR': None,
    'HTPC_MUSIC_DIR': None,
    'HTPC_PICTURE_DIR': None,
    # Ports
    'HTPC_PLEX_ADVERTISE_PORT': None,
    'HTPC_DELUGE_DOWNLOAD_PORT': None
}
START_LINE = '# start docker_mediaserver variables\n'
END_LINE = '# end docker_mediaserver variables\n'
EXPORT_PREFIX = 'export '


def is_valid_email(email):
    return re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$',
                     email) is not None


def is_valid_domain(domain):
    try:
        return re.search(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]',
                         domain)[0] == domain
    except TypeError:
        return False


def is_valid_port(port):
    try:
        if not 1 <= int(port) <= 65535:
            raise ValueError
    except ValueError:
        return False
    else:
        return True


def is_pathname_valid(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    '''
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    #
    # Did we mention this should be shipped with Python already?


def is_path_creatable(pathname: str) -> bool:
    '''
    `True` if the current user has sufficient permissions to create the passed
    pathname; `False` otherwise.
    '''
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dirname = os.path.dirname(pathname) or os.getcwd()
    return os.access(dirname, os.W_OK)


def is_path_exists_or_creatable(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname for the current OS _and_
    either currently exists or is hypothetically creatable; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    '''
    try:
        # To prevent "os" module calls from raising undesirable exceptions on
        # invalid pathnames, is_pathname_valid() is explicitly called first.
        return is_pathname_valid(pathname) and (
            os.path.exists(pathname) or is_path_creatable(pathname))
    # Report failure on non-fatal filesystem complaints (e.g., connection
    # timeouts, permissions issues) implying this path to be inaccessible. All
    # other exceptions are unrelated fatal issues and should not be caught here.
    except OSError:
        return False


def _get_user_value(key):
    while True:
        value = input(f'Enter {key}: ').strip()
        if key.endswith('_DIR'):
            if is_path_exists_or_creatable(value):
                break
            print(f'Not a valid path name: {value}')
        elif key in ('HTPC_PLEX_ADVERTISE_PORT', 'HTPC_DELUGE_DOWNLOAD_PORT'):
            if is_valid_port(value):
                break
            else:
                print(f'Not a valid port: {value}')
        elif key == 'HTPC_LETSENCRYPT_EMAIL':
            if is_valid_email(value):
                break
            else:
                print(f'Not a valid email address: {value}')
        elif key == 'HTPC_DOMAIN':
            if is_valid_domain(value):
                break
            else:
                print (f'Not a valid domain (dont enter http): {value}')
        else:
            break
    return value


def reset_some_values(var_list):
    new_var_list = copy.deepcopy(var_list)
    for key, value in var_list.items():
        if input(f'{key}={value}\nEdit this value? (y/n) ').strip() == 'y':
            new_var_list[key] = _get_user_value(key)
        print('\n')
    return new_var_list


def key_value_generator(f):
    """
    Yields the tuples (key, value) for a file-like object f
    """
    for line in f:
        if line == START_LINE:
            break
    else:
        return
    for line in f:
        if line == END_LINE:
            break
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = line.replace(EXPORT_PREFIX, '', 1)
        yield line.split('=', 1)


def get_var_list_from_file():
    var_list = copy.deepcopy(VAR_LIST)
    if os.path.isfile(BASH_FILE):
        print(f'Getting variables from environment file {BASH_FILE}')
        with open(BASH_FILE, 'r') as f:
            for key, value in key_value_generator(f):
                var_list[key] = value
        # Check if we got a setting TOO MUCH from the file
        obsolete_keys = []
        for key, value in var_list.items():
            if key not in VAR_LIST:
                print(f'Found an old, obsolete setting {key}:{value}')
                obsolete_keys.append(key)
        for key in obsolete_keys:
            del var_list[key]
    else:
        print(f'No environment variables saved yet in bash file {BASH_FILE}')
    # Check whether we need to get an ADDITIONAL setting from the user because
    # it was NOT in the file
    for key, value in var_list.items():
        if value is None:
            print(f'Found a new setting {key}')
            var_list[key] = _get_user_value(key)
    return var_list


def delete_old_environment_vars():
    """
    Cleans out any entries that we already wrote to our bash file
    """
    print(f'Removing old entries from the bash file {BASH_FILE}')
    with open(BASH_FILE, 'r+') as f:
        new_f = f.readlines()
        new_f = iter(new_f)
        f.seek(0)
        for line in new_f:
            if line == START_LINE:
                while line != END_LINE:
                    line = next(new_f)
            else:
                f.write(line)
        f.truncate()


def write_env_vars_to_disk(var_list):
    if os.path.exists(BASH_FILE):
        delete_old_environment_vars()
    print(f'Writing environment variables to {BASH_FILE}')
    with open(BASH_FILE, 'a') as f:
        f.write('\n')
        f.write(START_LINE)
        for key, value in var_list.items():
            f.write(f'{EXPORT_PREFIX}{key}={value}\n')
        f.write(END_LINE)
    print(f'Wrote environment variables to {BASH_FILE}')


def create_subfolders_if_not_exist(folder, subfolders):
    for subfolder in subfolders:
        path = os.path.join(folder, subfolder)
        try:
            os.makedirs(path)
            print(f'Created folder {path}')
        except FileExistsError:
            print(f'Folder {path} exists already')


def create_files_if_not_exist(folder, files):
    for file in files:
        path = os.path.join(folder, file)
        if os.path.isfile(path):
            print(f'File already exists: {path}')
            continue
        try:
            open(path, 'a').close()
            print(f'Created file {path}')
        except PermissionError:
            print(f'WARNING: no permission to create file {path}')
            print('You need to create that file yourself!')


def create_files_and_folders(var_list):
    """
    Creates all necessary files and folders for the HTPC
    """
    # Main folders
    for key, folder in var_list.items():
        if not key.endswith('_DIR'):
            continue
        try:
            os.makedirs(folder)
            print(f'Created folder {folder}')
        except FileExistsError:
            print(f'Folder {folder} exists already')
        except PermissionError:
            print(f'WARNING: no permission to create folder {folder}')
            print('You need to create that folder yourself!')
    # create necessary subfolders
    create_subfolders_if_not_exist(var_list['HTPC_CONFIG_DIR'],
                                   CONFIG_SUBFOLDERS)

    # Create all (empty) files if necessary
    # If Docker does not find a mounted file (not folder), a FOLDER is created
    create_files_if_not_exist(var_list['HTPC_CONFIG_DIR'],
                              ['pihole/log/pihole.log'])


def print_var_list(var_list):
    print('\n')
    print('Your environment variables are:')
    print('###############################')
    for key, value in var_list.items():
        print(f'{key}={value}')
    print('###############################')
    print('\n')


def main():
    common.sanity_checks()
    var_list = get_var_list_from_file()
    print_var_list(var_list)
    if input('Would you like to re-set some environment variables?'
             ' (y/n) ').strip() == 'y':
        var_list = reset_some_values(var_list)
    create_files_and_folders(var_list)
    write_env_vars_to_disk(var_list)
    print('Done!')
    print('Be sure to relogin for all changes to take effect!!')


if __name__ == '__main__':
    main()
