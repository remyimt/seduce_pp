import logging


user_initial_state = 'user_created'

# Add the environment names to the 'environments' array to limit the process to specific environments
process = {
    'deploy': [
        {
            'environments': [],
            'states': [
                'boot_conf', 'turn_off', 'turn_on', 'ssh_nfs', 'env_copy', 'env_check', 
                'delete_partition', 'create_partition', 'mount_partition', 'resize_partition',
                'wait_resizing', 'system_conf', 'boot_files', 'ssh_system', 'system_update',
                'boot_update', 'user_conf', 'user_script', 'deployed'
            ]
        }
    ],
    'destroy': [
        {
            'environments': [],
            'states': [
                'destroying', 'turn_off', 'destroyed'
            ]
        }
    ],
    'reboot': [
        {
            'environments': [],
            'states': [
                'turn_off', 'turn_on', 'coming_back'
            ]
        }
    ],
    'boot_test': [
        {
            'environments': [],
            'states': [
                'boot_conf', 'turn_off', 'turn_on', 'ssh_nfs', 'booted'
            ]
        }
    ],
    'save_env': [
        {
            'environments': [],
            'states': [
                'img_part', 'img_format', 'img_copy', 'img_copy_check', 'img_customize',
                'img_compress', 'img_compress_check', 'upload', 'upload_check', 'deployed'
            ]
        }
    ]
}


# State names must NOT include '_exec' or '_post'
# 'lost' timeouts must be greater then 'before_reboot' timeouts
# 0: infinite timeouts
# The states must be ordered according to the process values
state_desc = {
    'boot_conf': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'turn_off': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'turn_on': { 'exec': True, 'post': True, 'before_reboot': 60, 'lost': 90 },
    'ssh_nfs': { 'exec': False, 'post': True, 'before_reboot': 45, 'lost': 60 },
    'env_copy': { 'exec': True, 'post': True, 'before_reboot': 0, 'lost': 30 },
    'env_check': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 400 },
    'delete_partition': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 45 },
    'create_partition': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 45 },
    'mount_partition': { 'exec': True, 'post': True, 'before_reboot': 0, 'lost': 30 },
    'resize_partition': { 'exec': True, 'post': True, 'before_reboot': 0, 'lost': 30 },
    'wait_resizing': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 90 },
    'system_conf': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'boot_files': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'ssh_system': { 'exec': False, 'post': True, 'before_reboot': 150, 'lost': 180 },
    'system_update': { 'exec': True, 'post': True, 'before_reboot': 0, 'lost': 0 },
    'boot_update': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'user_conf': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 60 },
    'user_script': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'deployed': { 'exec': False, 'post': False, 'before_reboot': 0, 'lost': 0 },

    'coming_back': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 60 },

    'destroying': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 30 },
    'destroyed': { 'exec': False, 'post': False, 'before_reboot': 0, 'lost': 0 },

    'booted': { 'exec': False, 'post': False, 'before_reboot': 0, 'lost': 0 },

    'img_part': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_format': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_copy': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_copy_check': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_customize': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_compress': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'img_compress_check': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'upload': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 },
    'upload_check': { 'exec': True, 'post': False, 'before_reboot': 0, 'lost': 0 }
}

# Get the process from a state name
def get_process_from_state(state_name, env_name):
    for process_name in process:
        for states in process[process_name]:
            if state_name in states["states"] and (
                    len(states["environments"]) == 0 or env_name in states["environments"]):
                return process_name
    return ""

# Select the right list of process states
def select_process(process_name, env_name):
    if process_name in process:
        for p in process[process_name]:
            if len(p['environments']) == 0 or env_name in p['environments']:
                return p['states']
    return []


# Return True if SSH connections must use the 'ssh_user' property defined in the environment description
def use_env_ssh_user(dep_state):
    try:
        last_nfs_state = process['deployment'].index('system_conf')
        dep_idx = process['deployment'].index(dep_state)
        return dep_idx > last_nfs_state
    except:
        return True
