import subprocess
import itertools
import sys

from scripts import common

# Stacks:
ALL = (
    'overlay',  # order important!
    'traefik',
    'keycloak',
    'bazarr',
    'deluge',
    'hydra',
    'lidarr',
    'organizr',
    'pihole',
    'plex',
    'portainer',
    'radarr',
    'sabnzbd',
    'sonarr',
    'tdarr',
    'mylar'
)
ENCODING = 'utf-8'


def list_from_stdout(reply, first_column_name):
    iterator = iter(str.splitlines(reply.stdout))
    for line in iterator:
        if line.startswith(first_column_name):
            break
    else:
        raise RuntimeError(f'Did not catch first column name {first_column_name}')
    column_names = [x.lower() for x in line.split()]
    answ = []
    for line in iterator:
        answ.append(dict(itertools.zip_longest(column_names,
                                              line.split(),
                                              fillvalue=None)))
    return answ


def easyprint(rep):
    sys.stdout.write(rep.stdout)
    if rep.stderr:
        sys.stdout.write(rep.stderr)


def clear_screen():
    subprocess.run(['clear'])


def wait_for_user():
    input('\nPress any key to continue\n')


def list_to_dict(stacklist):
    return {entry['name']: entry for entry in stacklist}


def currently_running_stacks(print_to_stdout=True):
    rep = subprocess.run(['docker', 'stack', 'ls'],
                         capture_output=True,
                         encoding=ENCODING)
    if print_to_stdout:
        print('Currently running stacks:')
        easyprint(rep)
    answ = list_from_stdout(rep, 'NAME')
    return list_to_dict(answ)


def update_stacks(stacks):
    for stack in stacks:
        if stack == 'overlay':
            continue
        rep = subprocess.run(['docker-compose', '-f', f'{stack}.yml', 'pull'],
                             capture_output=True,
                             encoding=ENCODING)
        easyprint(rep)
        rep = subprocess.run(['docker', 'stack', 'deploy', '-c', f'{stack}.yml', stack],
                             capture_output=True,
                             encoding=ENCODING)
        easyprint(rep)
    wait_for_user()


def process_stack(relevant_stacks, action, commands):
    clear_screen()
    for i, stack in enumerate(relevant_stacks):
        print(f'{i}) {stack}')
    user = input(f'\nWhich stack do you want to {action}? (q to quit)\n')
    try:
        user = int(user)
    except ValueError:
        return
    for i, stack in enumerate(relevant_stacks):
        if i == user:
            break
    else:
        return
    for i, command in enumerate(commands):
        rep = subprocess.run([x.format(stack=stack) for x in command],
                             capture_output=True,
                             encoding=ENCODING)
        easyprint(rep)
    wait_for_user()
    return currently_running_stacks(print_to_stdout=False)


def start_stack(stacks):
    stacks = process_stack([stack for stack in ALL if stack not in stacks],
                           'start',
                           [('docker', 'stack', 'deploy', '-c', '{stack}.yml', '{stack}')])
    if stacks is None:
        return
    start_stack(stacks)


def stop_stack(stacks):
    stacks = process_stack([stack for stack in ALL if stack in stacks],
                           'stop',
                           [('docker', 'stack', 'rm', '{stack}')])
    if stacks is None:
        return
    stop_stack(stacks)


def update_stack(stacks):
    stacks = process_stack([stack for stack in ALL if stack in stacks],
                           'update',
                           [('docker-compose', '-f', '{stack}.yml', 'pull'),
                            ('docker', 'stack', 'deploy', '-c', '{stack}.yml', '{stack}')])
    if stacks is None:
        return
    update_stack(stacks)


def check_service_health():
    rep = subprocess.run(['docker', 'service', 'ls'],
                         capture_output=True,
                         encoding=ENCODING)
    easyprint(rep)
    wait_for_user()


def menu():
    while True:
        clear_screen()
        stacks = currently_running_stacks()
        print('\n')
        print('What do you want to do?')
        print('#######################')
        print('0) Check service health')
        print('1) Upgrade all stacks')
        print('2) Start stack')
        print('3) Remove stack')
        print('4) Upgrade stack')
        print('5) Exit')
        user = input('\n')
        if user == '0':
            check_service_health()
        elif user == '1':
            update_stacks(stacks)
        elif user == '2':
            start_stack(stacks)
        elif user == '3':
            stop_stack(stacks)
        elif user == '4':
            update_stack(stacks)
        elif user == '5':
            break


def main():
    common.sanity_checks()
    menu()


if __name__ == '__main__':
    main()
