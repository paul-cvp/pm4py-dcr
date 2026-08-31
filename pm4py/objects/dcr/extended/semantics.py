from typing import Set

from pm4py.objects.dcr.semantics import DcrSemantics


class ExtendedSemantics(DcrSemantics):

    @classmethod
    def enabled(cls, graph) -> Set[str]:
        res = super().enabled(graph)
        for e in set(graph.milestones.keys()).intersection(res):
            if len(graph.milestones[e].intersection(
                    graph.marking.included.intersection(graph.marking.pending))) > 0:
                res.discard(e)
        return res

    @classmethod
    def weak_execute(cls, event, graph):
        if event in graph.noresponses:
            for e_prime in graph.noresponses[event]:
                graph.marking.pending.discard(e_prime)

        return super().weak_execute(event, graph)


