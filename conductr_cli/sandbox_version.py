
def is_sandbox_docker_based(version):
    return major_version(version) == 1


def is_conductr_on_private_bintray(version):
    major, minor, _ = version_parts(version)
    return major == 1 or (major == 2 and minor == 0)


def is_conductr_supportive_of_features(version):
    return major_version(version) != 1


def is_cinnamon_grafana_docker_based(version):
    return major_version(version) != 1


def version_parts(version):
    return tuple(map(int, version.split('-')[0].split('.')))


def major_version(version):
    return version_parts(version)[0]
