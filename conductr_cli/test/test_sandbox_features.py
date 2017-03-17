from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from conductr_cli import logging_setup
from conductr_cli.sandbox_features import VisualizationFeature, LiteLoggingFeature,\
    LoggingFeature, MonitoringFeature, ProxyingFeature, \
    calculate_features, collect_features, feature_conflicts, select_bintray_uri
from conductr_cli.docker import DockerVmType
from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli.test.data.test_constants import LATEST_CONDUCTR_VERSION


class TestFeatures(TestCase):
    def test_feature_conflicts(self):
        # test no features
        self.assertEqual(feature_conflicts([]), {})

        # test not conflicting features
        self.assertEqual(feature_conflicts(['proxying', 'lite-logging']), {})

        # basic conflicts
        self.assertEqual(feature_conflicts(['lite-logging', 'logging']), {'logging': ['lite-logging', 'logging']})

        # conflicts from dependencies
        self.assertEqual(feature_conflicts(['lite-logging', 'monitoring']), {'logging': ['lite-logging', 'logging']})

    def test_calculate_features(self):
        self.assertEqual(calculate_features([]), [])

        self.assertEqual(calculate_features(['proxying']), ['proxying'])

        self.assertEqual(calculate_features(['monitoring', 'visualization']), ['logging', 'monitoring', 'visualization'])

    def test_collect_features(self):
        # default features enabled works
        self.assertEqual([ProxyingFeature, LiteLoggingFeature],
                         [type(f) for f in collect_features([], False, LATEST_CONDUCTR_VERSION, False)])

        # default features disabled works
        self.assertEqual([],
                         [type(f) for f in collect_features([], True, LATEST_CONDUCTR_VERSION, False)])

        self.assertEqual([ProxyingFeature, LiteLoggingFeature, VisualizationFeature],
                         [type(f) for f in collect_features([['visualization']], False, LATEST_CONDUCTR_VERSION, False)])

        self.assertEqual([ProxyingFeature, LoggingFeature],
                         [type(f) for f in collect_features([['logging']], False, LATEST_CONDUCTR_VERSION, False)])

        self.assertEqual([LoggingFeature],
                         [type(f) for f in collect_features([['logging']], True, LATEST_CONDUCTR_VERSION, False)])

        # enable dependencies
        self.assertEqual([ProxyingFeature, LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['monitoring']], False, LATEST_CONDUCTR_VERSION, False)])

        # allow explicit listing of dependencies
        self.assertEqual([ProxyingFeature, LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['logging'], ['monitoring']], False, LATEST_CONDUCTR_VERSION, False)])

        # topological ordering for dependencies
        self.assertEqual([ProxyingFeature, LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['monitoring'], ['logging']], False, LATEST_CONDUCTR_VERSION, False)])

        # topological ordering and ignore duplicates
        self.assertEqual([ProxyingFeature, LoggingFeature, MonitoringFeature, VisualizationFeature],
                         [type(f) for f in collect_features([['monitoring'], ['visualization'], ['logging'], ['monitoring']],
                                                            False, LATEST_CONDUCTR_VERSION, False)])

    def test_select_bintray_uri(self):
        self.assertEqual('cinnamon-grafana', select_bintray_uri('cinnamon-grafana')['name'])
        self.assertEqual('cinnamon-grafana', select_bintray_uri('cinnamon-grafana')['bundle'])

        self.assertEqual('cinnamon-grafana', select_bintray_uri('cinnamon-grafana', ['v2'])['name'])
        self.assertEqual('cinnamon-grafana:v2', select_bintray_uri('cinnamon-grafana', ['v2'])['bundle'])
        self.assertEqual('cinnamon-grafana:v2.1', select_bintray_uri('cinnamon-grafana', ['v2.1'])['bundle'])
        self.assertEqual('cinnamon-grafana:v2.1.0', select_bintray_uri('cinnamon-grafana', ['2.1.0'])['bundle'])
        self.assertEqual('cinnamon-grafana:v2.1.0.RC2', select_bintray_uri('cinnamon-grafana', ['2.1.0-RC2'])['bundle'])
        self.assertEqual('lightbend/commercial-monitoring/cinnamon-grafana:v2.1.0.20161018.43bab24',
                         select_bintray_uri('cinnamon-grafana',
                                            ['snapshot', '2.1.0-20161018-43bab24'],
                                            'lightbend/commercial-monitoring/')['bundle'])


class TestProxyingFeature(CliTestCase):
    logging_setup_args = MagicMock(**{
        'verbose': False,
        'quiet': False,
        'long_ids': False
    })

    def test_start_v1(self):
        run_mock = MagicMock()
        stdout_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            logging_setup.configure_logging(self.logging_setup_args, stdout_mock)
            ProxyingFeature([], LATEST_CONDUCTR_VERSION, False).start()

        self.assertEqual(run_mock.call_args_list, [])
        self.assertEqual('', self.output(stdout_mock))

    def test_start_v2_unconfigured(self):
        proxy_start = MagicMock()
        stdout_mock = MagicMock()

        with patch('conductr_cli.sandbox_proxy.start_proxy', proxy_start):
            logging_setup.configure_logging(self.logging_setup_args, stdout_mock)
            self.assertFalse(ProxyingFeature([], '2.0.0', False).start().started)

        proxy_start.assert_not_called()
        self.assertEqual('', self.output(stdout_mock))

    def test_start_v2_configured_no_docker(self):
        proxy_start = MagicMock(return_value=False)
        docker_present = MagicMock(return_value=False)
        stdout_mock = MagicMock()

        with \
                patch('conductr_cli.sandbox_proxy.start_proxy', proxy_start), \
                patch('conductr_cli.sandbox_proxy.is_docker_present', docker_present):
            logging_setup.configure_logging(self.logging_setup_args, stdout_mock)
            feature = ProxyingFeature([], '2.0.0', False)

            feature.conductr_pre_agent_start(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                [],
                ['192.168.100.1'],
                MagicMock()
            )

            feature.conductr_post_start(
                MagicMock(**{'bundle_http_port': 9000, 'ports': []}),
                MagicMock(**{'host': '192.168.100.1', 'core_addrs': ['192.168.100.1']})
            )

            self.assertEqual(feature.conductr_agent_envs(), [])

            self.assertFalse(feature.start().started)

        proxy_start.assert_called_once_with(proxy_bind_addr='192.168.100.1', bundle_http_port=9000, proxy_ports=[], all_feature_ports=[3000, 5601, 9200, 9999])
        self.assertEqual(
            strip_margin("""||------------------------------------------------|
                            || Starting proxying feature                      |
                            ||------------------------------------------------|
                            |HAProxy has not been started
                            |To enable proxying ensure Docker is running and restart the sandbox
                            |"""),
            self.output(stdout_mock))

    def test_start_v2_configured_with_docker(self):
        proxy_start = MagicMock(return_value=True)
        docker_present = MagicMock(return_value=True)
        stdout_mock = MagicMock()

        with \
                patch('conductr_cli.sandbox_proxy.start_proxy', proxy_start), \
                patch('conductr_cli.sandbox_proxy.is_docker_present', docker_present):
            logging_setup.configure_logging(self.logging_setup_args, stdout_mock)
            feature = ProxyingFeature([], '2.0.0', False)

            feature.conductr_pre_agent_start(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                [],
                ['192.168.100.1'],
                MagicMock()
            )

            feature.conductr_post_start(
                MagicMock(**{'bundle_http_port': 9000, 'ports': []}),
                MagicMock(**{'host': '192.168.100.1', 'core_addrs': ['192.168.100.1']})
            )

            self.assertEqual(feature.conductr_agent_envs(), ['HAPROXY_STATS_IP=192.168.100.1'])

            self.assertTrue(feature.start().started)

        proxy_start.assert_called_once_with(proxy_bind_addr='192.168.100.1', bundle_http_port=9000, proxy_ports=[], all_feature_ports=[3000, 5601, 9200, 9999])
        self.assertEqual(
            strip_margin("""||------------------------------------------------|
                            || Starting proxying feature                      |
                            ||------------------------------------------------|
                            |HAProxy has been started
                            |Your Bundles are by default accessible on:
                            |  192.168.100.1:9000
                            |"""),
            self.output(stdout_mock))

    def test_stop(self):
        proxy_stop = MagicMock(return_value=True)

        with patch('conductr_cli.sandbox_proxy.stop_proxy', proxy_stop):
            feature = ProxyingFeature([], '2.0.0', False)

            self.assertTrue(feature.stop())

        proxy_stop.assert_called_once_with()


class TestVisualizationFeature(TestCase):
    def test_start_v1(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            VisualizationFeature([], LATEST_CONDUCTR_VERSION, False).start()

        self.assertEqual(run_mock.call_args_list, [])

    def test_start_v2(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            VisualizationFeature([], '2.0.0', False).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'visualizer', '--disable-instructions'], configure_logging=False),
            call(['run', 'visualizer', '--disable-instructions'], configure_logging=False)
        ])

    def test_offline_mode(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            VisualizationFeature([], '2.0.0', True).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'visualizer', '--disable-instructions', '--offline'], configure_logging=False),
            call(['run', 'visualizer', '--disable-instructions'], configure_logging=False)
        ])


class TestLoggingFeature(TestCase):
    def test_start_v1(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            LoggingFeature([], LATEST_CONDUCTR_VERSION, False).start()

        self.assertEqual(run_mock.call_args_list, [])

    def test_start_v2_success(self):
        run_mock = MagicMock()
        vm_type_mock = MagicMock(return_value=DockerVmType.DOCKER_ENGINE)
        validate_docker_vm_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock), \
                patch('conductr_cli.docker.vm_type', vm_type_mock), \
                patch('conductr_cli.docker.validate_docker_vm', validate_docker_vm_mock):
            LoggingFeature([], '2.0.0', False).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'conductr-elasticsearch', '--disable-instructions'], configure_logging=False),
            call(['run', 'conductr-elasticsearch', '--disable-instructions'], configure_logging=False),
            call(['load', 'conductr-kibana', '--disable-instructions'], configure_logging=False),
            call(['run', 'conductr-kibana', '--disable-instructions', '--wait-timeout', '600'], configure_logging=False)
        ])

    def test_start_v2_docker_validation_failed(self):
        run_mock = MagicMock()
        vm_type_mock = MagicMock(return_value=DockerVmType.DOCKER_ENGINE)
        validate_docker_vm_mock = MagicMock(side_effect=SystemExit)

        with patch('conductr_cli.conduct_main.run', run_mock), \
                patch('conductr_cli.docker.vm_type', vm_type_mock), \
                patch('conductr_cli.docker.validate_docker_vm', validate_docker_vm_mock), \
                self.assertRaises(SystemExit):
            LoggingFeature([], '2.0.0', False).start()

        self.assertEqual(run_mock.call_args_list, [])

    def test_offline_mode(self):
        run_mock = MagicMock()
        vm_type_mock = MagicMock(return_value=DockerVmType.DOCKER_ENGINE)
        validate_docker_vm_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock), \
                patch('conductr_cli.docker.vm_type', vm_type_mock), \
                patch('conductr_cli.docker.validate_docker_vm', validate_docker_vm_mock):
            LoggingFeature([], '2.0.0', True).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'conductr-elasticsearch', '--disable-instructions', '--offline'], configure_logging=False),
            call(['run', 'conductr-elasticsearch', '--disable-instructions'], configure_logging=False),
            call(['load', 'conductr-kibana', '--disable-instructions', '--offline'], configure_logging=False),
            call(['run', 'conductr-kibana', '--disable-instructions', '--wait-timeout', '600'], configure_logging=False)
        ])


class TestLiteLoggingFeature(TestCase):
    def test_start_v1(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            LiteLoggingFeature([], LATEST_CONDUCTR_VERSION, False).start()

        self.assertEqual(run_mock.call_args_list, [])

    def test_start_v2(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            LiteLoggingFeature([], '2.0.0', False).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'eslite', '--disable-instructions'], configure_logging=False),
            call(['run', 'eslite', '--disable-instructions'], configure_logging=False)
        ])

    def test_offline_mode(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            LiteLoggingFeature([], '2.0.0', True).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'eslite', '--disable-instructions', '--offline'], configure_logging=False),
            call(['run', 'eslite', '--disable-instructions'], configure_logging=False)
        ])


class TestMonitoringFeature(TestCase):
    def test_start_v1(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            MonitoringFeature([], LATEST_CONDUCTR_VERSION, False).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'cinnamon-grafana', '--disable-instructions'], configure_logging=False),
            call(['run', 'cinnamon-grafana', '--disable-instructions', '--wait-timeout', '600'], configure_logging=False)
        ])

    def test_start_v2(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            MonitoringFeature([], '2.0.0', False).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'cinnamon-grafana-docker', '--disable-instructions'], configure_logging=False),
            call(['run', 'cinnamon-grafana-docker', '--disable-instructions', '--wait-timeout', '600'], configure_logging=False)
        ])

    def test_start_offline_mode(self):
        run_mock = MagicMock()

        with patch('conductr_cli.conduct_main.run', run_mock):
            MonitoringFeature([], '2.0.0', True).start()

        self.assertEqual(run_mock.call_args_list, [
            call(['load', 'cinnamon-grafana-docker', '--disable-instructions', '--offline'], configure_logging=False),
            call(['run', 'cinnamon-grafana-docker', '--disable-instructions', '--wait-timeout', '600'], configure_logging=False)
        ])
