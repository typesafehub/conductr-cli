from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from conductr_cli import license_validation
from conductr_cli.constants import DEFAULT_LICENSE_FILE
from conductr_cli.exceptions import LicenseValidationError
import ipaddress


class TestValidateLicense(TestCase):
    conductr_version = '2.1.0'

    core_addr = ipaddress.ip_address('192.168.1.1')

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    nr_of_agent_instances = 3

    license_file = DEFAULT_LICENSE_FILE

    def test_validate_posted_license(self):
        mock_get_license = MagicMock(side_effect=[
            (True, None),
            (True, self.license),
        ])
        mock_exists = MagicMock(return_value=True)
        mock_post_license = MagicMock()
        mock_validate_license_data = MagicMock()

        with patch('conductr_cli.license.get_license', mock_get_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license_validation.validate_license_data', mock_validate_license_data):
            license_validation.validate_license(self.conductr_version, self.core_addr,
                                                self.nr_of_agent_instances, self.license_file)

        expected_args = license_validation.LicenseArgs(self.core_addr)

        self.assertEqual([
            call(expected_args),
            call(expected_args)
        ], mock_get_license.call_args_list)

        mock_exists.assert_called_once_with(self.license_file)

        mock_post_license.assert_called_once_with(expected_args, self.license_file)

        mock_validate_license_data.assert_called_once_with(self.conductr_version, self.nr_of_agent_instances,
                                                           self.license)

    def test_no_license_file(self):
        mock_get_license = MagicMock(side_effect=[
            (True, None),
            (True, None),
        ])
        mock_exists = MagicMock(return_value=False)
        mock_post_license = MagicMock()
        mock_validate_license_data = MagicMock()

        with patch('conductr_cli.license.get_license', mock_get_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license_validation.validate_license_data', mock_validate_license_data):
            license_validation.validate_license(self.conductr_version, self.core_addr,
                                                self.nr_of_agent_instances, self.license_file)

        expected_args = license_validation.LicenseArgs(self.core_addr)

        self.assertEqual([
            call(expected_args),
            call(expected_args)
        ], mock_get_license.call_args_list)

        mock_exists.assert_called_once_with(self.license_file)

        mock_post_license.assert_not_called()

        mock_validate_license_data.assert_called_once_with(self.conductr_version, self.nr_of_agent_instances,
                                                           None)

    def test_no_license_support(self):
        mock_get_license = MagicMock(return_value=(False, None))
        mock_exists = MagicMock()
        mock_post_license = MagicMock()
        mock_validate_license_data = MagicMock()

        with patch('conductr_cli.license.get_license', mock_get_license), \
                patch('os.path.exists', mock_exists), \
                patch('conductr_cli.license.post_license', mock_post_license), \
                patch('conductr_cli.license_validation.validate_license_data', mock_validate_license_data):
            license_validation.validate_license(self.conductr_version, self.core_addr,
                                                self.nr_of_agent_instances, self.license_file)

        expected_args = license_validation.LicenseArgs(self.core_addr)

        mock_get_license.assert_called_once_with(expected_args)

        mock_exists.assert_not_called()

        mock_post_license.assert_not_called()

        mock_validate_license_data.assert_not_called()


class TestValidateLicenseData(TestCase):
    conductr_version = '2.1.0'

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    nr_of_agent_instances = 3

    def test_validate(self):
        mock_validate_version = MagicMock()
        mock_validate_nr_of_agents = MagicMock()
        mock_validate_expiry = MagicMock()
        mock_validate_grants = MagicMock()

        with patch('conductr_cli.license_validation.validate_version', mock_validate_version), \
                patch('conductr_cli.license_validation.validate_nr_of_agents', mock_validate_nr_of_agents), \
                patch('conductr_cli.license_validation.validate_expiry', mock_validate_expiry), \
                patch('conductr_cli.license_validation.validate_grants', mock_validate_grants):
            license_validation.validate_license_data(self.conductr_version, self.nr_of_agent_instances,
                                                     self.license)

        mock_validate_version.assert_called_once_with(self.conductr_version, self.license)
        mock_validate_nr_of_agents.assert_called_once_with(self.nr_of_agent_instances, self.license)
        mock_validate_expiry.assert_called_once_with(self.license)
        mock_validate_grants.assert_called_once_with(self.license)


class TestValidateVersion(TestCase):
    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*', '2.2.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    def test_license_multiple_versions(self):
        license_validation.validate_version('2.1.0-SNAPSHOT', self.license)
        license_validation.validate_version('2.1.5', self.license)
        license_validation.validate_version('2.2.3', self.license)

    def test_license_single_version(self):
        license_single_version = self.license.copy()
        license_single_version.update({'conductrVersions': ['2.1.*']})

        license_validation.validate_version('2.1.5', self.license)

    def test_license_version_not_present(self):
        license_no_version = self.license.copy()

        del license_no_version['conductrVersions']

        license_validation.validate_version('2.1.0-SNAPSHOT', license_no_version)
        license_validation.validate_version('2.0.0', license_no_version)
        license_validation.validate_version('2.1.5', license_no_version)
        license_validation.validate_version('2.2.3', license_no_version)

    def test_license_empty_versions(self):
        license_no_version = self.license.copy()
        license_no_version.update({'conductrVersions': []})

        license_validation.validate_version('2.1.0-SNAPSHOT', license_no_version)
        license_validation.validate_version('2.0.0', license_no_version)
        license_validation.validate_version('2.1.5', license_no_version)
        license_validation.validate_version('2.2.3', license_no_version)

    def test_invalid_version(self):
        self.assertRaises(LicenseValidationError, license_validation.validate_version, '2.0.1-SNAPSHOT', self.license)
        self.assertRaises(LicenseValidationError, license_validation.validate_version, '2.0.0', self.license)
        self.assertRaises(LicenseValidationError, license_validation.validate_version, '2.3.0', self.license)


class TestValidateNrOfAgents(TestCase):
    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*', '2.2.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    def test_less_then_allowed(self):
        license_validation.validate_nr_of_agents(2, self.license)

    def test_equals_to_allowed(self):
        license_validation.validate_nr_of_agents(3, self.license)

    def test_more_then_allowed(self):
        self.assertRaises(LicenseValidationError, license_validation.validate_nr_of_agents, 5, self.license)

    def test_nr_of_agents_missing(self):
        license_no_agents = self.license.copy()
        del license_no_agents['maxConductrAgents']

        license_validation.validate_nr_of_agents(1, license_no_agents)


class TestValidateExpiry(TestCase):
    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*', '2.2.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    def test_not_expired(self):
        mock_calculate_days_to_expiry = MagicMock(return_value=30)
        with patch('conductr_cli.license.calculate_days_to_expiry', mock_calculate_days_to_expiry):
            license_validation.validate_expiry(self.license)

    def test_expired(self):
        mock_calculate_days_to_expiry = MagicMock(return_value=-1)
        with patch('conductr_cli.license.calculate_days_to_expiry', mock_calculate_days_to_expiry):
            self.assertRaises(LicenseValidationError, license_validation.validate_expiry, self.license)

    def test_expiry_not_present(self):
        mock_calculate_days_to_expiry = MagicMock(return_value=-1)

        license_no_expiry = self.license.copy()
        del license_no_expiry['expires']

        with patch('conductr_cli.license.calculate_days_to_expiry', mock_calculate_days_to_expiry):
            license_validation.validate_expiry(license_no_expiry)

        mock_calculate_days_to_expiry.assert_not_called()


class TestValidateGrants(TestCase):
    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*', '2.2.*'],
        'expires': '2018-03-01T00:00:00Z',
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    def test_conductr_grants_present(self):
        license_validation.validate_grants(self.license)

    def test_conductr_grants_empty(self):
        license_no_grants = self.license.copy()
        license_no_grants.update({'grants': ['others']})

        self.assertRaises(LicenseValidationError, license_validation.validate_grants, license_no_grants)

    def test_conductr_grants_not_present(self):
        license_no_grants = self.license.copy()
        del license_no_grants['grants']

        self.assertRaises(LicenseValidationError, license_validation.validate_grants, license_no_grants)


class TestCanRunVersion(TestCase):
    def test_major_version(self):
        self.assertTrue(license_validation.can_run_version('2.*.*', '2.1.5-alpha.1'))
        self.assertTrue(license_validation.can_run_version('2.*.*', '2.1.5'))
        self.assertTrue(license_validation.can_run_version('2.*.*', '2.0.1'))
        self.assertTrue(license_validation.can_run_version('2.*.*', '2.0.0'))

        self.assertTrue(license_validation.can_run_version('2.*', '2.1.5-alpha.1'))
        self.assertTrue(license_validation.can_run_version('2.*', '2.1.5'))
        self.assertTrue(license_validation.can_run_version('2.*', '2.0.1'))
        self.assertTrue(license_validation.can_run_version('2.*', '2.0.0'))

        self.assertFalse(license_validation.can_run_version('1.*.*', '2.1.5-alpha.1'))
        self.assertFalse(license_validation.can_run_version('1.*.*', '2.1.5'))
        self.assertFalse(license_validation.can_run_version('1.*.*', '2.0.1'))
        self.assertFalse(license_validation.can_run_version('1.*.*', '2.0.0'))

        self.assertFalse(license_validation.can_run_version('1.*', '2.1.5-alpha.1'))
        self.assertFalse(license_validation.can_run_version('1.*', '2.1.5'))
        self.assertFalse(license_validation.can_run_version('1.*', '2.0.1'))
        self.assertFalse(license_validation.can_run_version('1.*', '2.0.0'))

    def test_major_minor_version(self):
        self.assertTrue(license_validation.can_run_version('2.1.*', '2.1.5-alpha.1'))
        self.assertTrue(license_validation.can_run_version('2.1.*', '2.1.5'))

        self.assertFalse(license_validation.can_run_version('2.1.*', '2.2.1-alpha.1'))
        self.assertFalse(license_validation.can_run_version('2.1.*', '2.2.1'))
        self.assertFalse(license_validation.can_run_version('2.1.*', '2.1'))
        self.assertFalse(license_validation.can_run_version('2.1.*', '2'))

    def test_major_minor_patch_version(self):
        self.assertTrue(license_validation.can_run_version('2.1.5', '2.1.5'))
        self.assertFalse(license_validation.can_run_version('2.1.5', '2.2.1'))

    def test_major_minor_patch_label(self):
        self.assertTrue(license_validation.can_run_version('2.1.5-alpha.1', '2.1.5-alpha.1'))

        self.assertFalse(license_validation.can_run_version('2.1.5-alpha.1', '2.1.5-alpha.2'))
        self.assertFalse(license_validation.can_run_version('2.1.5-alpha.1', '2.2.1-alpha.1'))

    def test_any_version(self):
        self.assertTrue(license_validation.can_run_version('*.*.*', '2.1.5'))
        self.assertTrue(license_validation.can_run_version('*', '2.1.5'))
