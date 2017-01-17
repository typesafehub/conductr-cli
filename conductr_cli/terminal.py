import subprocess


def docker_info():
    return subprocess.check_output(['docker', 'info'], stderr=subprocess.DEVNULL).strip()


def docker_images(image):
    return subprocess.check_output(['docker', 'images', '--quiet', image], stderr=subprocess.DEVNULL).strip()


def docker_pull(image):
    return subprocess.call(['docker', 'pull', image])


def docker_ps(ps_filter=None):
    ps_filter_arg = ['--filter', ps_filter] if ps_filter else []
    cmd = ['docker', 'ps', '--all', '--quiet'] + ps_filter_arg
    output = subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.DEVNULL).strip()
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
