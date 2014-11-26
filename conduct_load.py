import conduct_util
import requests


# `conduct load` command
def load(args):
    url = conduct_util.url('bundles')
    files = [
        ('nrOfCpus', str(args.nr_of_cpus)),
        ('memory', str(args.memory)),
        ('diskSpace', str(args.disk_space)),
        ('roles', ' '.join(args.roles)),
        ('bundle', open(args.bundle, 'rb'))
    ]
    if vars(args).get('configuration'):
        files.append(('configuration', open(args.configuration, 'rb')))
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(response.text)
    else:
        conduct_util.print_error('{} {}', response.status_code, response.reason)
