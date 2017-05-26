from conductr_cli.exceptions import BundleConfValidationError
from conductr_cli.data_structure_utils import sort_dict

BUNDLE_CONF_PROPERTIES = sort_dict(
    {
        'annotations': {
            'required': False
        },
        'compatibilityVersion': {
            'required': True,
            'alias': 'compatibility-version'
        },
        'components': {
            'required': True,
            'iterate-child-level': True,
            'child': {
                'description': {
                    'required': True,
                },
                'endpoints': {
                    'required': False,
                    'iterate-child-level': True,
                    'child': {
                        'acls': {
                            'required': False
                        },
                        'bind-port': {
                            'required': True
                        },
                        'bind-protocol': {
                            'required': True
                        },
                        'service-name': {
                            'required': False
                        },
                        'services': {
                            'required': False
                        }
                    }
                },
                'file-system-type': {
                    'required': True
                },
                'start-command': {
                    'required': True
                },
                'volumes': {
                    'required': False
                }
            }
        },
        'diskSpace': {
            'required': True,
            'alias': 'disk-space'
        },
        'memory': {
            'required': True
        },
        'name': {
            'required': True
        },
        'nrOfCpus': {
            'required': True
        },
        'roles': {
            'required': True
        },
        'system': {
            'required': True
        },
        'systemVersion': {
            'required': True,
            'alias': 'system-version'
        },
        'tags': {
            'required': False
        },
        'version': {
            'required': True
        }
    }
)


def validate_bundle_conf(bundle_conf, excludes):
    error_messages = []

    non_empty_error = assert_non_empty(bundle_conf)
    if non_empty_error:
        error_messages.append(non_empty_error)

    if 'property-names' not in excludes:
        property_names_error = assert_property_names(bundle_conf)
        if property_names_error:
            error_messages.append(property_names_error)

    if 'required' not in excludes:
        required_properties_error = assert_required_properties(bundle_conf)
        if required_properties_error:
            error_messages.append(required_properties_error)

    if error_messages:
        raise BundleConfValidationError(error_messages)


def assert_non_empty(bundle_conf):
    if bundle_conf:
        return None
    else:
        return 'The bundle.conf is empty'


def assert_property_names(bundle_conf):
    def collect_invalid_names(config, props, invalid_props, parent_key=None):
        for config_key in config:
            if all(config_key != valid_key
                   for prop_key, prop in props.items()
                   for valid_key in possible_property_names(prop_key, prop)):
                invalid_props.append(full_property_name(parent_key, config_key))
            if isinstance(config[config_key], dict):
                child_config = config[config_key]
                prop = props[config_key]
                if 'child' in prop:
                    if 'iterate-child-level' in prop and prop['iterate-child-level']:
                        for child_config_key in child_config:
                            collect_invalid_names(child_config[child_config_key],
                                                  prop['child'], invalid_props,
                                                  update_parent_key(parent_key, config_key, child_config_key))
                    else:
                        collect_invalid_names(child_config,
                                              prop['child'], invalid_props,
                                              update_parent_key(parent_key, config_key))
        return invalid_props

    invalid_property_names = collect_invalid_names(bundle_conf, BUNDLE_CONF_PROPERTIES, [])

    if invalid_property_names:
        return 'The following property names are invalid: {}'.format(', '.join(sorted(invalid_property_names)))
    else:
        return None


def assert_required_properties(bundle_conf):
    def collect_missing_properties(config, props, missing_props, parent_key=None):
        for prop_name, prop in props.items():
            if prop['required']:
                if all(name not in config for name in possible_property_names(prop_name, prop)):
                    missing_props.append(full_property_name(parent_key, prop_name))
            if 'child' in prop and prop_name in config:
                child_config = config[prop_name]
                if 'iterate-child-level' in prop and prop['iterate-child-level']:
                    for child_config_key in child_config:
                        collect_missing_properties(child_config[child_config_key],
                                                   prop['child'], missing_props,
                                                   update_parent_key(parent_key, prop_name, child_config_key))
                else:
                    collect_missing_properties(child_config,
                                               prop['child'], missing_props,
                                               update_parent_key(parent_key, prop_name))
        return missing_props

    missing_properties = collect_missing_properties(bundle_conf, BUNDLE_CONF_PROPERTIES, [])
    if missing_properties:
        return 'The following required properties are not declared: {}'.format(', '.join(missing_properties))
    else:
        return None


def possible_property_names(name, prop):
    return [name] if 'alias' not in prop else [name, prop['alias']]


def full_property_name(parent_key, property_name):
    return '{}.{}'.format(parent_key, property_name) if parent_key else property_name


def update_parent_key(parent_key, prop_name, child_key=None):
    if parent_key and child_key:
        return '{}.{}.{}'.format(parent_key, prop_name, child_key)
    elif parent_key and not child_key:
        return '{}.{}'.format(parent_key, prop_name)
    elif not parent_key and child_key:
        return '{}.{}'.format(prop_name, child_key)
    else:
        return prop_name
