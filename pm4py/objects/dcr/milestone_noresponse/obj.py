from typing import Dict, Set

from pm4py.objects.dcr.roles.obj import RoleDcrGraph


class MilestoneNoResponseDcrGraph(RoleDcrGraph):

    def __init__(self, template=None):
        super().__init__(template)
        self.__milestonesFor = {} if template is None else template['milestonesFor']
        self.__noResponseTo = {} if template is None else template['noResponseTo']

    def obj_to_template(self):
        res = super().obj_to_template()
        res['milestonesFor'] = self.__milestonesFor
        res['noResponseTo'] = self.__noResponseTo
        return res

    @property
    def milestones(self) -> Dict[str, Set[str]]:
        return self.__milestonesFor

    @property
    def noresponses(self) -> Dict[str, Set[str]]:
        return self.__noResponseTo

    def get_constraints(self) -> int:
        no = super().get_constraints()
        for i in self.__milestonesFor.values():
            no += len(i)
        for i in self.__noResponseTo.values():
            no += len(i)
        return no

    def __eq__(self, other):
        return super().__eq__(other) and self.milestones == other.milestones and self.noresponses == other.noresponses

