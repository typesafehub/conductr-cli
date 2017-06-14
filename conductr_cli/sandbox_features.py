"""Sandbox features.

Features are specified on the command line with `-f/--feature NAME [ ARGS ... ]`.

Any feature arguments will be passed to the feature class constructor.

Feature attributes:
    name (str): Feature name used for command line argument.
    ports (list of int): Docker port mappings for the feature.
    dependencies (list of str): Names of other features that should also be enabled.
    provides (list of str): Names of functionality that is provided, e.g. 'proxying' or 'logging'
    conductr_feature_envs (list of str): Feature names to pass when ConductR is started in Docker.
    conductr_args (list of str): Args that should be added during ConductR start.
    conductr_roles (list of str): Roles that should be added during ConductR start.
    start (method): Start the feature as needed. Called after the sandbox has started.
    conductr_pre_core_start (method): Hook that is called before cores are started
    conductr_core_envs (method): Hook that is called to set env vars for core processes
    conductr_pre_agent_start (method): Hook that is called before agents are started
    conductr_agent_envs (method): Hook that is called to set env vars for agent processes
    conductr_post_start (method): Hook that is called after ConductR has started
"""

import conductr_cli
from conductr_cli import docker, host, sandbox_proxy, terminal
from conductr_cli.sandbox_version import is_conductr_supportive_of_features, is_cinnamon_grafana_docker_based
from conductr_cli.constants import FEATURE_PROVIDE_LOGGING, FEATURE_PROVIDE_PROXYING
from conductr_cli.screen_utils import h1
from zipfile import ZipFile
import logging
import os


class FeatureStartResult:
    def __init__(self, started, bundle_results):
        self.started = started
        self.bundle_results = bundle_results


class BundleStartResult:
    def __init__(self, name, port):
        self.name = name
        self.port = port


class ProxyingFeature:
    """Proxying feature.

    On start, the proxying features will be run.
    """

    name = 'proxying'
    ports = []
    dependencies = []
    provides = [FEATURE_PROVIDE_PROXYING]

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode
        self.host = None
        self.proxy_bind_addr = None
        self.bundle_http_port = None
        self.proxy_ports = None

    def enabled(self):
        return is_conductr_supportive_of_features(self.image_version)

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        if self.enabled():
            self.proxy_bind_addr = core_addrs[0]

    def conductr_agent_envs(self):
        if self.enabled() and docker.is_docker_present() and self.proxy_bind_addr is not None:
            return ['HAPROXY_STATS_IP={}'.format(self.proxy_bind_addr)]
        else:
            return []

    def conductr_post_start(self, args, run_result):
        if self.enabled():
            self.host = run_result.host
            self.bundle_http_port = args.bundle_http_port
            self.proxy_ports = sorted(args.ports)

    @staticmethod
    def conductr_args():
        return []

    def conductr_feature_envs(self):
        return []

    def conductr_roles(self):
        if self.enabled():
            return ['haproxy']
        else:
            return []

    def start(self):
        if not self.enabled() or None in [self.host, self.proxy_bind_addr, self.bundle_http_port, self.proxy_ports]:
            return FeatureStartResult(False, [])
        else:
            started = sandbox_proxy.start_proxy(proxy_bind_addr=self.proxy_bind_addr,
                                                bundle_http_port=self.bundle_http_port,
                                                proxy_ports=self.proxy_ports,
                                                all_feature_ports=all_feature_ports())
            return FeatureStartResult(started, [])

    @staticmethod
    def stop():
        return sandbox_proxy.stop_proxy()


class OciInDockerFeature:
    """OciInDocker feature.

    When enabled, this feature will ensure ConductR runs OCI bundles inside of docker. It will also preload the
    image that ConductR uses for this.
    """

    name = 'oci-in-docker'
    ports = []
    dependencies = []
    provides = []

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode
        self.enabled = is_conductr_supportive_of_features(self.image_version)
        self.docker_present = docker.is_docker_present()
        self.image_name = None

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        self.image_name = self.extract_image_name(dir)

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    def conductr_args(self):
        return [] if not self.docker_present or not self.enabled or self.image_name is None else [
            '-Dconductr.agent.run.force-oci-docker=on'
        ]

    def conductr_feature_envs(self):
        return []

    def conductr_roles(self):
        return []

    def start(self):
        log = logging.getLogger(__name__)

        if self.enabled and self.image_name is not None:
            if self.docker_present:
                log.info(h1('Starting OCI-in-Docker support'))
                docker_image = terminal.docker_images(self.image_name)

                if not docker_image:
                    log.info('Pulling docker image {}'.format(self.image_name))
                    terminal.docker_pull(self.image_name)

                log.info('OCI-in-Docker provided by image {}'.format(self.image_name))

                return FeatureStartResult(True, [])
            else:
                log.info(h1('OCI-in-Docker support unavailable.'))
                log.info(h1('To provide support ensure Docker is running and restart the sandbox'))

                return FeatureStartResult(False, [])
        else:
            return FeatureStartResult(False, [])

    @staticmethod
    def stop():
        return True

    @staticmethod
    def extract_image_name(dir):
        for file in os.listdir(dir):
            if file.startswith('conductr-agent') and file.endswith('.jar'):
                try:
                    with ZipFile(os.path.join(dir, file), 'r') as jar:
                        conf = jar.read('application.conf').decode('UTF-8')

                        # pyhocon can't parse application.conf due to variable substitutions so we manually
                        # pull out the oci-docker-image line

                        for l in map(lambda l: l.strip(), conf.splitlines()):
                            if l.startswith('oci-docker-image'):
                                image_name = l[l.index('"') + 1:l.rindex('"')]
                                if image_name != "":
                                    return image_name
                finally:
                    pass
        return None


class VisualizationFeature:
    """Visualization feature.

    On start, the visualizer bundle will be run. The version of the visualizer
    bundle can also be configured using feature arguments. For example:

        `-f visualization`: default latest version of the Visualizer bundle
        `-f visualization v2`: specify a tag
    """

    name = 'visualization'
    ports = [9999]
    dependencies = []
    provides = []

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        pass

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    def conductr_feature_envs(self):
        if is_conductr_supportive_of_features(self.image_version):
            return []
        else:
            return [self.name]

    @staticmethod
    def conductr_args():
        return []

    @staticmethod
    def conductr_roles():
        return []

    def start(self):
        if is_conductr_supportive_of_features(self.image_version):
            log = logging.getLogger(__name__)
            log.info(h1('Starting visualization feature'))
            visualizer = select_bintray_uri('visualizer', self.version_args)
            log.info('Deploying bundle %s..' % visualizer['bundle'])
            load_command = ['load', visualizer['bundle'], '--disable-instructions'] + \
                parse_offline_mode_arg(self.offline_mode)
            conductr_cli.conduct_main.run(load_command, configure_logging=False)
            conductr_cli.conduct_main.run(['run', visualizer['name'], '--disable-instructions'],
                                          configure_logging=False)
            return FeatureStartResult(True, [BundleStartResult('visualizer', self.ports[0])])
        else:
            return FeatureStartResult(False, [])

    @staticmethod
    def stop():
        return True


class LoggingFeature:
    """Logging feature.

    On start, the conductr-elasticsearch and conductr-kibana bundles are started.
    The version of the bundles can also be configured using feature arguments. For example:

        `-f logging`: default latest version of the Visualizer bundle
        `-f logging v2`: specify the compatibility version
    """

    name = 'logging'
    ports = [5601, 9200]
    dependencies = []
    provides = [FEATURE_PROVIDE_LOGGING]

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        pass

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    def conductr_feature_envs(self):
        if is_conductr_supportive_of_features(self.image_version):
            return []
        else:
            return [self.name]

    def conductr_args(self):
        if is_conductr_supportive_of_features(self.image_version):
            return ['-Dcontrail.syslog.server.port=9200', '-Dcontrail.syslog.server.elasticsearch.enabled=on']
        else:
            return []

    def conductr_roles(self):
        if is_conductr_supportive_of_features(self.image_version):
            return ['elasticsearch', 'kibana']
        else:
            return []

    def start(self):
        if is_conductr_supportive_of_features(self.image_version):
            log = logging.getLogger(__name__)
            log.info(h1('Starting logging feature based on elasticsearch and kibana'))
            log.info('conductr-kibana bundle is packaged as a Docker image. Checking Docker requirements..')
            docker.validate_docker_vm(docker.vm_type())
            log.info('Docker is installed and configured correctly.')
            elasticsearch = select_bintray_uri('conductr-elasticsearch', self.version_args)
            log.info('Deploying bundle %s..' % elasticsearch['bundle'])
            elasticsearch_load_command = ['load', elasticsearch['bundle'], '--disable-instructions'] + \
                parse_offline_mode_arg(self.offline_mode)
            conductr_cli.conduct_main.run(elasticsearch_load_command, configure_logging=False)
            conductr_cli.conduct_main.run(['run', elasticsearch['name'], '--disable-instructions'],
                                          configure_logging=False)
            kibana = select_bintray_uri('conductr-kibana', self.version_args)
            log.info('Deploying bundle %s..' % kibana['bundle'])
            kibana_load_command = ['load', kibana['bundle'], '--disable-instructions'] + \
                parse_offline_mode_arg(self.offline_mode)
            conductr_cli.conduct_main.run(kibana_load_command, configure_logging=False)
            conductr_cli.conduct_main.run(['run', kibana['name'], '--disable-instructions', '--wait-timeout', '600'],
                                          configure_logging=False)
            return FeatureStartResult(True, [
                BundleStartResult('conductr-kibana', self.ports[0]),
                BundleStartResult('conductr-elasticsearch', self.ports[1])
            ])
        else:
            return FeatureStartResult(False, [])

    @staticmethod
    def stop():
        return True


class LiteLoggingFeature:
    """Lite logging feature.

    On start, the latest eslite bundle is started
    """

    name = 'lite-logging'
    ports = []
    dependencies = []
    provides = [FEATURE_PROVIDE_LOGGING]

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        pass

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    @staticmethod
    def conductr_feature_envs():
        return []

    def conductr_args(self):
        if is_conductr_supportive_of_features(self.image_version):
            return ['-Dcontrail.syslog.server.port=9200', '-Dcontrail.syslog.server.elasticsearch.enabled=on']
        else:
            return []

    def conductr_roles(self):
        if is_conductr_supportive_of_features(self.image_version):
            return ['elasticsearch']
        else:
            return []

    def start(self):
        if is_conductr_supportive_of_features(self.image_version):
            log = logging.getLogger(__name__)
            log.info(h1('Starting logging feature based on eslite'))
            eslite = select_bintray_uri('eslite', self.version_args)
            log.info('Deploying bundle %s..' % eslite['bundle'])
            load_command = ['load', eslite['bundle'], '--disable-instructions'] + \
                parse_offline_mode_arg(self.offline_mode)
            conductr_cli.conduct_main.run(load_command, configure_logging=False)
            conductr_cli.conduct_main.run(['run', eslite['name'], '--disable-instructions'], configure_logging=False)
            return FeatureStartResult(True, [])
        else:
            return FeatureStartResult(False, [])

    @staticmethod
    def stop():
        return True


class MonitoringFeature:
    """Monitoring feature.

    The monitoring feature depends on the logging feature.

    On start, a Grafana bundle will be run. The version of the Grafana
    bundle can also be configured using feature arguments. For example:

        `-f monitoring`: default latest version of the Grafana bundle
        `-f monitoring v2`: specify the compatibility version
        `-f monitoring 2.1.0`: specify the full Cinnamon version
        `-f monitoring snapshot 2.1.0-20161018-43bab24`: specify a snapshot version
    """

    name = 'monitoring'
    ports = [3000]
    conductr_args = []
    conductr_roles = []
    dependencies = [LoggingFeature.name]
    provides = []

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        pass

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    @staticmethod
    def conductr_feature_envs():
        return []

    @staticmethod
    def conductr_args():
        return []

    @staticmethod
    def conductr_roles():
        return []

    def start(self):
        log = logging.getLogger(__name__)
        log.info(h1('Starting monitoring feature'))
        bundle_repo = 'lightbend/commercial-monitoring/' if self.version_args and self.version_args[0] == 'snapshot' \
            else ''
        if is_cinnamon_grafana_docker_based(self.image_version):
            bundle_name = 'cinnamon-grafana-docker'
        else:
            bundle_name = 'cinnamon-grafana'
        grafana = select_bintray_uri(bundle_name, self.version_args, bundle_repo)
        log.info('Deploying bundle %s..' % grafana['bundle'])
        load_command = ['load', grafana['bundle'], '--disable-instructions'] + \
            parse_offline_mode_arg(self.offline_mode)
        conductr_cli.conduct_main.run(load_command, configure_logging=False)
        conductr_cli.conduct_main.run(['run', grafana['name'], '--disable-instructions', '--wait-timeout', '600'],
                                      configure_logging=False)
        return FeatureStartResult(True, [BundleStartResult(grafana['name'], self.ports[0])])

    @staticmethod
    def stop():
        return True


class ContinuousDeliveryFeature:
    """ContinuousDelivery feature.

    On start, the continuous-delivery bundle will be run. The version of the continuous-delivery
    bundle can also be configured using feature arguments. For example:

        `-f continuous-delivery`: default latest version of the Visualizer bundle
        `-f continuous-delivery v2`: specify a tag
    """

    name = 'continuous-delivery'
    ports = []
    dependencies = []
    provides = []

    def __init__(self, version_args, image_version, offline_mode):
        self.version_args = version_args
        self.image_version = image_version
        self.offline_mode = offline_mode

    def conductr_pre_core_start(self, envs, envs_core, args, args_core, dir, bind_addrs, conductr_roles):
        pass

    def conductr_core_envs(self):
        return []

    def conductr_pre_agent_start(self, envs, envs_agent, args, args_agent, dir, bind_addrs, core_addrs, conductr_roles):
        pass

    def conductr_agent_envs(self):
        return []

    def conductr_post_start(self, args, run_result):
        pass

    def conductr_feature_envs(self):
        return []

    @staticmethod
    def conductr_args():
        return []

    @staticmethod
    def conductr_roles():
        return []

    def start(self):
        if is_conductr_supportive_of_features(self.image_version):
            log = logging.getLogger(__name__)
            log.info(h1('Starting continuous delivery feature'))
            cd = select_bintray_uri('continuous-delivery', self.version_args)
            log.info('Deploying bundle %s..' % cd['bundle'])
            load_command = ['load', cd['bundle'], '--disable-instructions'] + parse_offline_mode_arg(self.offline_mode)
            conductr_cli.conduct_main.run(load_command, configure_logging=False)
            conductr_cli.conduct_main.run(['run', cd['name'], '--disable-instructions'],
                                          configure_logging=False)
            return FeatureStartResult(True, [])
        else:
            return FeatureStartResult(False, [])

    @staticmethod
    def stop():
        return True


feature_classes = [
    ProxyingFeature,
    VisualizationFeature,
    LoggingFeature,
    LiteLoggingFeature,
    MonitoringFeature,
    OciInDockerFeature,
    ContinuousDeliveryFeature
]

feature_names = [feature.name for feature in feature_classes]
feature_lookup = {feature.name: feature for feature in feature_classes}


def calculate_features(features):
    """Given a list of feature names, calculates all features that are to be started in dependency order.

    Returns:
        list of str: All features (by name) to be started in dependency order
    """

    visited = set()
    calculated_names = []

    def visit(feature_names):
        for feature_name in feature_names:
            if feature_name not in visited:
                visited.add(feature_name)
                visit(feature_lookup[feature_name].dependencies)
                calculated_names.append(feature_name)

    visit(features)

    return calculated_names


def collect_features(feature_args, no_default_features, image_version, offline_mode):
    """Collect all enabled features.

    Collect features recursively with topological sort to include all dependencies in order.

    Args:
        feature_args (list of list of str): Command-line arguments for features.
            Note that each feature has a list of arguments, the first is the feature name,
            followed by optional arguments. For example: `[['logging'], ['monitoring', '2.1.0']]`.
        no_default_features: If true, no features will be enabled unless explicitly included
        image_version: Version of the ConductR docker image.
        offline_mode: The offline mode flag

    Returns:
        list of obj: All enabled features, initialised with feature arguments, in dependency order.
    """

    feature_names = [name for name, *args in feature_args]
    feature_args = {name: args for name, *args in feature_args}

    features = []

    all_feature_names = calculate_features(feature_names)

    for feature_name in all_feature_names:
        args = feature_args[feature_name] if feature_name in feature_args else []
        feature = feature_lookup[feature_name](args, image_version, offline_mode)
        features.append(feature)

    # Calculate default and mandatory features. Mandatory features are always enabled whereas default features
    # are enabled unless a `--no-default-features` argument is provided.

    # Note that OCI-in-Docker is a default feature on linux (thus can be disabled) whereas it is mandatory on macOS

    def add_default_features(features):
        names = [feature.name for feature in features]

        def add_logging_lite(features):
            if LoggingFeature.name not in names:
                features.insert(0, feature_lookup[LiteLoggingFeature.name]([], image_version, offline_mode))

        def add_oci_in_docker(features):
            if OciInDockerFeature.name not in names and host.is_linux():
                features.insert(0, feature_lookup[OciInDockerFeature.name]([], image_version, offline_mode))

        def add_proxying(features):
            if ProxyingFeature.name not in names:
                features.insert(0, feature_lookup[ProxyingFeature.name]([], image_version, offline_mode))

        def add_continuous_delivery(features):
            if ContinuousDeliveryFeature.name not in names:
                features.insert(0, feature_lookup[ContinuousDeliveryFeature.name]([], image_version, offline_mode))

        add_logging_lite(features)
        add_oci_in_docker(features)
        add_proxying(features)
        add_continuous_delivery(features)

    def add_mandatory_features(features):
        names = [feature.name for feature in features]

        def add_oci_in_docker(features):
            if OciInDockerFeature.name not in names and not host.is_linux():
                features.insert(0, feature_lookup[OciInDockerFeature.name]([], image_version, offline_mode))

        add_oci_in_docker(features)

    if not no_default_features:
        add_default_features(features)

    add_mandatory_features(features)

    return features


def feature_conflicts(names):
    """Calculates all feature conflicts (according to provides)

    Args:
        names: list of str

    Returns:
        dictionary with key equals provide, value equals list of conflicting names
        e.g. { 'logging': ['logging-lite', 'logging'] }
    """

    conflicts = {}

    for n in calculate_features(names):
        f = feature_lookup[n]

        for p in f.provides:
            if p in conflicts:
                conflicts[p].append(f.name)
            else:
                conflicts[p] = [f.name]

    for p in list(conflicts):
        if len(conflicts[p]) < 2:
            del conflicts[p]

    return conflicts


def stop_features():
    feature_success = True

    for f in feature_classes:
        feature_success = f.stop() and feature_success

    return feature_success


def select_bintray_uri(name, version_args=[], bundle_repo=''):
    bundle_version = ''  # latest
    # parse args: [VERSION]
    if version_args:
        if version_args[0] == 'snapshot':
            if version_args[1:]:
                bundle_version = version_args[1]
        else:
            bundle_version = version_args[0]

    # reformat version: dashes to dots and ensure 'v' prefix
    if bundle_version:
        bundle_version = bundle_version.replace('-', '.')
        bundle_version = 'v' + bundle_version if not bundle_version.startswith('v') else bundle_version
        bundle_version = ':' + bundle_version
    bundle_expression = bundle_repo + name + bundle_version
    return {'name': name, 'bundle': bundle_expression}


def parse_offline_mode_arg(offline_mode):
    if offline_mode:
        return ['--offline']
    else:
        return []


def all_feature_ports():
    return sorted([
        port
        for f in feature_classes
        for port in f.ports
    ])
