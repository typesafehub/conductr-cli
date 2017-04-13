from enum import Enum
from pyhocon import ConfigTree, ConfigList


class Endpoint:
    def __init__(self, endpoint_dict):
        self.name = endpoint_dict['name']
        self.component = endpoint_dict['component']

        if 'bind-protocol' in endpoint_dict:
            self.bind_protocol = endpoint_dict['bind-protocol']
        else:
            self.bind_protocol = 'tcp'

        if 'bind-port' in endpoint_dict:
            self.bind_port = endpoint_dict['bind-port']
        else:
            self.bind_port = 0

        if 'service-name' in endpoint_dict:
            self.service_name = endpoint_dict['service-name']
        else:
            self.service_name = None

        self.acls = []
        if 'acls' in endpoint_dict:
            for acl in endpoint_dict['acls']:
                if acl.startswith('http'):
                    self.bind_protocol = 'http'
                self.acls.append(RequestAcl(acl))

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
    request_mappings = []

    def __init__(self, shorthand_string):
        protocol_family_string, other_parts = shorthand_string.split(':', 1)
        protocol_family = ProtocolFamily[protocol_family_string]

        if other_parts.startswith('[') and other_parts.endswith(']'):
            ports = [int(port.strip()) for port in other_parts[1:-1].split(',')]
            if protocol_family is ProtocolFamily.tcp:
                self.request_mappings.append(TcpRequest(ports))
            elif protocol_family is ProtocolFamily.udp:
                self.request_mappings.append(UdpRequest(ports))
        elif other_parts.startswith('/'):
            if protocol_family is ProtocolFamily.http:
                self.request_mappings.append(HttpRequest(other_parts))

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
    ports = []

    def __init__(self, ports):
        self.ports = ports

    def hocon(self):
        return ConfigList(self.ports)


class UdpRequest:
    protocol_family = ProtocolFamily.udp
    ports = []

    def __init__(self, ports):
        self.ports = ports

    def hocon(self):
        return ConfigList(self.ports)


class HttpRequest:
    protocol_family = ProtocolFamily.http
    method = None
    path_beg = None
    rewrite = None

    def __init__(self, path_beg):
        self.path_beg = path_beg

    def hocon(self):
        request_tree = ConfigTree()
        request_tree.put('path-beg', self.path_beg)
        if self.method:
            request_tree.put('method', self.method)
        if self.rewrite:
            request_tree.put('rewrite', self.rewrite)
        request_list = ConfigList()
        request_list.append(request_tree)
        return request_list
