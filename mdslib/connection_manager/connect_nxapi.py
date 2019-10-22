import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from builtins import range

from urllib3.exceptions import InsecureRequestWarning

from .errors import NXOSError

log = logging.getLogger(__name__)


class ConnectNxapi(object):
    """

    """

    def __init__(self, host, username, password, transport=u'https', port=None, verify_ssl=True):
        """

        Args:
            host:
            username:
            password:
            transport:
            port:
            verify_ssl:
        """
        if transport not in ['http', 'https']:
            raise NXOSError('\'%s\' is an invalid transport.' % transport)

        if port is None:
            if transport == 'http':
                port = 8081
            elif transport == 'https':
                port = 8443

        self.url = u'%s://%s:%s/ins' % (transport, host, port)
        log.debug("URL is : " + self.url)
        self.headers = {u'content-type': u'application/json-rpc'}
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        if not self.verify_ssl:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            log.debug(
                "Warning!! 'verify_ssl' flag is set to False, hence ignoring the 'InsecureRequestWarning' exception")
        else:
            log.debug("'verify_ssl' flag is set to True, so hopefully SSL connections is setup")

    def _build_payload(self, commands, method, rpc_version=u'2.0'):
        """

        Args:
            commands:
            method:
            rpc_version:

        Returns:

        """
        payload_list = []

        id_num = 1
        for command in commands:
            payload = dict(jsonrpc=rpc_version,
                           method=method,
                           params=dict(cmd=command, version=1),
                           id=id_num, )

            payload_list.append(payload)
            id_num += 1

        log.debug("Payload list is :")
        log.debug(payload_list)
        return payload_list

    def send_request(self, commands, method=u'cli', timeout=30):
        """

        Args:
            commands:
            method:
            timeout:

        Returns:
            response_list
        """
        timeout = int(timeout)
        payload_list = self._build_payload(commands, method)
        # print(timeout)
        response = requests.post(self.url,
                                 timeout=timeout,
                                 data=json.dumps(payload_list),
                                 headers=self.headers,
                                 auth=HTTPBasicAuth(self.username, self.password),
                                 verify=self.verify_ssl)

        log.debug(response)
        response_list = json.loads(response.text)

        if isinstance(response_list, dict):
            response_list = [response_list]

        for i in range(len(commands)):
            response_list[i][u'command'] = commands[i]

        return response_list
