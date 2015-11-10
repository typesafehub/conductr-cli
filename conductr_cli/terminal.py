import subprocess


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


def boot2docker_shellinit():
    cmd = ['boot2docker', 'shellinit']
    output = subprocess.check_output(cmd, universal_newlines=True)
    return [line.strip() for line in output.splitlines()]


def boot2docker_ip():
    cmd = ['boot2docker', 'ip']
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def hostname():
    return subprocess.check_output(['hostname'], universal_newlines=True).strip()
