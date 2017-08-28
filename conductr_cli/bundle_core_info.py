import datetime

from conductr_cli.conduct_info_inspect import has_bundle_id, has_bundle_name


class BundleCoreInfo(object):
    def __init__(self, bundle_id, bundle_name, bundle_digest, configuration_digest,
                 scale=0, start_time=datetime.datetime.max, compatibility_version=None):
        self.bundle_id = bundle_id
        self.bundle_name = bundle_name
        self.bundle_digest = bundle_digest
        self.configuration_digest = configuration_digest
        self.bundle_name_with_digest = '{0}-{1}'.format(bundle_name, bundle_digest)
        self.bundle_name_with_configuration_digest = '{0}-{1}'.format(bundle_name, configuration_digest)
        self.scale = scale
        self.start_time = start_time
        self.compatibility_Version = compatibility_version

    @classmethod
    def from_bundles(cls, bundles_json):
        def get_start_time(bundle):
            default_start_time = datetime.datetime.max
            if bundle.get('bundleExecutions') is None:
                default_start_time = default_start_time
            if len(bundle['bundleExecutions']) > 0:
                start = (bundle['bundleExecutions'])[0].get('startTime', None)
                if start is not None:
                    default_start_time = datetime.datetime.strptime(start.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            return default_start_time

        return list(map(
            lambda b: cls(bundle_id=b['bundleId'],
                          bundle_digest=b['bundleDigest'],
                          configuration_digest=b.get('configurationDigest', ''),
                          bundle_name=b['attributes']['bundleName'],
                          scale=b['bundleScale']['scale'] if b.get('bundleScale', None) is not None else 0,
                          compatibility_version=b['attributes']['compatibilityVersion'],
                          start_time=get_start_time(b)
                          ),
            bundles_json))

    @classmethod
    def filter_by_bundle_id(cls, bundle_core_info, bundle_id):
        for bundle_info in bundle_core_info:
            if has_bundle_id(bundle_info.bundle_id, bundle_id) or has_bundle_name(bundle_info.bundle_name, bundle_id):
                return bundle_info
        return None

    @staticmethod
    def diff(this, that):
        return set(this) - set(that)

    def __str__(self) -> str:
        return '{0} - {1}'.format(self.bundle_id, self.bundle_name)

    def __repr__(self):
        return '(%s)' % self.bundle_id

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__repr__())
