"""
This module extends the MilestoneNoResponseDcrGraph class to include support for
nested groups and subprocesses within Dynamic Condition Response (DCR) Graphs.

The module adds functionality to handle hierarchical structures in DCR Graphs,
allowing for more complex process models with nested elements and subprocesses.

Classes:
    NestingSubprocessDcrGraph: Extends MilestoneNoResponseDcrGraph to include nested groups and subprocesses.

This class provides methods to manage and manipulate nested groups and subprocesses
within a DCR Graph, enhancing the model's ability to represent complex organizational
structures and process hierarchies.

References
----------
.. [1] Hildebrandt, T., Mukkamala, R.R., Slaats, T. (2012). Nested Dynamic Condition Response Graphs. In: Arbab, F., Sirjani, M. (eds) Fundamentals of Software Engineering. FSEN 2011. Lecture Notes in Computer Science, vol 7141. Springer, Berlin, Heidelberg. `DOI <https://doi.org/10.1007/978-3-642-29320-7_23>`_.

.. [2] Normann, H., Debois, S., Slaats, T., Hildebrandt, T.T. (2021). Zoom and Enhance: Action Refinement via Subprocesses in Timed Declarative Processes. In: Polyvyanyy, A., Wynn, M.T., Van Looy, A., Reichert, M. (eds) Business Process Management. BPM 2021. Lecture Notes in Computer Science(), vol 12875. Springer, Cham. `DOI <https://doi.org/10.1007/978-3-030-85469-0_12>`_.
"""
from pm4py.objects.dcr.extended.obj import ExtendedDcrGraph
from typing import Set, Dict


class HierarchicalDcrGraph(ExtendedDcrGraph):
    """
    This class extends the MilestoneNoResponseDcrGraph to include nested groups
    and subprocesses, allowing for more complex hierarchical structures in DCR Graphs.

    Attributes
    ----------
    self.__nestedgroups: Dict[str, Set[str]]
        A dictionary mapping group names to sets of event IDs within each group.
    self.__subprocesses: Dict[str, Set[str]]
        A dictionary mapping subprocess names to sets of event IDs within each subprocess.
    self.__nestedgroups_map: Dict[str, str]
        A dictionary mapping event IDs to their corresponding group names.

    Methods
    -------
    obj_to_template(self) -> dict:
        Converts the object to a template dictionary, including nested groups and subprocesses.

    """
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
