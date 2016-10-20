"""Sandbox features.

Features are specified on the command line with `-f/--feature NAME [ ARGS ... ]`.

Any feature arguments will be passed to the feature class constructor.

Feature attributes:
    name (str): Feature name used for command line argument.
    ports (list of int): Docker port mappings for the feature.
    dependencies (list of str): Names of other features that should also be enabled.
    bootstrap_features (list of str): Feature names to pass when ConductR is started in Docker.
    start (method): Start the feature as needed. Called after the sandbox has started.
"""

from conductr_cli import conduct_main
import logging


class VisualizationFeature:
    name = 'visualization'
    ports = [9999]
    dependencies = []
    bootstrap_features = [name]

    def __init__(self, args):
        self.args = args

    def start(self):
        pass


class LoggingFeature:
    name = 'logging'
    ports = [5601, 9200]
    dependencies = []
    bootstrap_features = [name]

    def __init__(self, args):
        self.args = args

    def start(self):
        pass


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
    dependencies = [LoggingFeature.name]
    bootstrap_features = []

    def __init__(self, args):
        self.args = args

    def start(self):
        log = logging.getLogger(__name__)
        log.info('Starting monitoring feature...')
        grafana = self.grafana_bundle()
        log.info('Running %s...' % grafana['bundle'])
        conduct_main.run(['load', grafana['bundle']])
        conduct_main.run(['run', grafana['name']])

    def grafana_bundle(self):
        bundle_name = 'cinnamon-grafana'
        bundle_repo = ''  # default
        bundle_version = ''  # latest
        # parse args: [snapshot] [VERSION]
        if self.args:
            if self.args[0] == 'snapshot':
                bundle_repo = 'lightbend/commercial-monitoring/'
                if self.args[1:]:
                    bundle_version = self.args[1]
            else:
                bundle_version = self.args[0]
        # reformat version: dashes to dots and ensure 'v' prefix
        if bundle_version:
            bundle_version = bundle_version.replace('-', '.')
            bundle_version = 'v' + bundle_version if not bundle_version.startswith('v') else bundle_version
            bundle_version = ':' + bundle_version
        bundle_expression = bundle_repo + bundle_name + bundle_version
        return {'name': bundle_name, 'bundle': bundle_expression}


feature_classes = [VisualizationFeature, LoggingFeature, MonitoringFeature]

feature_names = [feature.name for feature in feature_classes]
feature_lookup = {feature.name: feature for feature in feature_classes}


def collect_features(cli_args):
    """Collect all enabled features.

    Collect features recursively with topological sort to include all dependencies in order.

    Args:
        cli_args (list of list of str): Command-line arguments for features.
            Note that each feature has a list of arguments, the first is the feature name,
            followed by optional arguments. For example: `[['logging'], ['monitoring', '2.1.0']]`.

    Returns:
        list of obj: All enabled features, initialised with feature arguments, in dependency order.
    """

    feature_names = [name for name, *args in cli_args]
    feature_args = {name: args for name, *args in cli_args}

    visited = set()
    features = []

    def visit(feature_names):
        for feature_name in feature_names:
            if feature_name not in visited:
                visited.add(feature_name)
                args = feature_args[feature_name] if feature_name in feature_args else []
                feature = feature_lookup[feature_name](args)
                visit(feature.dependencies)
                features.append(feature)

    visit(feature_names)
    return features
