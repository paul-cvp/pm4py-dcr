'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
import copy
from pm4py.objects.petri_net import properties
from pm4py.objects.petri_net.sem_interface import Semantics
from pm4py.objects.petri_net.timed_arc_net.obj import TimedArcNet, TimedMarking
from pm4py.objects.petri_net.properties import AGE_INVARIANT, AGE_MIN, AGE_MAX, TRANSPORT_INDEX


class TimedArcSemantics(Semantics):
    def is_enabled(self, t, pn, m, **kwargs):
        """
        Verifies whether a given transition is enabled in a given Petri net and marking

        Parameters
        ----------
        :param t: transition to check
        :param pn: Petri net
        :param m: marking to check

        Returns
        -------
        :return: true if enabled, false otherwise
        """
        return is_enabled(t, pn, m)

    def execute(self, t, pn, m, **kwargs):
        """
        Executes a given transition in a given Petri net and Marking

        Parameters
        ----------
        :param t: transition to execute
        :param pn: Petri net
        :param m: marking to use

        Returns
        -------
        :return: newly reached marking if :param t: is enabled, None otherwise
        """
        return execute(t, pn, m)

    def weak_execute(self, t, pn, m, **kwargs):
        """
        Execute a transition even if it is not fully enabled

        Parameters
        ----------
        :param t: transition to execute
        :param pn: Petri net
        :param m: marking to use

        Returns
        -------
        :return: newly reached marking if :param t: is enabled, None otherwise
        """
        return weak_execute(t, m)

    def enabled_transitions(self, pn, m, **kwargs):
        """
        Returns a set of enabled transitions in a Petri net and given marking

        Parameters
        ----------
        :param pn: Petri net
        :param m: marking of the pn

        Returns
        -------
        :return: set of enabled transitions
        """
        return enabled_transitions(pn, m)


# 29/08/2021: the following methods have been encapsulated in the InhibitorResetSemantics class.
# the long term idea is to remove them. However, first we need to adapt the existing code to the new
# structure. Moreover, for performance reason, it is better to leave the code here, without having
# to instantiate a TimedArcSemantics object.
def is_enabled(t, pn, m):
    if t not in pn.transitions:
        return False
    else:
        source_transport = {}
        for a in t.in_arcs:
            if isinstance(a, TimedArcNet.InhibitorArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.INHIBITOR_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "tapnInhibitor" or
                                                                                                a.properties[properties.ARCTYPE] == "inhibitor")):
                if m[a.source] > 0:
                    return False
            elif isinstance(a, TimedArcNet.TransportArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "transport")):  # the age of the token in the source place of the transport arc must satisfy the guards


                min = 0
                max = float("inf")
                source_transport[a.properties[TRANSPORT_INDEX]] = a.source  # all transport in_arcs have a unique index to link them to transport out_arcs
                if AGE_MIN in a.properties:
                    min = a.properties[AGE_MIN]
                if AGE_MAX in a.properties:
                    max = a.properties[AGE_MAX]
                if min > m.timed_dict[a.source] or m.timed_dict[a.source] > max:
                    return False
            elif m[a.source] < a.weight:
                return False

        for a in t.out_arcs:
            if isinstance(a, TimedArcNet.TransportArc) and isinstance(a.target, TimedArcNet.InvariantPlace):
                if a.target[AGE_INVARIANT] >= m.timed_dict[source_transport[a.properties[TRANSPORT_INDEX]]]:
                    return False

    return True


def next_delay(pn):
    transport_arcs = [arc for arc in pn.arcs
                      if properties.ARCTYPE in arc.properties and arc.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC
                      and isinstance(arc.source, TimedArcNet.Place)]
    first_delay = float("inf")
    first_enabled_transition = None
    for arc in transport_arcs:
        min_age = arc.properties[properties.AGE_MIN] if properties.AGE_MIN in arc.properties else 0
        if min_age < first_delay:
            first_delay = min_age
            first_enabled_transition = arc.target
    return first_delay, first_enabled_transition


def next_deadline(pn):
    invariant_places = [p for p in pn.places if properties.AGE_INVARIANT in p.properties]
    first_deadline = float("inf")
    for place in invariant_places:
        age_invariant = place.properties[properties.AGE_INVARIANT]
        if age_invariant < first_deadline:
            first_deadline = age_invariant
    return first_deadline


def time_step(tics, pn, m):
    for p in pn.places:
        if AGE_INVARIANT in p.properties and p in m.timed_dict and p.properties[AGE_INVARIANT] < m.timed_dict[p] + tics:
            return False
    m.time_step(tics)
    return True


def execute(t, pn, m):
    if not is_enabled(t, pn, m):
        return None

    m_out = copy.copy(m)
    if isinstance(pn, TimedArcNet):
        m_out.timed_dict = copy.copy(m.timed_dict)
    transfer_time_dict = {}
    for a in t.in_arcs:
        if isinstance(a, TimedArcNet.InhibitorArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.INHIBITOR_ARC or
                                                                                                    a.properties[properties.ARCTYPE] == "tapnInhibitor" or
                                                                                                    a.properties[properties.ARCTYPE] == "inhibitor")):
            pass
        else:
            m_out[a.source] -= a.weight
            if m_out[a.source] == 0:
                del m_out[a.source]
            if isinstance(a, TimedArcNet.TransportArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "transport")):
                transfer_time_dict[a.properties[TRANSPORT_INDEX]] = m_out.timed_dict[a.source]
                if m_out[a.source] == 0:
                    del m_out.timed_dict[a.source]

    for a in t.out_arcs:
        m_out[a.target] += a.weight
        if isinstance(a, TimedArcNet.TransportArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "transport")):
            m_out.timed_dict[a.target] = transfer_time_dict[a.properties[TRANSPORT_INDEX]]

    return m_out


def weak_execute(t, m):
    m_out = copy.copy(m)
    m_out.timed_dict = copy.copy(m.timed_dict)
    transfer_time_dict = {}
    for a in t.in_arcs:
        if isinstance(a, TimedArcNet.InhibitorArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.INHIBITOR_ARC or
                                                                                                    a.properties[properties.ARCTYPE] == "tapnInhibitor" or
                                                                                                    a.properties[properties.ARCTYPE] == "inhibitor")):
            pass
        else:
            m_out[a.source] -= a.weight
            if m_out[a.source] <= 0:
                del m_out[a.source]
            if isinstance(a, TimedArcNet.TransportArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "transport")):
                transfer_time_dict[a.properties[TRANSPORT_INDEX]] = m_out.timed_dict[a.source]
                if m_out[a.source] <= 0:
                    del m_out.timed_dict[a.source]
    for a in t.out_arcs:
        m_out[a.target] += a.weight
        if isinstance(a, TimedArcNet.TransportArc) or (properties.ARCTYPE in a.properties and (a.properties[properties.ARCTYPE] == properties.TRANSPORT_ARC or
                                                                                                a.properties[properties.ARCTYPE] == "transport")):
            m_out.timed_dict[a.target] = transfer_time_dict[a.properties[TRANSPORT_INDEX]]
    return m_out


def enabled_transitions(pn, m):
    enabled = set()
    # print(next_delay(pn))
    # print(next_deadline(pn))
    for t in pn.transitions:
        if is_enabled(t, pn, m):
            enabled.add(t)
    return enabled
