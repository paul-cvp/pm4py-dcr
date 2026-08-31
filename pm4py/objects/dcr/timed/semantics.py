from datetime import timedelta
from typing import Set

from pm4py.objects.dcr.extended.semantics import ExtendedSemantics


class TimedSemantics(ExtendedSemantics):

    def __init__(self, graph):
        self.__can_execute_time = self.create_can_execute_time_dict(graph)

    @classmethod
    def execute(cls, graph, event_or_tics):
        if isinstance(event_or_tics, timedelta):
            return cls.time_step(graph, event_or_tics)
        elif isinstance(event_or_tics, int):
            return cls.time_step(graph, timedelta(event_or_tics))
        elif event_or_tics in graph.events:
            return super().execute(graph, event_or_tics)
        else:
            raise ValueError('event_or_tics must be either timedelta, int or event')

    @classmethod
    def enabled(cls, graph) -> Set[str]:
        res = super().enabled(graph)
        for e in res:
            if e in graph.timedconditions:
                for (e_prime, k) in graph.timedconditions[e].items():
                    if (e_prime in graph.marking.included.intersection(graph.marking.executed) and
                            graph.marking.executed_time[e_prime] < k):
                        res.discard(e)
        return res

    @classmethod
    def weak_execute(cls, event, graph):
        graph.marking.executed_time[event] = 0

        if event in graph.timedresponses:
            for (e_prime, k) in graph.timedresponses[event].items():
                graph.marking.pending_deadline[e_prime] = k

        return super().weak_execute(event, graph)

    @classmethod
    def time_step(cls, graph, tics):
        deadline = cls.next_deadline(graph)
        # we can only time step if no included pending event deadline is exceeded
        if tics <= deadline:
            for e in graph.marking.pending_deadline:
                # for each existing deadline we update the deadline time until the event must be made not pending by removing tics
                # Note the events here do not need to be included
                # For an excluded pending event the deadline becomes 0 if the deadline is passed while its excluded. So it must be executed immediately after it has been included.
                graph.marking.pending_deadline[e] = max(graph.marking.pending_deadline[e] - tics, timedelta(0))
            for e in graph.marking.executed:
                # for each executed event we care about adding tics until we reach the
                # maximum of all its delays so that it can fire (we stop counting the executed time afterwards)
                graph.marking.executed_time[e] = min(graph.marking.executed_time[e] + tics, cls.__can_execute_time[e])
        return graph

    @staticmethod
    def next_deadline(graph):
        next_deadline = None
        for e in graph.marking.pending_deadline:
            if e in graph.marking.included:
                if (next_deadline is None) or (graph.marking.pending_deadline[e] < next_deadline):
                    next_deadline = graph.marking.pending_deadline[e]
        return next_deadline

    @staticmethod
    def next_delay(graph):
        next_delay = None
        for e in graph.timedconditions:
            for (e_prime, k) in graph.timedconditions[e].items():
                if e_prime in graph.marking.included and e_prime in graph.marking.executed:
                    delay = k - graph.marking.executed_time[e_prime]
                    if delay > timedelta(0) and (next_delay is None or delay < next_delay):
                        next_delay = delay
        return next_delay

    @staticmethod
    def create_can_execute_time_dict(graph):
        d = {}
        for e in graph.events:
            d[e] = timedelta(0)
        for e in graph.timedconditions:
            for (e_prime, k) in graph.timedconditions[e].items():
                if k > d[e_prime]:
                    d[e_prime] = k
        return d
