from conductr_cli.exceptions import BundleConfValidationError
from conductr_cli.data_structure_utils import sort_dict

BUNDLE_CONF_PROPERTIES = sort_dict(
    {
        'annotations': {
            'required': False,
            'emptiness_check': False
        },
        'compatibilityVersion': {
            'required': True,
            'emptiness_check': True,
            'alias': 'compatibility-version'
        },
        'components': {
            'required': True,
            'emptiness_check': True,
            'iterate-child-level': True,
            'child': {
                'description': {
                    'required': True,
                    'emptiness_check': False,
                },
                'endpoints': {
                    'required': False,
                    'emptiness_check': False,
                    'iterate-child-level': True,
                    'child': {
                        'acls': {
                            'required': False,
                            'emptiness_check': False
                        },
                        'bind-port': {
                            'required': True,
                            'emptiness_check': False
                        },
                        'bind-protocol': {
                            'required': True,
                            'emptiness_check': True
                        },
                        'service-name': {
                            'required': False,
                            'emptiness_check': True
                        },
                        'services': {
                            'required': False,
                            'emptiness_check': False
                        }
                    }
                },
                'file-system-type': {
                    'required': True,
                    'emptiness_check': True
                },
                'start-command': {
                    'required': True,
                    'emptiness_check': False
                },
                'volumes': {
                    'required': False,
                    'emptiness_check': True
                }
            }
        },
        'diskSpace': {
            'required': True,
            'emptiness_check': False,
            'alias': 'disk-space'
        },
        'memory': {
            'required': True,
            'emptiness_check': False
        },
        'name': {
            'required': True,
            'emptiness_check': True
        },
        'nrOfCpus': {
            'required': True,
            'emptiness_check': False
        },
        'roles': {
            'required': True,
            'emptiness_check': False
        },
        'system': {
            'required': True,
            'emptiness_check': True
        },
        'systemVersion': {
            'required': True,
            'emptiness_check': True,
            'alias': 'system-version'
        },
        'tags': {
            'required': False,
            'emptiness_check': False
        },
        'version': {
            'required': True,
            'emptiness_check': True
        }
    }
)


def validate_bundle_conf(bundle_conf, excludes):
    error_messages = []

    bundle_conf_non_empty_error = assert_bundle_conf_non_empty(bundle_conf)
    if bundle_conf_non_empty_error:
        error_messages.append(bundle_conf_non_empty_error)

    if 'property-name' not in excludes:
        property_names_error = assert_property_names(bundle_conf)
        if property_names_error:
            error_messages.append(property_names_error)

    if 'empty-property' not in excludes:
        properties_non_empty_error = assert_properties_non_empty(bundle_conf)
        if properties_non_empty_error:
            error_messages.append(properties_non_empty_error)

    if 'required' not in excludes:
        required_properties_error = assert_required_properties(bundle_conf)
        if required_properties_error:
            error_messages.append(required_properties_error)

    if error_messages:
        raise BundleConfValidationError(error_messages)


def assert_bundle_conf_non_empty(bundle_conf):
    if bundle_conf:
        return None
    else:
        return 'The bundle.conf is empty'


def assert_properties_non_empty(bundle_conf):
    empty_properties = collect_invalid_properties('empty-property', bundle_conf, BUNDLE_CONF_PROPERTIES, [])
    if empty_properties:
        return 'The following properties are not allowed to be empty: {}'.format(', '.join(empty_properties))
    else:
        return None


def assert_property_names(bundle_conf):
    invalid_property_names = collect_invalid_properties('property-name', bundle_conf, BUNDLE_CONF_PROPERTIES, [])

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
                                                   prop['child'],
                                                   missing_props,
                                                   update_parent_key(parent_key, prop_name, child_config_key))
                else:
                    collect_missing_properties(child_config,
                                               prop['child'],
                                               missing_props,
                                               update_parent_key(parent_key, prop_name))
        return missing_props

    missing_properties = collect_missing_properties(bundle_conf, BUNDLE_CONF_PROPERTIES, [])
    if missing_properties:
        return 'The following required properties are not declared: {}'.format(', '.join(missing_properties))
    else:
        return None


def collect_invalid_properties(assertion, config, props, invalid_props, parent_key=None):
    for config_key in config:
        if assertion == 'property-name' and \
                all(config_key != valid_key
                    for prop_key, prop in props.items()
                    for valid_key in possible_property_names(prop_key, prop)):
            invalid_props.append(full_property_name(parent_key, config_key))
        elif assertion == 'empty-property' \
                and config_key in props and props[config_key]['emptiness_check'] \
                and not config[config_key]:
            invalid_props.append(full_property_name(parent_key, config_key))

        if isinstance(config[config_key], dict):
            child_config = config[config_key]
            prop = props[config_key]
            if 'child' in prop:
                if 'iterate-child-level' in prop and prop['iterate-child-level']:
                    for child_config_key in child_config:
                        collect_invalid_properties(assertion,
                                                   child_config[child_config_key],
                                                   prop['child'],
                                                   invalid_props,
                                                   update_parent_key(parent_key, config_key, child_config_key))
                else:
                    collect_invalid_properties(assertion,
                                               child_config,
                                               prop['child'],
                                               invalid_props,
                                               update_parent_key(parent_key, config_key))
    return invalid_props


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
