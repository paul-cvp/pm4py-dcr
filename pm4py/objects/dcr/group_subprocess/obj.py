from pm4py.objects.dcr.milestone_noresponse.obj import MilestoneNoResponseDcrGraph
from typing import Set, Dict


class GroupSubprocessDcrGraph(MilestoneNoResponseDcrGraph):

    def __init__(self, template=None):
        super().__init__(template)
        self.__nestedgroups = {} if template is None else template['nestedgroups']
        self.__subprocesses = {} if template is None else template['subprocesses']
        self.__nestedgroups_map = {} if template is None else template['nestedgroupsMap']
        if len(self.__nestedgroups_map) == 0 and len(self.__nestedgroups) > 0:
            self.__nestedgroups_map = {}
            for group, events in self.__nestedgroups.items():
                for e in events:
                    self.__nestedgroups_map[e] = group

    def obj_to_template(self):
        res = super().obj_to_template()
        res['nestedgroups'] = self.__nestedgroups
        res['subprocesses'] = self.__subprocesses
        res['nestedgroupsMap'] = self.__nestedgroups_map
        return res

    @property
    def nestedgroups(self) -> Dict[str, Set[str]]:
        return self.__nestedgroups

    @nestedgroups.setter
    def nestedgroups(self, ng):
        self.__nestedgroups = ng

    @property
    def nestedgroups_map(self) -> Dict[str, str]:
        return self.__nestedgroups_map

    @nestedgroups_map.setter
    def nestedgroups_map(self, ngm):
        self.__nestedgroups_map = ngm

    @property
    def subprocesses(self) -> Dict[str, Set[str]]:
        return self.__subprocesses

    @subprocesses.setter
    def subprocesses(self, sps):
        self.__subprocesses = sps