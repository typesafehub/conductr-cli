from conductr_cli import bndl_utils
from conductr_cli.bndl_utils import ApplicationType, BndlFormat
from conductr_cli.endpoint import Endpoint
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, strip_margin
from io import BytesIO
from pyhocon import ConfigFactory
import os
import shutil
import tempfile


class TestBndlUtils(CliTestCase):
    def test_escape_bash_double_quotes(self):
        self.assertEqual(bndl_utils.escape_bash_double_quotes('hello'), 'hello')
        self.assertEqual(bndl_utils.escape_bash_double_quotes('"hello"'), '\\"hello\\"')
        self.assertEqual(bndl_utils.escape_bash_double_quotes('$hello'), '$hello')
        self.assertEqual(bndl_utils.escape_bash_double_quotes('echo `whoami`'), 'echo \\`whoami\\`')

    def test_detect_format_stream(self):
        # empty stream is none
        self.assertEqual(
            bndl_utils.detect_format_stream(b''),
            None
        )

        # parsable as hocon is bundle
        self.assertEqual(bndl_utils.detect_format_stream(b'name = "test"'), BndlFormat.BUNDLE)

        # unrelated stream is none
        self.assertEqual(
            bndl_utils.detect_format_stream(b'hello world this is a test'),
            None
        )

        # docker save without tag starts with a hex digest tar dir entry
        self.assertEqual(
            bndl_utils.detect_format_stream(b'194853445611786369d26c17093e481cdc14c838375091037f780fe22aa760e7/'
                                            b'\x00\x00\x00'),
            BndlFormat.DOCKER
        )

        # docker save with a tag starts with a json tar file entry
        self.assertEqual(
            bndl_utils.detect_format_stream(b'4a415e3663882fbc554ee830889c68a33b3585503892cc718a4698e91ef2a526.json'
                                            b'\x00\x00\x00'),
            BndlFormat.DOCKER
        )

        # docker from a tar stream of a dir on disk, we just hope the order works out
        self.assertEqual(
            bndl_utils.detect_format_stream(b'\x00/manifest.json\x00\x00\x00/layer.tar\x00\x00\x00'),
            BndlFormat.DOCKER
        )

        # oci image from a tar stream of a dir on disk, we just hope the order works out
        self.assertEqual(
            bndl_utils.detect_format_stream(b'\x00/oci-layout\x00\x00\x00/refs/\x00\x00\x00'),
            BndlFormat.OCI_IMAGE
        )

        # zips are bundles
        self.assertEqual(bndl_utils.detect_format_stream(b'PK\x03\x04'), BndlFormat.BUNDLE)

    def test_detect_format_dir(self):
        docker_dir = tempfile.mkdtemp()
        oci_image_dir = tempfile.mkdtemp()
        bundle_dir = tempfile.mkdtemp()
        bundle_conf_dir = tempfile.mkdtemp()
        nothing_dir = tempfile.mkdtemp()

        try:
            os.mkdir(os.path.join(oci_image_dir, 'refs'))
            os.mkdir(os.path.join(oci_image_dir, 'blobs'))

            open(os.path.join(oci_image_dir, 'oci-layout'), 'a').close()
            open(os.path.join(docker_dir, 'repositories'), 'a').close()
            open(os.path.join(docker_dir, 'manifest.json'), 'a').close()
            open(os.path.join(nothing_dir, 'hello'), 'a').close()
            open(os.path.join(bundle_dir, 'bundle.conf'), 'a').close()
            open(os.path.join(bundle_conf_dir, 'runtime-config.sh'), 'a').close()

            self.assertEqual(bndl_utils.detect_format_dir(oci_image_dir), BndlFormat.OCI_IMAGE)
            self.assertEqual(bndl_utils.detect_format_dir(docker_dir), BndlFormat.DOCKER)
            self.assertEqual(bndl_utils.detect_format_dir(nothing_dir), BndlFormat.BUNDLE)
            self.assertEqual(bndl_utils.detect_format_dir(bundle_dir), BndlFormat.BUNDLE)
            self.assertEqual(bndl_utils.detect_format_dir(bundle_conf_dir), BndlFormat.BUNDLE)
        finally:
            shutil.rmtree(docker_dir)
            shutil.rmtree(oci_image_dir)
            shutil.rmtree(bundle_dir)
            shutil.rmtree(bundle_conf_dir)
            shutil.rmtree(nothing_dir)

    def test_digest_reader_writer(self):
        data = b'some data'
        digest = '1307990e6ba5ca145eb35e99182a9bec46531bc54ddf656a602c780fa0240dee'
        digest_empty = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

        bytes_io = BytesIO(data)

        reader = bndl_utils.DigestReaderWriter(bytes_io)
        writer = bndl_utils.DigestReaderWriter(BytesIO())

        shutil.copyfileobj(reader, writer)

        self.assertEqual(reader.digest_in.hexdigest(), digest)
        self.assertEqual(reader.digest_out.hexdigest(), digest_empty)
        self.assertEqual(reader.size_in, 9)
        self.assertEqual(reader.size_out, 0)
        self.assertEqual(writer.digest_in.hexdigest(), digest_empty)
        self.assertEqual(writer.digest_out.hexdigest(), digest)
        self.assertEqual(writer.size_in, 0)
        self.assertEqual(writer.size_out, 9)

    def test_first_mtime(self):
        tmpdir = tempfile.mkdtemp()

        try:
            open(os.path.join(tmpdir, 'one'), 'w').close()
            os.mkdir(os.path.join(tmpdir, 'sub'))
            open(os.path.join(tmpdir, 'sub', 'two'), 'w').close()
            os.utime(os.path.join(tmpdir, 'one'), (1234, 1234))
            self.assertEqual(bndl_utils.first_mtime(os.path.join(tmpdir)), 1234)
        finally:
            shutil.rmtree(tmpdir)

    def test_load_bundle_args_into_conf_with_empty_lists(self):
        simple_config = ConfigFactory.parse_string('')
        args = create_attributes_object({
            'annotations': [],
            'format': BndlFormat.BUNDLE,
            'roles': [],
            'tags': []
        })
        application_type = ApplicationType.GENERIC
        defaults = application_type.config_defaults('universal')
        bndl_utils.load_bundle_args_into_conf(simple_config, args, application_type)
        self.assertEqual(simple_config.get('annotations'), defaults['annotations'])
        self.assertEqual(simple_config.get('compatibilityVersion'), defaults['compatibilityVersion'])
        self.assertEqual(simple_config.get('diskSpace'), defaults['diskSpace'])
        self.assertEqual(simple_config.get('memory'), defaults['memory'])
        self.assertEqual(simple_config.get('name'), defaults['name'])
        self.assertEqual(simple_config.get('nrOfCpus'), defaults['nrOfCpus'])
        self.assertEqual(simple_config.get('roles'), defaults['roles'])
        self.assertEqual(simple_config.get('system'), defaults['system'])
        self.assertEqual(simple_config.get('systemVersion'), defaults['systemVersion'])
        self.assertEqual(simple_config.get('tags'), defaults['tags'])
        self.assertEqual(simple_config.get('version'), defaults['version'])

    def test_load_bundle_args_into_conf_with_generic_defaults(self):
        simple_config = ConfigFactory.parse_string('')
        args = create_attributes_object({
            'format': BndlFormat.BUNDLE
        })
        application_type = ApplicationType.GENERIC
        defaults = application_type.config_defaults('universal')
        bndl_utils.load_bundle_args_into_conf(simple_config, args, application_type)
        self.assertEqual(simple_config.get('annotations'), defaults['annotations'])
        self.assertEqual(simple_config.get('compatibilityVersion'), defaults['compatibilityVersion'])
        self.assertEqual(simple_config.get('diskSpace'), defaults['diskSpace'])
        self.assertEqual(simple_config.get('memory'), defaults['memory'])
        self.assertEqual(simple_config.get('name'), defaults['name'])
        self.assertEqual(simple_config.get('nrOfCpus'), defaults['nrOfCpus'])
        self.assertEqual(simple_config.get('roles'), defaults['roles'])
        self.assertEqual(simple_config.get('system'), defaults['system'])
        self.assertEqual(simple_config.get('systemVersion'), defaults['systemVersion'])
        self.assertEqual(simple_config.get('tags'), defaults['tags'])
        self.assertEqual(simple_config.get('version'), defaults['version'])

    def test_load_bundle_args_into_conf_with_play_defaults(self):
        simple_config = ConfigFactory.parse_string('')
        args = create_attributes_object({
            'format': BndlFormat.BUNDLE
        })
        application_type = ApplicationType.PLAY
        defaults = application_type.config_defaults('universal')
        bndl_utils.load_bundle_args_into_conf(simple_config, args, application_type)
        self.assertEqual(simple_config.get('annotations'), defaults['annotations'])
        self.assertEqual(simple_config.get('compatibilityVersion'), defaults['compatibilityVersion'])
        self.assertEqual(simple_config.get('diskSpace'), defaults['diskSpace'])
        self.assertEqual(simple_config.get('memory'), defaults['memory'])
        self.assertEqual(simple_config.get('name'), defaults['name'])
        self.assertEqual(simple_config.get('nrOfCpus'), defaults['nrOfCpus'])
        self.assertEqual(simple_config.get('roles'), defaults['roles'])
        self.assertEqual(simple_config.get('system'), defaults['system'])
        self.assertEqual(simple_config.get('systemVersion'), defaults['systemVersion'])
        self.assertEqual(simple_config.get('tags'), defaults['tags'])
        self.assertEqual(simple_config.get('version'), defaults['version'])

    def test_load_bundle_args_into_conf(self):
        base_args = create_attributes_object({
            'name': 'world',
            'format': BndlFormat.BUNDLE,
            'tags': ['testing'],
            'annotations': {}
        })

        base_args_dup_tags = create_attributes_object({
            'name': 'world',
            'format': BndlFormat.BUNDLE,
            'tags': ['testing', 'testing', 'testing'],
            'annotations': {}
        })

        extended_args = create_attributes_object({
            'name': 'world',
            'format': BndlFormat.BUNDLE,
            'version': '4',
            'compatibility_version': '5',
            'system': 'myapp',
            'system_version': '3',
            'nr_of_cpus': '8',
            'memory': '65536',
            'disk_space': '16384',
            'roles': ['web', 'backend'],
            'image_tag': 'latest',
            'annotations': ['com.lightbend.test=hello world', 'description=this is a test'],
            'endpoints': [
                Endpoint({
                    'name': 'web',
                    'component': 'test-bundle',
                    'service-name': 'web',
                    'acls': [
                        {'value': '/', 'rewrite': None, 'match': 'path', 'protocol': 'http'},
                        {'value': '/subpath', 'rewrite': None, 'match': 'path', 'protocol': 'http'}
                    ]
                }),
                Endpoint({
                    'name': 'no-acls',
                    'component': 'test-bundle',
                    'bind-port': 2345
                }),
                Endpoint({
                    'name': 'tcp',
                    'component': 'test-bundle',
                    'service-name': 'tcp',
                    'acls': [
                        {'value': '[5000, 5001]', 'rewrite': None, 'match': None, 'protocol': 'tcp'},
                        {'value': '[5002, 5003]', 'rewrite': None, 'match': None, 'protocol': 'tcp'}
                    ]
                }),
                Endpoint({
                    'name': 'udp',
                    'component': 'test-bundle',
                    'service-name': 'udp',
                    'acls': [
                        {'value': '[6000, 6001]', 'rewrite': None, 'match': None, 'protocol': 'udp'},
                        {'value': '[6002, 6003]', 'rewrite': None, 'match': None, 'protocol': 'udp'}
                    ]
                })
            ]
        })

        check_args = create_attributes_object({
            'check_addresses': ['$MY_BUNDLE_HOST', 'http://192.168.10.1:9999'],
            'check_connection_timeout': 5,
            'check_initial_delay': 5
        })

        # empty
        no_defaults = ConfigFactory.parse_string('')
        bndl_utils.load_bundle_args_into_conf(no_defaults, create_attributes_object({}), application_type=None)

        self.assertEqual(no_defaults, ConfigFactory.parse_string(''))

        # test that config value is specified, with defaults etc
        simple_config = ConfigFactory.parse_string('')
        defaults = ApplicationType.GENERIC.config_defaults('universal')
        bndl_utils.load_bundle_args_into_conf(simple_config, base_args, ApplicationType.GENERIC)
        self.assertEqual(simple_config.get('name'), 'world')
        self.assertEqual(simple_config.get('compatibilityVersion'), defaults['compatibilityVersion'])
        self.assertEqual(simple_config.get('diskSpace'), defaults['diskSpace'])
        self.assertEqual(simple_config.get('memory'), defaults['memory'])
        self.assertEqual(simple_config.get('nrOfCpus'), defaults['nrOfCpus'])
        self.assertEqual(simple_config.get('roles'), defaults['roles'])
        self.assertEqual(simple_config.get('system'), 'world')
        self.assertEqual(simple_config.get('version'), defaults['version'])
        self.assertEqual(simple_config.get('tags'), ['testing'])

        # test that config value is overwritten
        name_config = ConfigFactory.parse_string('name = "hello"')
        bndl_utils.load_bundle_args_into_conf(name_config, base_args, ApplicationType.GENERIC)
        self.assertEqual(name_config.get('name'), 'world')

        # test that config value is retained
        cpu_config = ConfigFactory.parse_string('nrOfCpus = 0.1')
        bndl_utils.load_bundle_args_into_conf(cpu_config, base_args, ApplicationType.GENERIC)
        self.assertEqual(cpu_config.get('nrOfCpus'), 0.1)

        config = ConfigFactory.parse_string('')
        bndl_utils.load_bundle_args_into_conf(config, extended_args, ApplicationType.GENERIC)

        # test that various args are set correctly
        self.assertEqual(config.get('name'), 'world')
        self.assertEqual(config.get('version'), '4')
        self.assertEqual(config.get('compatibilityVersion'), '5')
        self.assertEqual(config.get('system'), 'myapp')
        self.assertEqual(config.get('systemVersion'), '3')
        self.assertEqual(config.get('nrOfCpus'), '8')
        self.assertEqual(config.get('memory'), '65536')
        self.assertEqual(config.get('diskSpace'), '16384')
        self.assertEqual(config.get('roles'), ['web', 'backend'])

        # test that the "latest" tag is ignored
        self.assertEqual(config.get('tags'), ['0.0.1'])

        # test that we add replace tags that exist
        tag_config = ConfigFactory.parse_string('{ tags = ["hello"] }')
        bndl_utils.load_bundle_args_into_conf(tag_config, base_args, ApplicationType.GENERIC)
        self.assertEqual(tag_config.get('tags'), ['testing'])

        # test that we only retain unique tags
        tag_config = ConfigFactory.parse_string('{}')
        bndl_utils.load_bundle_args_into_conf(tag_config, base_args_dup_tags, ApplicationType.GENERIC)
        self.assertEqual(tag_config.get('tags'), ['testing'])

        # test that annotations are added
        annotations_config = ConfigFactory.parse_string('{ annotations = { name = "my-name" } }')
        bndl_utils.load_bundle_args_into_conf(annotations_config, extended_args, ApplicationType.GENERIC)
        self.assertEqual(annotations_config.get('annotations'), {
            'name': 'my-name',
            'com': {
                'lightbend': {
                    'test': 'hello world'
                }
            },
            'description': 'this is a test'
        })

        # test that endpoints are replaced in existing component
        existing_endpoints_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    test-bundle {
               |      description = "test-bundle"
               |      file-system-type = "universal"
               |      start-command = [
               |        "test-bundle/bin/test-bundle"
               |      ]
               |      endpoints {
               |        test {
               |          bind-protocol = "tcp"
               |          bind-port = 0
               |        }
               |      }
               |    }
               |  }
               |}"""))
        bndl_utils.load_bundle_args_into_conf(existing_endpoints_config, extended_args, ApplicationType.GENERIC)
        expected_replaced_endpoints_config = ConfigFactory.parse_string(strip_margin(
            """|web {
               |  bind-protocol = "http"
               |  bind-port = 0
               |  service-name = "web"
               |  acls = [
               |    {
               |      http {
               |        requests = [
               |          {
               |            path = "/"
               |          }
               |          {
               |            path = "/subpath"
               |          }
               |        ]
               |      }
               |    }
               |  ]
               |}
               |no-acls {
               |  bind-protocol = "tcp"
               |  bind-port = 2345
               |}
               |tcp {
               |  bind-protocol = "tcp"
               |  bind-port = 0
               |  service-name = "tcp"
               |  acls = [
               |    {
               |      tcp {
               |        requests = [
               |          5000,
               |          5001,
               |          5002,
               |          5003
               |        ]
               |      }
               |    }
               |  ]
               |}
               |udp {
               |  bind-protocol = "udp"
               |  bind-port = 0
               |  service-name = "udp"
               |  acls = [
               |    {
               |      udp {
               |        requests = [
               |          6000,
               |          6001,
               |          6002,
               |          6003
               |        ]
               |      }
               |    }
               |  ]
               |}"""))
        self.assertEqual(existing_endpoints_config.get('components.test-bundle.endpoints'),
                         expected_replaced_endpoints_config)

        # test that endpoints are added when component is auto-detected
        auto_detect_endpoint_args = create_attributes_object({
            'format': BndlFormat.BUNDLE,
            'endpoints': [
                Endpoint({
                    'name': 'web',
                    'service-name': 'web',
                    'acls': [
                        {'value': '/', 'rewrite': None, 'match': None, 'protocol': 'http'}
                    ]
                })
            ]
        })
        auto_detect_endpoints_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    test-bundle {
               |      description = "test-bundle"
               |      file-system-type = "universal"
               |      start-command = [
               |        "test-bundle/bin/test-bundle"
               |      ]
               |      endpoints {
               |        test {
               |          bind-protocol = "tcp"
               |          bind-port = 0
               |        }
               |      }
               |    }
               |    bundle-status {
               |      description = "bundle-status"
               |      file-system-type = "universal"
               |      start-command = [
               |        "check",
               |        "$SOME_BUNDLE_HOST"
               |      ]
               |    }
               |  }
               |}"""))
        bndl_utils.load_bundle_args_into_conf(auto_detect_endpoints_config,
                                              auto_detect_endpoint_args,
                                              ApplicationType.GENERIC)
        expected_replaced_endpoints_config = ConfigFactory.parse_string(strip_margin(
            """|web {
               |  bind-protocol = "http"
               |  bind-port = 0
               |  service-name = "web"
               |  acls = [
               |    {
               |      http {
               |        requests = [
               |          {
               |            path-beg = "/"
               |          }
               |        ]
               |      }
               |    }
               |  ]
               |}"""))
        self.assertEqual(auto_detect_endpoints_config.get('components.test-bundle.endpoints'),
                         expected_replaced_endpoints_config)

        # test that endpoints can be added when no component exist
        no_components_config = ConfigFactory.parse_string(strip_margin("""|{}"""))

        bndl_utils.load_bundle_args_into_conf(no_components_config, extended_args, False)

        # test that endpoints can be added when the specified component does not exist
        missing_endpoint_component_args = create_attributes_object({
            'endpoints': [
                Endpoint({
                    'name': 'web',
                    'component': 'a-component',
                    'service-name': 'web',
                    'acls': [
                        {'value': '/', 'rewrite': None, 'match': None, 'protocol': 'http'},
                        {'value': '/subpath', 'rewrite': None, 'match': None, 'protocol': 'http'}
                    ]
                })
            ]
        })
        missing_component_endpoints_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    test-bundle {
               |      description = "test-bundle"
               |      file-system-type = "universal"
               |      start-command = [
               |        "test-bundle/bin/test-bundle"
               |      ]
               |      endpoints {
               |        test {
               |          bind-protocol = "tcp"
               |          bind-port = 0
               |        }
               |      }
               |    }
               |  }
               |}"""))

        bndl_utils.load_bundle_args_into_conf(missing_component_endpoints_config,
                                              missing_endpoint_component_args,
                                              False)

        # test that endpoints cannot be added when auto detection of component failed due to multiple components
        # in the config
        multiple_endpoint_components_args = create_attributes_object({
            'endpoints': [
                Endpoint({
                    'name': 'web',
                    'service-name': 'web',
                    'acls': [
                        {'value': '/', 'rewrite': None, 'match': None, 'protocol': 'http'}
                    ]
                })
            ]
        })
        multiple_endpoint_components_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    test-bundle1 {
               |      description = "test-bundle1"
               |      file-system-type = "universal"
               |      start-command = [
               |        "test-bundle/bin/test-bundle1"
               |      ]
               |      endpoints {
               |        test1 {
               |          bind-protocol = "tcp"
               |          bind-port = 0
               |        }
               |      }
               |    }
               |    test-bundle2 {
               |      description = "test-bundle2"
               |      file-system-type = "universal"
               |      start-command = [
               |        "test-bundle/bin/test-bundle2"
               |      ]
               |      endpoints {
               |        test2 {
               |          bind-protocol = "tcp"
               |          bind-port = 0
               |        }
               |      }
               |    }
               |  }
               |}"""))
        self.assertRaises(SyntaxError, bndl_utils.load_bundle_args_into_conf, multiple_endpoint_components_config,
                          multiple_endpoint_components_args, False)

        # test that check command is replaced in existing component
        existing_check_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    bundle-status {
               |      description = "bundle-status"
               |      file-system-type = "universal"
               |      start-command = [
               |        "check",
               |        "$SOME_BUNDLE_HOST"
               |      ]
               |    }
               |  }
               |}"""))
        bndl_utils.load_bundle_args_into_conf(existing_check_config,
                                              check_args,
                                              application_type=None)
        expected_replaced_check_config = ConfigFactory.parse_string(strip_margin(
            """|description = "bundle-status"
               |file-system-type = "universal"
               |start-command = [
               |  "check",
               |  "--initial-delay",
               |  "5",
               |  "--connection-timeout",
               |  "5",
               |  "$MY_BUNDLE_HOST",
               |  "http://192.168.10.1:9999"
               |]"""))
        self.assertEqual(existing_check_config.get('components.bundle-status'), expected_replaced_check_config)

        # test that status check component is added
        without_check_config = ConfigFactory.parse_string(strip_margin(
            """|{
               |  components {
               |    bundle {
               |      description = "bundle"
               |      file-system-type = "universal"
               |      start-command = [
               |        "some-command"
               |      ]
               |    }
               |  }
               |}"""))
        expected_new_check_config = ConfigFactory.parse_string(strip_margin(
            """|description = "Status check for the bundle component"
               |file-system-type = "universal"
               |start-command = [
               |  "check",
               |  "--initial-delay",
               |  "5",
               |  "--connection-timeout",
               |  "5",
               |  "$MY_BUNDLE_HOST",
               |  "http://192.168.10.1:9999"
               |],
               |endpoints = {}"""))
        bndl_utils.load_bundle_args_into_conf(without_check_config,
                                              check_args,
                                              application_type=None)
        self.assertEqual(without_check_config.get('components.bundle-status'), expected_new_check_config)

        # test that check component can be added when bundle.conf does not contain any components -- e.g. configurations
        no_components_config = ConfigFactory.parse_string(strip_margin("""|{}"""))
        bndl_utils.load_bundle_args_into_conf(no_components_config, check_args, False)
