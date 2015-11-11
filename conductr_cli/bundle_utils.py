from zipfile import ZipFile


def short_id(bundle_id):
    return '-'.join([part[:7] for part in bundle_id.split('-')])


def conf(bundle_path):
    bundle_zip = ZipFile(bundle_path)
    bundle_configuration = [bundle_zip.read(name) for name in bundle_zip.namelist() if name.endswith('bundle.conf')]
    return bundle_configuration[0].decode('utf-8') if len(bundle_configuration) == 1 else ''


def zip_entry(entry_name, zip_file_path):
    zip_file = ZipFile(zip_file_path)
    entries = [entry for entry in zip_file.infolist() if entry.filename.endswith(entry_name)]
    if entries:
        return zip_file.open(entries[0])
    else:
        return None
