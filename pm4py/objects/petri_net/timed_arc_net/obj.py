from pm4py.objects.petri_net.obj import InhibitorNet, Marking, PetriNet
from pm4py.objects.petri_net.properties import AGE_INVARIANT


class TimedMarking(Marking):

    def __init__(self, marking=None):
        Marking.__init__(self, marking)
        self.timed_dict = {}  # place and age of token (the net is 1-safe or 1-bounded)

    def time_step(self, tics):
        for k in self.keys():
            if k not in self.timed_dict:
                self.timed_dict[k] = tics
            else:
                self.timed_dict[k] += tics

    def __repr__(self):
        return str([str(p.name) + ":" + str(self.get(p)) for p in sorted(list(self.keys()), key=lambda x: x.name)]) + " " + str(self.timed_dict)


class TimedArcNet(InhibitorNet):

    def __init__(self, name=None, places=None, transitions=None, arcs=None, properties=None):
        super().__init__(name, places, transitions, arcs, properties)

    class TransportArc(PetriNet.Arc):
        def __init__(self, source, target, weight=1, properties=None):
            PetriNet.Arc.__init__(self, source, target, weight=weight, properties=properties)

    class InvariantPlace(PetriNet.Place):

        def __init__(self, name, in_arcs=None, out_arcs=None, properties=None):
            super().__init__(name, in_arcs, out_arcs, properties)

        def __set_age_invariant(self, age):
            self.properties[AGE_INVARIANT] = age

        def __get_age_invariant(self):
            return self.properties[AGE_INVARIANT]

        age_invariant = property(__get_age_invariant, __set_age_invariant)

