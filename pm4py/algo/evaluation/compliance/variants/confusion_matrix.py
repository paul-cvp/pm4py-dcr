import math
from pm4py.objects.dcr.semantics import DCRSemantics
from copy import deepcopy
from typing import Tuple

class complianceResult:
    '''
    class to store the collection of result from compliance

    contains function to compute the value for the confusion matrix
    '''
    def __init__(self):
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0

    def addTraceResult(self,expectedResult,actualResult):
        '''
        this function notes, if a trace is true positive/negative or false positive/negative
        based on ground truth log expected result and the actually result

        Parameters
        ----------
        :param expectedResult: expected result of trace
        :param actualResult: actual result of trace

        Returns
        -------
        '''
        if actualResult == True:
            if expectedResult == True:
                self.tp += 1
            else:
                self.fp += 1
        else:
            if expectedResult == True:
                self.fn += 1
            else:
                self.tn += 1

    def compute_accuracy(self) -> float:
        #returns how accurate the model is according to expected behavior:
        #acc. = (TP+TN)/(TP+TN+FP+FN)
        return (self.tp + self.tn)/(self.tn + self.tp + self.fn + self.fp)

    def compute_positive_precision(self) -> float:
        # prec. = (TP)/(TP+FP)
        #returns value of how precise the model reflect the expected behavior
        return (self.tp)/(self.tp + self.fp)

    def compute_negative_precision(self) -> float:
        # prec. = (TN)/(TN+FN)
        # returns value of how precise the model reflect the expected behavior
        return (self.tn)/(self.tn + self.fn)


    def compute_positive_recall(self) -> float:
        #recall = (TP)/(TP+FN)
        #return value of how well the model has captured expected behavior
        return (self.tp)/(self.fn + self.tp)

    def compute_negative_recall(self) -> float:
        #recall = (TP)/(TP+FN)
        #return value of how well the model has captured expected behavior
        return (self.tn)/(self.fp + self.tn)


    def get_positive_f_score(self) -> float:
        f_score = (((2) * self.compute_positive_precision() * self.compute_positive_recall()) /
                   (self.compute_positive_precision() + self.compute_positive_recall()))
        return f_score

    def get_negative_f_score(self) -> float:
        f_score = (((2) * self.compute_negative_precision() * self.compute_negative_recall()) /
         (self.compute_negative_precision() + self.compute_negative_recall()))
        return f_score
    def mcc(self) -> float:
        numerator = (self.tn * self.tp) - (self.fn * self.fp)
        Denominator = (self.tp + self.fp) * (self.tp + self.fn) * (
                self.tn + self.fp) * (self.tn + self.fn)
        return numerator / math.sqrt(Denominator)

    def get_classification_values(self) -> Tuple[int, int, int, int]:
        return self.tp,self.fp,self.tn,self.fn


class ComplianceChecker:
    """
    The compliance checker, will take in, a dcr graph and a ground truth log

    this implementation is based on the compliance checker for DisCoveR java implementation used to analyze:
    - accuracy
    - precision
    - recall/fitness

    runs traces extracted from a ground truth log
    use function from dcrsemantics run, returns none if the trace is deviating
    if trace is deviating from model return false

    if trace can be executed return dcr graph and marking, check if the graph is accepting
    """
    def __init__(self):
        self.compliance_res = complianceResult()

    def apply(self, graph, gt_log):
        return self.compliant_traces(graph, gt_log)

    def compliant_traces(self, graph, test_log, ground_truth_log):
        #Eventlog and pandas dataframe requires two different approaches
        sem = DCRSemantics()
        initial_marking = deepcopy(graph.marking)
        for trace, gt_trace in zip(test_log,ground_truth_log):
            actual_value = True
            for e, gt_e in zip(trace,gt_trace):
                if not sem.is_enabled(e['concept:name'], graph):
                    actual_value = False
                    break
                else:
                    graph = sem.execute(graph, e['concept:name'])
            if not sem.is_accepting(graph):
                self.compliance_res.addTraceResult(gt_trace.attributes['pdc:isPos'], False)
            else:
                self.compliance_res.addTraceResult(gt_trace.attributes['pdc:isPos'], actual_value)
            graph.marking.reset(deepcopy(initial_marking))
        return self.compliance_res

    def compliance_trace(self, graph, gt_trace):
        for e in gt_trace:
            pass





                
