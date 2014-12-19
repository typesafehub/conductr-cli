import conduct_logging
import conduct_url
import requests


# `conduct load` command
def load(args):
    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', str(args.nr_of_cpus)),
        ('memory', str(args.memory)),
        ('diskSpace', str(args.disk_space)),
        ('roles', ' '.join(args.roles)),
        ('bundle', open(args.bundle, 'rb'))
    ]
    if args.configuration is not None:
        files.append(('configuration', open(args.configuration, 'rb')))
    response = requests.post(url, files=files)
    if response.status_code == 200:
        conduct_logging.pretty_json(response.text)
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
