from conductr_cli import bundle_validation
from conductr_cli.exceptions import BundleConfValidationError
from conductr_cli.test.cli_test_case import strip_margin
from unittest import TestCase
from pyhocon import ConfigFactory
from unittest.mock import patch, MagicMock


class TestValidateBundleConf(TestCase):
    @staticmethod
    def test_success_with_all_checks():
        mock_assert_bundle_conf_non_empty = MagicMock(return_value=None)
        mock_assert_properties_non_empty = MagicMock(return_value=None)
        mock_assert_property_names = MagicMock(return_value=None)
        mock_assert_required_properties = MagicMock(return_value=None)

        with patch('conductr_cli.bundle_validation.assert_bundle_conf_non_empty', mock_assert_bundle_conf_non_empty), \
                patch('conductr_cli.bundle_validation.assert_properties_non_empty', mock_assert_properties_non_empty), \
                patch('conductr_cli.bundle_validation.assert_property_names', mock_assert_property_names), \
                patch('conductr_cli.bundle_validation.assert_required_properties', mock_assert_required_properties):
            bundle_conf = ConfigFactory.parse_string('nrOfCpus = 1.0')

            bundle_validation.validate_bundle_conf(bundle_conf, excludes=[])

        mock_assert_bundle_conf_non_empty.assert_called_once_with(bundle_conf)
        mock_assert_properties_non_empty.assert_called_once_with(bundle_conf)
        mock_assert_property_names.assert_called_once_with(bundle_conf)
        mock_assert_required_properties.assert_called_once_with(bundle_conf)

    @staticmethod
    def test_success_with_excludes():
        mock_assert_bundle_conf_non_empty = MagicMock(return_value=None)
        mock_assert_properties_non_empty = MagicMock(return_value=None)
        mock_assert_property_names = MagicMock(return_value=None)
        mock_assert_required_properties = MagicMock()

        with patch('conductr_cli.bundle_validation.assert_bundle_conf_non_empty', mock_assert_bundle_conf_non_empty), \
                patch('conductr_cli.bundle_validation.assert_properties_non_empty', mock_assert_properties_non_empty), \
                patch('conductr_cli.bundle_validation.assert_property_names', mock_assert_property_names), \
                patch('conductr_cli.bundle_validation.assert_required_properties', mock_assert_required_properties):
            bundle_conf = ConfigFactory.parse_string('nrOfCpus = 1.0')

            bundle_validation.validate_bundle_conf(bundle_conf,
                                                   excludes=['required', 'property-name', 'empty-property'])

        mock_assert_bundle_conf_non_empty.assert_called_once_with(bundle_conf)
        mock_assert_properties_non_empty.assert_not_called()
        mock_assert_property_names.assert_not_called()
        mock_assert_required_properties.assert_not_called()

    def test_raise_bundle_conf_validation_error(self):
        mock_assert_bundle_conf_non_empty = MagicMock(return_value='bundle.conf non empty error')
        mock_assert_properties_non_empty = MagicMock(return_value='Property non empty error')
        mock_assert_property_names = MagicMock(return_value='Property name error')
        mock_assert_required_properties = MagicMock(return_value='Required properties error')

        with patch('conductr_cli.bundle_validation.assert_bundle_conf_non_empty', mock_assert_bundle_conf_non_empty), \
                patch('conductr_cli.bundle_validation.assert_properties_non_empty', mock_assert_properties_non_empty), \
                patch('conductr_cli.bundle_validation.assert_property_names', mock_assert_property_names), \
                patch('conductr_cli.bundle_validation.assert_required_properties', mock_assert_required_properties):
            bundle_conf = ConfigFactory.parse_string('nrOfCpus = 1.0')

            self.assertRaises(BundleConfValidationError, bundle_validation.validate_bundle_conf, bundle_conf, [])

        mock_assert_bundle_conf_non_empty.assert_called_once_with(bundle_conf)
        mock_assert_properties_non_empty.assert_called_once_with(bundle_conf)
        mock_assert_property_names.assert_called_once_with(bundle_conf)
        mock_assert_required_properties.assert_called_once_with(bundle_conf)


class TestAssertBundleConfNonEmpty(TestCase):
    def test_valid(self):
        bundle_conf = ConfigFactory.parse_string('nrOfCpus = 1.0')
        self.assertEqual(bundle_validation.assert_bundle_conf_non_empty(bundle_conf), None)

    def test_invalid(self):
        bundle_conf = ConfigFactory.parse_string('')
        self.assertEqual(bundle_validation.assert_bundle_conf_non_empty(bundle_conf),
                         'The bundle.conf is empty')


class TestAssertPropertiesNonEmpty(TestCase):
    def test_valid_empty_endpoint(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |components {
               |test-bundle {
               |    description = ""
               |    file-system-type = "universal"
               |    start-command = []
               |    endpoints {}
               |  }
               |}"""))
        self.assertEqual(bundle_validation.assert_properties_non_empty(bundle_conf), None)

    def test_valid_empty_services(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |components {
               |test-bundle {
               |    description = ""
               |    file-system-type = "universal"
               |    start-command = []
               |    endpoints {
               |      "akka-remote" = {
               |        bind-protocol = "tcp"
               |        bind-port     = 0
               |        services      = []
               |      }
               |    }
               |  }
               |}"""))
        self.assertEqual(bundle_validation.assert_properties_non_empty(bundle_conf), None)

    def test_invalid(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibilityVersion = "1"
               |system = ""
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |components {}"""))
        expected_error_message = 'The following properties are not allowed to be empty: system, components'
        self.assertEqual(bundle_validation.assert_properties_non_empty(bundle_conf), expected_error_message)


class TestAssertPropertyNames(TestCase):
    def test_valid_property_names_camel_case(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |annotations = {},
               |tags = ["1.0.0"]
               |components {
               |  test-bundle {
               |    description = "test-bundle"
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |        bind-port = 0
               |        acls = "some-acl"
               |      }
               |    }
               |  }
               |  bundle-status {
               |    description = "bundle-status"
               |    file-system-type = "universal"
               |    start-command = [
               |      "check",
               |      "$SOME_BUNDLE_HOST"
               |    ]
               |  }
               |}"""))
        self.assertEqual(bundle_validation.assert_property_names(bundle_conf), None)

    def test_valid_property_names_dash_notation(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibility-version = "1"
               |system = "my-system"
               |system-version = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |disk-space = 200000000
               |roles = ["web"]
               |annotations = {},
               |tags = ["1.0.0"]
               |components {
               |  test-bundle {
               |    description = "test-bundle"
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |        bind-port = 0
               |        acls = "some-acl"
               |      }
               |    }
               |  }
               |  bundle-status {
               |    description = "bundle-status"
               |    file-system-type = "universal"
               |    start-command = [
               |      "check",
               |      "$SOME_BUNDLE_HOST"
               |    ]
               |  }
               |}"""))
        self.assertEqual(bundle_validation.assert_property_names(bundle_conf), None)

    def test_invalid(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |nome = "my-bundle"
               |compatibilitVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |annotations = {},
               |tags = ["1.0.0"]
               |components {
               |  test-bundle {
               |    descriptiom = "test-bundle"
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |        bind-part = 0
               |        acls = "some-acl"
               |      }
               |    }
               |  }
               |  bundle-status {
               |    description = "bundle-status"
               |    file-system-type = "universal"
               |    start-commands = [
               |      "check",
               |      "$SOME_BUNDLE_HOST"
               |    ]
               |  }
               |}"""))
        expected_error_message = 'The following property names are invalid: ' \
                                 'compatibilitVersion, ' \
                                 'components.bundle-status.start-commands, ' \
                                 'components.test-bundle.descriptiom, ' \
                                 'components.test-bundle.endpoints.test.bind-part, ' \
                                 'nome'

        self.assertEqual(bundle_validation.assert_property_names(bundle_conf), expected_error_message)


class TestAssertRequiredProperties(TestCase):
    def test_valid(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |name = "my-bundle"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |components {
               |  test-bundle {
               |    description = "test-bundle"
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |        bind-port = 0
               |      }
               |    }
               |  }
               |  bundle-status {
               |    description = "bundle-status"
               |    file-system-type = "universal"
               |    start-command = [
               |      "check",
               |      "$SOME_BUNDLE_HOST"
               |    ],
               |    endpoints {}
               |  }
               |}"""))
        self.assertEqual(bundle_validation.assert_required_properties(bundle_conf), None)

    def test_invalid(self):
        bundle_conf = ConfigFactory.parse_string(strip_margin(
            """|version = "1"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web"]
               |components {
               |  test-bundle {
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |      }
               |    }
               |  }
               |  bundle-status {
               |    description = "bundle-status"
               |    file-system-type = "universal"
               |  }
               |}"""))
        expected_error_message = 'The following required properties are not declared: ' \
                                 'components.test-bundle.description, ' \
                                 'components.test-bundle.endpoints.test.bind-port, ' \
                                 'components.bundle-status.start-command, ' \
                                 'name'
        self.assertEqual(bundle_validation.assert_required_properties(bundle_conf), expected_error_message)
