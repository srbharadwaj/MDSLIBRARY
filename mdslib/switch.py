__author__ = 'Suhas Bharadwaj (subharad)'

import logging
from mdslib.connection_manager.connect_nxapi import ConnectNxapi
from mdslib.connection_manager.errors import CLIError
from mdslib.modules.devicealias import DeviceAlias
# from mdslib.modules.zone import DeviceAlias
# from mdslib.modules.zoneset import DeviceAlias


import time

log = logging.getLogger(__name__)


class Switch(object):
    """
    The is a switch __connection class which is used to discover switch via nxapi
    """

    def __init__(self, ip_address, username, password, connection_type='https', port=None, timeout=30, verify_ssl=True):
        """

        :param ip_address:
        :param username:
        :param password:
        :param url:
        """

        self.__ip_address = ip_address
        self.__username = username
        self.__password = password
        self.connectiontype = connection_type
        self.__port = port
        self.timeout = timeout
        self.__verify_ssl = verify_ssl

        log.debug("Opening up a __connection for the switch with ip " + ip_address)
        self.__connection = ConnectNxapi(ip_address, username, password, transport=connection_type, port=port,
                                         verify_ssl=verify_ssl)
        # self.__msg_format = "xml"
        # self.__cmd_type = "cli_show"

        # self.__log_info_about_url_msgfmt_cmdtype()

    @property
    def ipaddr(self):
        return self.__ip_address

    @property
    def switchname(self):
        return self.show("show switchname", raw_text=True)

    @switchname.setter
    def switchname(self, swname):
        self.config("switchname " + swname)

    @property
    def version(self):
        out = self.show("show version")
        if not out:
            return None
        fullversion = out['sys_ver_str']
        ver = fullversion.split()[0]
        return ver

    @property
    def model(self):
        out = self.show("show version")
        if not out:
            return None
        return out['chassis_id']

    @property
    def modules(self):
        out = self.show("show module")
        if not out:
            return None
        modinfo = out['TABLE_modinfo']['ROW_modinfo']
        # For 1RU switch modinfo is a dict
        if type(modinfo) is dict:
            return [modinfo]
        return modinfo

    def __log_info_about_url_msgfmt_cmdtype(self):
        """

        :return:
        """
        log.info("url is :" + self.getUrl())
        # print "url is :" + self.getUrl()
        log.info("msg fmt is :" + self.getMsgFormat())
        # print "msg fmt is :" + self.getMsgFormat()
        log.info("cmd type is :" + self.getCmdType())
        # print "cmd type is :" + self.getCmdType()

    def __validate_msgfmt_and_cmdtype(self, msg_fmt, cmd_type):
        """

        :param msg_fmt:
        :param cmd_type:
        :return:
        """
        if msg_fmt == "json-rpc":
            if cmd_type == "cli" or cmd_type == "cli_ascii":
                return True
            else:
                return False
        elif msg_fmt == "xml":
            if cmd_type == "cli_show" or cmd_type == "cli_show_ascii" or cmd_type == "cli_conf":
                return True
            else:
                return False
        elif msg_fmt == "json":
            if cmd_type == "cli_show" or cmd_type == "cli_show_ascii" or cmd_type == "cli_conf":
                return True
            else:
                return False
        else:
            return False

    def __set_msgfmt_and_cmdtype(self, msg_fmt='xml', cmd_type='cli_show'):
        """

        :param msg_fmt:
        :param cmd_type:
        :return:
        """
        if self.__validate_msgfmt_and_cmdtype(msg_fmt, cmd_type):
            self.__msg_format = msg_fmt
            self.__cmd_type = cmd_type
        else:
            # TODO
            # Throw proper critical warning
            print("TODO")
            raise NotImplementedError

        self.__log_info_about_url_msgfmt_cmdtype()

    def _cli_error_check(self, command_response):
        error = command_response.get(u'error')
        if error:
            command = command_response.get(u'command')
            if u'data' in error:
                raise CLIError(command, error[u'data'][u'msg'])
            else:
                raise CLIError(command, 'Invalid command.')

    def _cli_command(self, commands, method=u'cli'):
        if not isinstance(commands, list):
            commands = [commands]

        conn_response = self.__connection.send_request(commands, method=method, timeout=self.timeout)

        text_response_list = []
        for command_response in conn_response:
            self._cli_error_check(command_response)
            text_response_list.append(command_response[u'result'])

        return text_response_list

    def show(self, command, raw_text=False):
        """Send a show command.
        Args:
            command (str): The command to send to the switch.
        Keyword Args:
            raw_text (bool): Whether to return raw text or structured data.
        Returns:
            The output of the show command, which could be raw text or structured data.
        """

        commands = [command]
        list_result = self.show_list(commands, raw_text)
        if list_result:
            return list_result[0]
        else:
            return {}

    def show_list(self, commands, raw_text=False):
        """Send a list of show commands.
        Args:
            commands (list): A list of commands to send to the switch.
        Keyword Args:
            raw_text (bool): Whether to return raw text or structured data.
        Returns:
            A list of outputs for each show command
        """
        return_list = []
        if raw_text:
            response_list = self._cli_command(commands, method=u'cli_ascii')
            for response in response_list:
                if response:
                    return_list.append(response[u'msg'].strip())
        else:
            response_list = self._cli_command(commands)
            for response in response_list:
                if response:
                    return_list.append(response[u'body'])

        log.debug("Show commands sent are :")
        log.debug(commands)
        log.debug("Result got was :")
        log.debug(return_list)

        return return_list

    def config(self, command):
        """Send a configuration command.
        Args:
            command (str): The command to send to the device.
        Raises:
            CLIError: If there is a problem with the supplied command.
        """
        commands = [command]
        list_result = self.config_list(commands)
        return list_result[0]

    def config_list(self, commands):
        """Send a list of configuration commands.
        Args:
            commands (list): A list of commands to send to the device.
        Raises:
            CLIError: If there is a problem with one of the commands in the list.
        """
        return_list = self._cli_command(commands)

        log.debug("Config commands sent are :")
        log.debug(commands)
        log.debug("Result got was :")
        log.debug(return_list)

        return return_list

    def reload(self, module: int = None, timeout: int = 300, copyrs=True):

        if module is None:
            # Switch reload
            cmd = "terminal dont-ask ; reload"
            if copyrs:
                log.info("Reloading switch after copy running-config startup-config")
                crs = self.show("copy running-config startup-config", raw_text=True)
                if 'Copy complete' in crs:
                    log.info('copy running-config startup-config is successful')
                else:
                    log.error('copy running-config startup-config failed')
                    log.error(crs.split("\n")[-1])
                    return {'FAILED': crs}
            else:
                log.info("Reloading switch without copy running-config startup-config")

        else:
            # Module reload
            mod = str(module)
            cmd = "terminal dont-ask ; reload module " + mod
            if copyrs:
                log.info("Reloading the module " + mod + " after copy running-config startup-config")
                crs = self.show("copy running-config startup-config", raw_text=True)
                if 'Copy complete' in crs:
                    log.info('copy running-config startup-config is successful')
                else:
                    log.error('copy running-config startup-config failed')
                    log.error(crs.split("\n")[-1])
                    return {'FAILED': crs}
            else:
                log.info("Reloading the module " + mod + " without copy running-config startup-config")

        shmod_before = self.show("show module", raw_text=True).split("\n")
        shintb_before = self.show("show interface brief", raw_text=True).split("\n")
        log.info("Reloading please wait...")
        out = self.config(cmd)
        time.sleep(timeout)
        shmod_after = self.show("show module", raw_text=True).split("\n")
        shintb_after = self.show("show interface brief", raw_text=True).split("\n")

        shcores = self.show("show cores", raw_text=True).split("\n")
        if len(shcores) > 2:
            log.error(
                "Cores present on the switch, please check the switch and also the log file")
            log.error(shcores[2:])
            return {'FAILED': out}

        if shmod_before == shmod_after:
            log.info("'show module' is correct after reload")
        else:
            log.error(
                "'show module' output is different from before and after reload, please check the log file")
            log.debug("'show module' before reload")
            log.debug(shmod_before)
            log.debug("'show module' after reload")
            log.debug(shmod_after)

            bset = set(shmod_before)
            aset = set(shmod_after)
            bef = list(bset - aset)
            aft = list(aset - bset)
            log.debug("diff of before after reload")
            log.debug(bef)
            log.debug(aft)
            return {'FAILED': [bef, aft]}

        if shintb_before == shintb_after:
            log.info("'show interface brief' is correct after reload")
        else:
            log.error(
                "'show interface brief' output is different from before and after reload, please check the log file")
            log.debug("'show interface brief' before reload")
            log.debug(shintb_before)
            log.debug("'show interface brief' after reload")
            log.debug(shintb_after)

            bset = set(shintb_before)
            aset = set(shintb_after)
            bef = list(bset - aset)
            aft = list(aset - bset)
            log.debug("diff of before after reload")
            log.debug(bef)
            log.debug(aft)
            return {'FAILED': [bef, aft]}
        log.info("Reload was successful")
        return {'SUCESS': None}

    def get_device_alias_handler(self):
        return DeviceAlias(self)
