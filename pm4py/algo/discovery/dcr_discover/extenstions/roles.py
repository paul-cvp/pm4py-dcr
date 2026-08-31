import pandas as pd
from typing import Optional, Any, Union, Dict
import pm4py
from pm4py.objects.dcr.obj import DcrGraph
from pm4py.util import exec_utils, constants, xes_constants
from pm4py.objects.dcr.distributed.obj import DistributedDcrGraph
from pm4py.objects.log.obj import EventLog


def apply(log, graph, parameters) -> DistributedDcrGraph:
    """
    this method calls the role miner

    Parameters
    ----------
    log: EventLog | pandas.Dataframe
        Event log to use in the role miner
    graph: DCRGraph
        Dcr graph to apply additional attributes to
    parameters
        Parameters of the algorithm, including:
            activity_key: activity identifier, used for assigning the events to
            resource_key: resource identifier, used to determine the principals and role assignmed if specified
            group_key: group identifier, used to determine the access right, i.e. the Role assignments for event in log

    Returns
    -------
    :class:´RoleDCR_Graph`
        return a DCR graph, that contains organizational attributes
    """
    role_mine = RoleMining()
    return role_mine.mine(log, graph, parameters)


class RoleMining:
    """
    The RoleMining provides a simple algorithm to mine for organizational data of an event log for DCR graphs

    After initialization, user can call mine(log, G, parameters), which will return a DCR Graph with distributed.

    Attributes
    ----------
    graph: Dict[str,Any]
        A template that will be used collecting organizational data

    Methods
    -------
    mine(log, G, parameters)
        calls the main mining function, extract distributed and principals from the log and perform rol

    Notes
    ------
    * NaN values are disregarded, if event in log has event with both, it will not store NaN as a role assignment
    * Currently no useful implementation for analysis of principalsAssignments, but is included for future improvement
    """
    def __init__(self):
        self.role_template = {"roles": set(), "principals": set(), "roleAssignments": {}, "principalsAssignments": {}}

    def __role_assignment_role_to_activity(self, log: pd.DataFrame, activity_key: str,
                                           group_key: str, resource_key: str) -> None:
        """
        If log has defined distributed, mine for role assignment using a role identifier,
        such as a Group key or possible optional parameter.

        Parameters
        ----------
        log
            event log
        activity_key
            attribute to be used as activity identifier
        group_key
            attribute to be used as role identifier
        resource_key
            attribute to be used as resource identifier
        """
        # turn this into a dict that can iterated over
        act_roles_couple = dict(log.groupby([group_key, activity_key]).size())
        for couple in act_roles_couple:
            self.role_template['roleAssignments'][couple[0]] = self.role_template['roleAssignments'][couple[0]].union({couple[1]})
        act_roles_couple = dict(log.groupby([group_key, resource_key]).size())
        for couple in act_roles_couple:
            self.role_template['principalsAssignments'][couple[0]] = self.role_template['principalsAssignments'][couple[0]].union({couple[1]})


    def mine(self, log: Union[pd.DataFrame, EventLog], graph: DcrGraph, parameters: Optional[Dict[str, Any]]):
        """
        Main role mine algorithm, will mine for principals and distributed in a DCR graphs, and associated role assignment.
        determine principals, distributed and roleAssignment through unique occurrences in log.

        Parameters
        ----------
        log: pandas.DataFrame | EventLog
            Event log used for mining
        graph: DCRGraph
            DCR graph to append additional attributes
        parameters: Optional[Dict[str, Any]]
            optional parameters used for role mining
        Returns
        -------
        RoleDCR_Graph(G, dcr)
            returns a DCR graph with organizational attributes, store in a variant of DCR
            :class:`pm4py.objects.dcr.distributed.obj.RoleDCR_Graph`
        """

        activity_key = exec_utils.get_param_value(constants.PARAMETER_CONSTANT_ACTIVITY_KEY, parameters,
                                                  xes_constants.DEFAULT_NAME_KEY)
        resource_key = exec_utils.get_param_value(constants.PARAMETER_CONSTANT_RESOURCE_KEY, parameters,
                                                  xes_constants.DEFAULT_RESOURCE_KEY)
        group_key = exec_utils.get_param_value(constants.PARAMETER_CONSTANT_GROUP_KEY, parameters,
                                               xes_constants.DEFAULT_GROUP_KEY)

        # perform mining on event logs
        if not isinstance(log, pd.DataFrame):
            log = pm4py.convert_to_dataframe(log)

        keys = set(log.keys())
        if (resource_key not in keys) and (group_key not in keys):
            raise ValueError('input log does not contain attribute identifiers for resources or roles')

        # load resources if provided
        principals = set(log[resource_key].values)
        principals = set(filter(lambda x: x == x, principals))
        self.role_template['principals'] = principals

        # if no resources are provided, map distributed to activities
        roles = set(log[group_key].values)
        roles = set(filter(lambda x: x == x, roles))
        self.role_template['roles'] = roles
        for i in self.role_template['roles']:
            self.role_template['roleAssignments'][i] = set()
            self.role_template['principalsAssignments'][i] = set()

        self.__role_assignment_role_to_activity(log, activity_key, group_key, resource_key)
        return DistributedDcrGraph({**graph.obj_to_template(), **self.role_template})
