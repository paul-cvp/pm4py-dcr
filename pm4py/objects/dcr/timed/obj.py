"""
This module extends the Dynamic Condition Response (DCR) Graph framework to
include timed constraints and behaviors. It builds upon the NestingSubprocessDcrGraph
class to incorporate time-based elements into the DCR Graph model.

The module introduces timing aspects to both the marking of events and the
relations between events, allowing for more sophisticated process models that
can represent time-dependent behaviors and constraints.

Classes:
    TimedMarking: Extends the basic Marking class to include timing information.
    TimedDcrGraph: Extends NestingSubprocessDcrGraph to incorporate timed conditions and responses.

This module enhances the DCR Graph model with the ability to represent and
manage time-based constraints, enabling more accurate modelling of real-world
processes where timing plays a crucial role.

References
----------
.. [1] Hildebrandt, T., Mukkamala, R.R., Slaats, T., Zanitti, F. (2013). Contracts for cross-organizational workflows as timed Dynamic Condition Response Graphs. The Journal of Logic and Algebraic Programming, 82(5-7), 164-185. `DOI <https://doi.org/10.1016/j.jlap.2013.05.005>`_.
"""
from datetime import timedelta

from pm4py.objects.dcr.obj import Marking
from pm4py.objects.dcr.hierarchical.obj import HierarchicalDcrGraph

from typing import Dict


class TimedMarking(Marking):
    """
    This class extends the basic Marking class to include timing information
    for executed events and pending deadlines.

    Attributes
    ----------
    self.__executed_time: Dict[str, datetime]
        A dictionary mapping events to their execution times.
    self.__pending_deadline: Dict[str, datetime]
        A dictionary mapping events to their pending deadlines.

    Methods
    -------
    No additional methods are explicitly defined in this class.
    """
    def __init__(self, executed, included, pending, executed_time=None, pending_deadline=None) -> None:
        super().__init__(executed, included, pending)
        self.__executed_time = {} if executed_time is None else executed_time
        self.__pending_deadline = {} if pending_deadline is None else pending_deadline

    @property
    def executed_time(self):
        return self.__executed_time

    @property
    def pending_deadline(self):
        return self.__pending_deadline


class TimedDcrGraph(HierarchicalDcrGraph):
    """
    This class extends the NestingSubprocessDcrGraph to incorporate timed
    conditions and responses, allowing for time-based constraints in DCR Graphs.

    Attributes
    ----------
    self.__marking: TimedMarking
        The marking of the DCR graph, including timing information.
    self.__timedconditions: Dict[str, Dict[str, timedelta]]
        A nested dictionary mapping events to their timed conditions.
    self.__timedresponses: Dict[str, Dict[str, timedelta]]
        A nested dictionary mapping events to their timed responses.

    Methods
    -------
    timed_dict_to_graph(self, timing_dict: Dict) -> None:
        Converts a timing dictionary to graph format, populating timed conditions and responses.
    obj_to_template(self) -> dict:
        Converts the object to a template dictionary, including timed conditions and responses.
    """
    def __init__(self, template=None, timing_dict=None):
        super().__init__(template)
        self.__marking = TimedMarking(set(), set(), set()) if template is None else (
            TimedMarking(template['marking']['executed'], template['marking']['included'], template['marking']['pending'],
                         template['marking']['executedTime'], template['marking']['pendingDeadline']))
        self.__timedconditions = {} if template is None else template['conditionsForDelays']
        self.__timedresponses = {} if template is None else template['responseToDeadlines']
        if timing_dict is not None:
            self.timed_dict_to_graph(timing_dict)

    def timed_dict_to_graph(self, timing_dict):
        for timing, value in timing_dict.items():
            if timing[0] == 'CONDITION':
                e1 = timing[2]
                e2 = timing[1]
                if e1 not in self.__timedconditions:
                    self.__timedconditions[e1] = {}
                self.__timedconditions[e1][e2] = value
            elif timing[0] == 'RESPONSE':
                e1 = timing[1]
                e2 = timing[2]
                if e1 not in self.__timedresponses:
                    self.__timedresponses[e1] = {}
                self.__timedresponses[e1][e2] = value

    def obj_to_template(self):
        res = super().obj_to_template()
        res['conditionsForDelays'] = self.__timedconditions
        res['responseToDeadlines'] = self.__timedresponses
        res['marking']['executedTime'] = self.__marking.executed_time
        res['marking']['pendingDeadline'] = self.__marking.pending_deadline
        return res

    @property
    def timedconditions(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timedconditions

    @timedconditions.setter
    def timedconditions(self, value: Dict[str, Dict[str, timedelta]]):
        self.__timedconditions = value

    @property
    def timedresponses(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timedresponses

    @timedresponses.setter
    def timedresponses(self, value: Dict[str, Dict[str, timedelta]]):
        self.__timedresponses = value
