import json
from enum import Enum
from pyhocon import ConfigTree, ConfigList
from collections import defaultdict


class Endpoint:
    def __init__(self, endpoint_dict):
        self.name = endpoint_dict['name']

        if 'component' in endpoint_dict:
            self.component = endpoint_dict['component']

        self.acls = []
        grouped_acls = defaultdict(list)
        if 'acls' in endpoint_dict:
            for acl in endpoint_dict['acls']:
                grouped_acls[ProtocolFamily[acl['protocol']]].append(acl)
            for protocol_family, entries in grouped_acls.items():
                self.acls.append(RequestAcl(protocol_family, entries))

        if 'bind-protocol' in endpoint_dict:
            self.bind_protocol = endpoint_dict['bind-protocol']
        elif not grouped_acls:
            self.bind_protocol = 'tcp'
        elif len(grouped_acls) == 1:
            self.bind_protocol = next(iter(grouped_acls.keys())).name
        else:
            protocol_families = [key.name for key in grouped_acls.keys()]
            raise AmbigousBindProtocolError('could not set the bind protocol for an endpoint. '
                                            'bind-protocol is not specified and '
                                            'acls contain multiple protocol families: {}'.format(protocol_families))

        if 'bind-port' in endpoint_dict:
            self.bind_port = endpoint_dict['bind-port']
        else:
            self.bind_port = 0

        if 'service-name' in endpoint_dict:
            self.service_name = endpoint_dict['service-name']
        else:
            self.service_name = None

    def hocon(self):
        endpoint_tree = ConfigTree()
        endpoint_tree.put('{}.bind-protocol'.format(self.name), self.bind_protocol)
        endpoint_tree.put('{}.bind-port'.format(self.name), self.bind_port)
        if self.service_name:
            endpoint_tree.put('{}.service-name'.format(self.name), self.service_name)
        for acl in self.acls:
            acl_list = ConfigList()
            acl_list.append(acl.hocon())
            endpoint_tree.put('{}.acls'.format(self.name), acl_list)
        return endpoint_tree


class RequestAcl:
    def __init__(self, protocol_family, entries):
        self.request_mappings = []
        for mapping in entries:
            if mapping['value'].startswith('[') and mapping['value'].endswith(']'):
                ports = json.loads(mapping['value'])
                if protocol_family is ProtocolFamily.tcp:
                    self.request_mappings.append(TcpRequest(ports))
                elif protocol_family is ProtocolFamily.udp:
                    self.request_mappings.append(UdpRequest(ports))
            elif mapping['value'].startswith('/'):
                if protocol_family is ProtocolFamily.http:
                    self.request_mappings.append(HttpRequest(mapping['match'], mapping['value'], mapping['rewrite']))

    def hocon(self):
        acl_tree = ConfigTree()
        for mapping in self.request_mappings:
            acl_tree.put('{}.requests'.format(mapping.protocol_family.name), mapping.hocon(), append=True)
        return acl_tree


class ProtocolFamily(Enum):
    tcp = 1
    udp = 2
    http = 3


class TcpRequest:
    protocol_family = ProtocolFamily.tcp

    def __init__(self, ports):
        self.ports = ports

    def hocon(self):
        return ConfigList(self.ports)


class UdpRequest:
    protocol_family = ProtocolFamily.udp

    def __init__(self, ports):
        self.ports = ports

    def hocon(self):
        return ConfigList(self.ports)


class HttpRequest:
    protocol_family = ProtocolFamily.http

    def __init__(self, match, value, rewrite):
        self.match = match
        self.value = value
        self.rewrite = rewrite
        self.method = None

    def hocon(self):
        request_tree = ConfigTree()
        request_tree.put(self.match if self.match else 'path-beg', self.value)
        if self.method:
            request_tree.put('method', self.method)
        if self.rewrite:
            request_tree.put('rewrite', self.rewrite)
        request_list = ConfigList()
        request_list.append(request_tree)
        return request_list


class AmbigousBindProtocolError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
