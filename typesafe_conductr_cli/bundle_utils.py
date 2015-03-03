def short_id(bundle_id):
    return '-'.join([part[:7] for part in bundle_id.split('-')])
