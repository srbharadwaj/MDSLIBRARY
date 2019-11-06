__author__ = 'Suhas Bharadwaj (subharad)'

import logging
import requests
from mdslib.connection_manager.connect_nxapi import ConnectNxapi
from mdslib.connection_manager.errors import CLIError
from mdslib.parsers.system.shtopology import ShowTopology
from mdslib.modules.devicealias import DeviceAlias


import time

log = logging.getLogger(__name__)


def log_exception(logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    @param logger: The logging object
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                # log the exception
                err = "There was an exception in  "
                err += func.__name__
                logger.exception(err)
            # re-raise the exception
            raise

        return wrapper

    return decorator


class Switch(object):
    """
    The is a switch __connection class which is used to discover switch via nxapi
    """

    def __init__(self, ip_address, username, password, connection_type='https', port=8443, timeout=30, verify_ssl=True):
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
        self.port = port
        self.timeout = timeout
        self.__verify_ssl = verify_ssl

        log.info("Opening up a connection for switch with ip " + ip_address)
        self.__connection = ConnectNxapi(ip_address, username, password, transport=connection_type, port=port,
                                         verify_ssl=verify_ssl)

        self.can_connect = False
        # Get version of the switch and log it
        self.log_version()

    @log_exception(log)
    def log_version(self):
        try:
            log.debug(self.version)
            self.can_connect = True
        except requests.exceptions.ConnectionError as e:
            msg = "ERROR!! Connection refused for the switch : " + self.ipaddr + \
                  " Verify that the switch has " + self.connectiontype + " configured with port " + str(self.port)
            log.error(msg)

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

        error = command_response.get(u'clierror')
        if error:
            command = command_response.get(u'input')
            raise CLIError(command, error)

    def _cli_command(self, commands, rpc=u'2.0', method=u'cli'):
        if not isinstance(commands, list):
            commands = [commands]

        conn_response = self.__connection.send_request(commands, rpc_version=rpc, method=method, timeout=self.timeout)
        log.debug("conn_response is")
        log.debug(conn_response)

        text_response_list = []
        if rpc is not None:
            for command_response in conn_response:
                self._cli_error_check(command_response)
                text_response_list.append(command_response[u'result'])
        else:
            text_response_list = []
            for command_response in conn_response:
                if 'ins_api' in command_response.keys():
                    retout = command_response['ins_api']['outputs']['output']
                    if type(retout) is dict:
                        fullout = [retout]
                    else:
                        fullout = retout
                    for eachoutput in fullout:
                        # print(eachoutput)
                        self._cli_error_check(eachoutput)
                        text_response_list.append(eachoutput[u'body'])
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

    def config(self, command, rpc=u'2.0', method=u'cli'):
        """Send a configuration command.
        Args:
            command (str): The command to send to the device.
        Raises:
            CLIError: If there is a problem with the supplied command.
        """
        commands = [command]
        list_result = self.config_list(commands, rpc, method)
        return list_result[0]

    def config_list(self, commands, rpc=u'2.0', method=u'cli'):
        """Send a list of configuration commands.
        Args:
            commands (list): A list of commands to send to the device.
        Raises:
            CLIError: If there is a problem with one of the commands in the list.
        """
        return_list = self._cli_command(commands, rpc=rpc, method=method)

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

    def is_npv_switch(self):
        jsonoutput = True
        try:
            flist = self.show("show feature")
        except CLIError as c:
            if "cannot be parsed by the server" in c.message:
                jsonoutput = False
                flist = self.show("show feature", raw_text=True)
                log.debug(c)
            else:
                log.error(
                    "Could not discover the entire fabric, since 'show feature' could not be run on the switch " + self.ipaddr)

        if not jsonoutput:
            for eachline in flist.splitlines():
                if 'npv' in eachline:
                    if 'enabled' in eachline.lower():
                        return True
                    else:
                        return False
        else:
            flist = flist['TABLE_cfcFeatureCtrl2Table']['ROW_cfcFeatureCtrl2Table']
            # print(flist)
            for eachf in flist:
                if eachf['cfcFeatureCtrlName2'].strip() == 'npv':
                    if eachf['cfcFeatureCtrlOpStatus2'].strip().lower() == 'enabled':
                        return True
                    else:
                        return False
        return False

    def get_peer_switches(self):
        peer_sw_list = []
        shtopoout = self.show("show topology", raw_text=True)
        sh = ShowTopology(shtopoout.splitlines())
        for vsan, interfacelist in sh.parse_data.items():
            for eachinterface in interfacelist:
                peer_sw_ip = eachinterface['peer_ip']
                peer_sw_list.append(peer_sw_ip)
        peerlist = list(dict.fromkeys(peer_sw_list))
        log.debug("Peer NPIV list of switch : " + self.ipaddr + " are: ")
        log.debug(peerlist)
        return peerlist

    def get_peer_npv_switches(self):
        retout = []
        fcnsout = self.show("show fcns database detail")['TABLE_fcns_vsan']['ROW_fcns_vsan']
        for eachline in fcnsout:
            temp = eachline['TABLE_fcns_database']['ROW_fcns_database']
            # print(temp)
            if type(temp['fc4_types_fc4_features']) is str:
                if temp['fc4_types_fc4_features'].strip() == 'npv':
                    ip = temp['node_ip_addr']
                    retout.append(ip)
        peerlist = list(dict.fromkeys(retout))
        log.debug("Peer NPV list of switch : " + self.ipaddr + " are: ")
        log.debug(peerlist)
        return peerlist
