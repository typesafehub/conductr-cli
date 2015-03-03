from zipfile import ZipFile


def short_id(bundle_id):
    return '-'.join([part[:7] for part in bundle_id.split('-')])


def conf(bundle_path):
    bundle_zip = ZipFile(bundle_path)
    bundleConf = [bundle_zip.read(name) for name in bundle_zip.namelist() if name.endswith('bundle.conf')]
    return bundleConf[0].decode('utf-8') if len(bundleConf) == 1 else ''
