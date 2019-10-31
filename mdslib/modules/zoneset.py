from mdslib.connection_manager.errors import CLIError
import logging

log = logging.getLogger(__name__)


class ZoneSet(object):
    def __init__(self, switch, vsan):
        self.__swobj = switch
        self.vsan = vsan

    @property
    def zonesets(self):
        raise NotImplemented  # TODO

    @property
    def active_zoneset(self):
        raise NotImplemented  # TODO

    @property
    def zoneset_names(self):
        raise NotImplemented  # TODO

    def create(self, name):
        raise NotImplemented  # TODO

    def delete(self, name):
        raise NotImplemented  # TODO

    def get_facts(self):
        raise NotImplemented  # TODO

    def add_members(self, name, members):
        raise NotImplemented  # TODO

    def remove_members(self, name, members):
        raise NotImplemented  # TODO

    def activate(self, name, action=True):
        raise NotImplemented  # TODO
