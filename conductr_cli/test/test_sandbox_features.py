from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from conductr_cli.sandbox_features import VisualizationFeature, LiteLoggingFeature,\
    LoggingFeature, MonitoringFeature, \
    collect_features, select_bintray_uri
from conductr_cli.docker import DockerVmType
from conductr_cli.test.data.test_constants import LATEST_CONDUCTR_VERSION


class TestFeatures(TestCase):
    def test_collect_features(self):
        self.assertEqual([LiteLoggingFeature],
                         [type(f) for f in collect_features([], LATEST_CONDUCTR_VERSION, False)])

        self.assertEqual([LiteLoggingFeature, VisualizationFeature],
                         [type(f) for f in collect_features([['visualization']], LATEST_CONDUCTR_VERSION, False)])

        self.assertEqual([LoggingFeature],
                         [type(f) for f in collect_features([['logging']], LATEST_CONDUCTR_VERSION, False)])

        # enable dependencies
        self.assertEqual([LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['monitoring']], LATEST_CONDUCTR_VERSION, False)])

        # allow explicit listing of dependencies
        self.assertEqual([LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['logging'], ['monitoring']], LATEST_CONDUCTR_VERSION, False)])

        # topological ordering for dependencies
        self.assertEqual([LoggingFeature, MonitoringFeature],
                         [type(f) for f in collect_features([['monitoring'], ['logging']], LATEST_CONDUCTR_VERSION, False)])

        # topological ordering and ignore duplicates
        self.assertEqual([LoggingFeature, MonitoringFeature, VisualizationFeature],
                         [type(f) for f in collect_features([['monitoring'], ['visualization'], ['logging'], ['monitoring']],
                                                            LATEST_CONDUCTR_VERSION, False)])

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
