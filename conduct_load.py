import conduct
import requests


# `conduct load` command
def load(args):
    url = conduct.url('bundles')
    files = [
        ('nr-of-cpus', str(args.nr_of_cpus)),
        ('memory-space', str(args.memory)),
        ('disk-space', str(args.disk_space)),
        ('roles', ' '.join(args.roles)),
        ('bundle', open(args.bundle, 'rb')),
    ]
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(response.text)
    else:
        conduct.print_error('{} {}', response.status_code, response.reason)
