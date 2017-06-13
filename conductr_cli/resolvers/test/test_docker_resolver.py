from conductr_cli.resolvers import docker_resolver
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import tempfile


class TestParseUri(TestCase):
    def test_success(self):
        self.assertEqual(docker_resolver.parse_uri('alpine'), (
            (None, 'registry.hub.docker.com'),
            (None, 'library'),
            ('alpine', 'alpine'),
            (None, 'latest')
        ))

        self.assertEqual(docker_resolver.parse_uri('alpine:3.5'), (
            (None, 'registry.hub.docker.com'),
            (None, 'library'),
            ('alpine', 'alpine'),
            ('3.5', '3.5')
        ))

        self.assertEqual(docker_resolver.parse_uri('lightbend-docker.registry.bintray.io/conductr/oci-in-docker'), (
            ('lightbend-docker.registry.bintray.io', 'lightbend-docker.registry.bintray.io'),
            ('conductr', 'conductr'),
            ('oci-in-docker', 'oci-in-docker'),
            (None, 'latest')
        ))

        self.assertEqual(docker_resolver.parse_uri('lightbend-docker.registry.bintray.io/conductr/oci-in-docker:0.1'), (
            ('lightbend-docker.registry.bintray.io', 'lightbend-docker.registry.bintray.io'),
            ('conductr', 'conductr'),
            ('oci-in-docker', 'oci-in-docker'),
            ('0.1', '0.1')
        ))


class TestLoadCredentials(TestCase):
    def test_load_docker_credentials(self):
        with tempfile.NamedTemporaryFile('w') as one,\
                tempfile.NamedTemporaryFile('w') as two, \
                tempfile.NamedTemporaryFile('w') as three:
            one.write('user=one\npassword=one-password')
            one.flush()
            two.write('username=two\npassword=two-password')
            two.flush()
            three.write('hello')
            three.flush()

            with open(one.name, 'r') as one_in, \
                    patch('os.path.exists', MagicMock(return_value=True)), \
                    patch('builtins.open', MagicMock(return_value=one_in)):
                self.assertEqual(
                    docker_resolver.load_docker_credentials('test'),
                    ('one', 'one-password')
                )

            with open(two.name, 'r') as two_in, \
                    patch('os.path.exists', MagicMock(return_value=True)), \
                    patch('builtins.open', MagicMock(return_value=two_in)):
                self.assertEqual(
                    docker_resolver.load_docker_credentials('test'),
                    ('two', 'two-password')
                )

            with open(three.name, 'r') as three_in, \
                    patch('os.path.exists', MagicMock(return_value=True)), \
                    patch('builtins.open', MagicMock(return_value=three_in)):
                self.assertIsNone(docker_resolver.load_docker_credentials('test'))

            path_exists_mock = MagicMock(side_effect=[False, True])

            with open(one.name, 'r') as one_in, \
                    patch('os.path.exists', path_exists_mock), \
                    MagicMock(return_value=one_in) as open_mock, \
                    patch('builtins.open', open_mock):
                docker_resolver.load_docker_credentials('test')

                path_exists_mock.assert_has_calls([
                    call('{}-{}'.format(docker_resolver.DOCKER_CREDENTIAL_FILE_PATH, 'test')),
                    call(docker_resolver.DOCKER_CREDENTIAL_FILE_PATH)
                ])


class TestFetchManifest(TestCase):

    def test_offline_mode(self):
        mock_is_file = MagicMock(return_value=True)
        mock_json_load = MagicMock(return_value='1234')
        mock_open = MagicMock(return_value=MagicMock())

        with \
                patch('os.path.isfile', mock_is_file), \
                patch('json.load', mock_json_load), \
                patch('builtins.open', mock_open):
            self.assertEqual(
                docker_resolver.fetch_manifest('/tmp', 'registry.hub.docker.com', 'library', 'alpine', '3.5', True),
                '1234'
            )

        mock_is_file.assert_called_once_with('/tmp/docker-manifest-624ab327c0f6bb1039ca62'
                                             '9a2c1ec806514b9194c30491c02e9800254c73d998')


class TestSupportedSchemes(TestCase):
    def test_supported_schemes(self):
        self.assertEqual([SCHEME_BUNDLE], docker_resolver.supported_schemes())
