import subprocess


def docker_version():
    cmd = ['docker', '--version']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    if output:
        full_version = output.split('Docker version ')[1].split(',')[0]
        return float('.'.join(full_version.split('.', 2)[:2]))   # Version format: 1.23
    else:
        None


def docker_images(image):
    return subprocess.check_output(['docker', 'images', '--quiet', image]).strip()


def docker_pull(image):
    return subprocess.call(['docker', 'pull', image])


def docker_ps(ps_filter=None):
    ps_filter_arg = ['--filter', ps_filter] if ps_filter else []
    cmd = ['docker', 'ps', '--quiet'] + ps_filter_arg
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output.splitlines()


def docker_inspect(container_id, inspect_format=None):
    format_arg = ['--format', inspect_format] if inspect_format else []
    cmd = ['docker', 'inspect'] + format_arg + [container_id]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_run(optional_args, image, positional_args):
    cmd = ['docker', 'run'] + optional_args + [image] + positional_args
    return subprocess.call(cmd)


def docker_rm(containers):
    return subprocess.call(['docker', 'rm', '-f'] + containers)


def docker_machine_env(vm_name):
    cmd = ['docker-machine', 'env', vm_name]
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output.splitlines()


def docker_machine_ip(vm_name):
    cmd = ['docker-machine', 'ip', vm_name]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_machine_status(vm_name):
    cmd = ['docker-machine', 'status', vm_name]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_machine_create_vm(vm_name):
    cmd = ['docker-machine', 'create', vm_name, '-d', 'virtualbox']
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_machine_start_vm(vm_name):
    cmd = ['docker-machine', 'start', vm_name]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_machine_stop_vm(vm_name):
    cmd = ['docker-machine', 'stop', vm_name]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def docker_machine_help():
    cmd = ['docker-machine', 'help']
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def vbox_manage_increase_ram(vm_name, ram_size):
    cmd = ['VBoxManage', 'modifyvm', vm_name, '--memory', ram_size]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def vbox_manage_get_ram_size(vm_name):
    ram_value = vbox_manage_get_info(vm_name, 'Memory size')
    return int(ram_value.replace('MB', ''))


def vbox_manage_increase_cpu(vm_name, no_of_cpu):
    cmd = ['VBoxManage', 'modifyvm', vm_name, '--cpus', no_of_cpu]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def vbox_manage_get_cpu_count(vm_name):
    no_of_cpu = vbox_manage_get_info(vm_name, 'Number of CPUs')
    return int(no_of_cpu)


def vbox_manage_get_info(vm_name, vm_property):
    cmd = ['VBoxManage', 'showvminfo', vm_name]
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    matching_lines = [line for line in output.split('\n') if line.startswith('{}:'.format(vm_property))]
    if matching_lines:
        key, value = matching_lines[0].split(':')
        return value.strip()
    else:
        return None


def hostname():
    return subprocess.check_output(['hostname'], universal_newlines=True).strip()
