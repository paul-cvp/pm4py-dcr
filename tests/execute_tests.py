import inspect
import os
import sys
import unittest
import importlib.util

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

EXECUTE_TESTS = True

import pm4py
import numpy
import pandas
import networkx

pm4py.util.constants.SHOW_PROGRESS_BAR = False
pm4py.util.constants.SHOW_EVENT_LOG_DEPRECATION = False
pm4py.util.constants.SHOW_INTERNAL_WARNINGS = False
# pm4py.util.constants.DEFAULT_TIMESTAMP_PARSE_FORMAT = None

enabled_tests = ["SimplifiedInterfaceTest", "SimplifiedInterface2Test", "DocTests", "RoleDetectionTest",
                 "PassedTimeTest", "Pm4pyImportPackageTest", "XesImportExportTest", "CsvImportExportTest",
                 "OtherPartsTests", "AlphaMinerTest", "InductiveMinerTest", "InductiveMinerTreeTest",
                 "AlignmentTest", "DfgTests", "SnaTests", "PetriImportExportTest", "BPMNTests", "ETCTest",
                 "DiagnDfConfChecking", "ProcessModelEvaluationTests", "DecisionTreeTest", "GraphsForming",
                 "HeuMinerTest", "MainFactoriesTest", "AlgorithmTest", "LogFilteringTest",
                 "DataframePrefilteringTest", "StatisticsLogTest", "StatisticsDfTest", "TransitionSystemTest",
                 "ImpExpFromString", "WoflanTest", "OcelFilteringTest", "OcelDiscoveryTest", "LlmTest", "DcrImportExportTest",
                 "DcrSemanticsTest", "DcrDiscoveryTest", "DcrConformanceTest", "DcrAlignmentTest"]

loader = unittest.TestLoader()
suite = unittest.TestSuite()

failed = 0

if not importlib.util.find_spec("graphviz"):
    print("important! install 'grapviz' from pip")
    failed +=1

if not importlib.util.find_spec("lxml"):
    print("important! install 'lxml' from pip")
    failed += 1

if "SimplifiedInterfaceTest" in enabled_tests:
    try:
        from tests.simplified_interface import SimplifiedInterfaceTest
        suite.addTests(loader.loadTestsFromTestCase(SimplifiedInterfaceTest))
    except:
        print("SimplifiedInterfaceTest import failed!")
        failed += 1

if "SimplifiedInterface2Test" in enabled_tests:
    try:
        from tests.simplified_interface_2 import SimplifiedInterface2Test
        suite.addTests(loader.loadTestsFromTestCase(SimplifiedInterface2Test))
    except:
        print("SimplifiedInterface2Test import failed!")
        failed += 1

if "DocTests" in enabled_tests:
    try:
        from tests.doc_tests import DocTests
        suite.addTests(loader.loadTestsFromTestCase(DocTests))
    except:
        print("DocTests import failed!")
        failed += 1

if "RoleDetectionTest" in enabled_tests:
    try:
        from tests.role_detection import RoleDetectionTest
        suite.addTests(loader.loadTestsFromTestCase(RoleDetectionTest))
    except:
        print("RoleDetectionTest import failed!")
        failed += 1

if "PassedTimeTest" in enabled_tests:
    try:
        from tests.passed_time import PassedTimeTest
        suite.addTests(loader.loadTestsFromTestCase(PassedTimeTest))
    except:
        print("PassedTimeTest import failed!")
        failed += 1

if "Pm4pyImportPackageTest" in enabled_tests:
    try:
        from tests.imp_everything import Pm4pyImportPackageTest
        suite.addTests(loader.loadTestsFromTestCase(Pm4pyImportPackageTest))
    except:
        print("Pm4pyImportPackageTest import failed!")
        failed += 1

if "XesImportExportTest" in enabled_tests:
    try:
        from tests.xes_impexp_test import XesImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(XesImportExportTest))
    except:
        print("XesImportExportTest import failed!")
        failed += 1

if "CsvImportExportTest" in enabled_tests:
    try:
        from tests.csv_impexp_test import CsvImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(CsvImportExportTest))
    except:
        print("CsvImportExportTest import failed!")
        failed += 1

if "OtherPartsTests" in enabled_tests:
    try:
        from tests.other_tests import OtherPartsTests
        suite.addTests(loader.loadTestsFromTestCase(OtherPartsTests))
    except:
        print("OtherPartsTests import failed!")
        failed += 1

if "AlphaMinerTest" in enabled_tests:
    try:
        from tests.alpha_test import AlphaMinerTest
        suite.addTests(loader.loadTestsFromTestCase(AlphaMinerTest))
    except:
        print("AlphaMinerTest import failed!")
        failed += 1

if "InductiveMinerTest" in enabled_tests:
    try:
        from tests.inductive_test import InductiveMinerTest
        suite.addTests(loader.loadTestsFromTestCase(InductiveMinerTest))
    except:
        print("InductiveMinerTest import failed!")
        failed += 1

if "InductiveMinerTreeTest" in enabled_tests:
    try:
        from tests.inductive_tree_test import InductiveMinerTreeTest
        suite.addTests(loader.loadTestsFromTestCase(InductiveMinerTreeTest))
    except:
        print("InductiveMinerTreeTest import failed!")
        failed += 1

if "AlignmentTest" in enabled_tests:
    try:
        from tests.alignment_test import AlignmentTest
        suite.addTests(loader.loadTestsFromTestCase(AlignmentTest))
    except:
        print("AlignmentTest import failed!")
        failed += 1

if "DfgTests" in enabled_tests:
    try:
        from tests.dfg_tests import DfgTests
        suite.addTests(loader.loadTestsFromTestCase(DfgTests))
    except:
        print("DfgTests import failed!")
        failed += 1

if "SnaTests" in enabled_tests:
    try:
        from tests.sna_test import SnaTests
        suite.addTests(loader.loadTestsFromTestCase(SnaTests))
    except:
        print("SnaTests import failed!")
        failed += 1

if "PetriImportExportTest" in enabled_tests:
    try:
        from tests.petri_imp_exp_test import PetriImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(PetriImportExportTest))
    except:
        print("PetriImportExportTest import failed!")
        failed += 1

if "BPMNTests" in enabled_tests:
    try:
        from tests.bpmn_tests import BPMNTests
        suite.addTests(loader.loadTestsFromTestCase(BPMNTests))
    except:
        print("BPMNTests import failed!")
        failed += 1

if "ETCTest" in enabled_tests:
    try:
        from tests.etc_tests import ETCTest
        suite.addTests(loader.loadTestsFromTestCase(ETCTest))
    except:
        print("ETCTest import failed!")
        failed += 1

if "DiagnDfConfChecking" in enabled_tests:
    try:
        from tests.diagn_df_conf_checking import DiagnDfConfChecking
        suite.addTests(loader.loadTestsFromTestCase(DiagnDfConfChecking))
    except:
        print("DiagnDfConfChecking import failed!")
        failed += 1

if "ProcessModelEvaluationTests" in enabled_tests:
    try:
        from tests.evaluation_tests import ProcessModelEvaluationTests
        suite.addTests(loader.loadTestsFromTestCase(ProcessModelEvaluationTests))
    except:
        print("ProcessModelEvaluationTests import failed!")
        failed += 1

if "DecisionTreeTest" in enabled_tests:
    try:
        from tests.dec_tree_test import DecisionTreeTest
        suite.addTests(loader.loadTestsFromTestCase(DecisionTreeTest))
    except:
        print("DecisionTreeTest import failed!")
        failed += 1

if "GraphsForming" in enabled_tests:
    try:
        from tests.graphs_forming import GraphsForming
        suite.addTests(loader.loadTestsFromTestCase(GraphsForming))
    except:
        print("GraphsForming import failed!")
        failed += 1

if "HeuMinerTest" in enabled_tests:
    try:
        from tests.heuminer_test import HeuMinerTest
        suite.addTests(loader.loadTestsFromTestCase(HeuMinerTest))
    except:
        print("HeuMinerTest import failed!")
        failed += 1

if "MainFactoriesTest" in enabled_tests:
    try:
        from tests.main_fac_test import MainFactoriesTest
        suite.addTests(loader.loadTestsFromTestCase(MainFactoriesTest))
    except:
        print("MainFactoriesTest import failed!")
        failed += 1

if "AlgorithmTest" in enabled_tests:
    try:
        from tests.algorithm_test import AlgorithmTest
        suite.addTests(loader.loadTestsFromTestCase(AlgorithmTest))
    except:
        print("AlgorithmTest import failed!")
        failed += 1

if "LogFilteringTest" in enabled_tests:
    try:
        from tests.filtering_log_test import LogFilteringTest
        suite.addTests(loader.loadTestsFromTestCase(LogFilteringTest))
    except:
        print("LogFilteringTest import failed!")
        failed += 1

if "DataframePrefilteringTest" in enabled_tests:
    try:
        from tests.filtering_pandas_test import DataframePrefilteringTest
        suite.addTests(loader.loadTestsFromTestCase(DataframePrefilteringTest))
    except:
        print("DataframePrefilteringTest import failed!")
        failed += 1

if "StatisticsLogTest" in enabled_tests:
    try:
        from tests.statistics_log_test import StatisticsLogTest
        suite.addTests(loader.loadTestsFromTestCase(StatisticsLogTest))
    except:
        print("StatisticsLogTest import failed!")
        failed += 1

if "StatisticsDfTest" in enabled_tests:
    try:
        from tests.statistics_df_test import StatisticsDfTest
        suite.addTests(loader.loadTestsFromTestCase(StatisticsDfTest))
    except:
        print("StatisticsDfTest import failed!")
        failed += 1

if "TransitionSystemTest" in enabled_tests:
    try:
        from tests.trans_syst_tests import TransitionSystemTest
        suite.addTests(loader.loadTestsFromTestCase(TransitionSystemTest))
    except:
        print("TransitionSystemTest import failed!")
        failed += 1

if "ImpExpFromString" in enabled_tests:
    try:
        from tests.imp_exp_from_string import ImpExpFromString
        suite.addTests(loader.loadTestsFromTestCase(ImpExpFromString))
    except:
        print("ImpExpFromString import failed!")
        failed += 1

if "WoflanTest" in enabled_tests:
    try:
        from tests.woflan_tests import WoflanTest
        suite.addTests(loader.loadTestsFromTestCase(WoflanTest))
    except:
        print("WoflanTest import failed!")
        failed += 1

if "OcelFilteringTest" in enabled_tests:
    try:
        from tests.ocel_filtering_test import OcelFilteringTest
        suite.addTests(loader.loadTestsFromTestCase(OcelFilteringTest))
    except:
        print("OcelFilteringTest import failed!")
        failed += 1

if "OcelDiscoveryTest" in enabled_tests:
    try:
        from tests.ocel_discovery_test import OcelDiscoveryTest
        suite.addTests(loader.loadTestsFromTestCase(OcelDiscoveryTest))
    except:
        print("OcelDiscoveryTest import failed!")
        failed += 1

if "LlmTest" in enabled_tests:
    try:
        from tests.llm_test import LlmTest
        suite.addTests(loader.loadTestsFromTestCase(LlmTest))
    except:
        print("LlmTest import failed!")
        failed += 1


if failed > 0:
    print("-- PRESS ENTER TO CONTINUE --")
    input()
    try:
        from tests.ocel_discovery_test import OcelDiscoveryTest
        suite.addTests(loader.loadTestsFromTestCase(OcelDiscoveryTest))
    except:
        print("OcelDiscoveryTest import failed!")
        failed += 1

if "LlmTest" in enabled_tests:
    try:
        from tests.llm_test import LlmTest
        suite.addTests(loader.loadTestsFromTestCase(LlmTest))
    except:
        print("LlmTest import failed!")
        failed += 1

if "DcrImportExportTest" in enabled_tests:
    from tests.dcr_test import TestImportExportDCR

    suite.addTests(loader.loadTestsFromTestCase(TestImportExportDCR))

if "DcrSemanticsTest" in enabled_tests:
    from tests.dcr_test import TestObjSematics

    suite.addTests(loader.loadTestsFromTestCase(TestObjSematics))

if "DcrDiscoveryTest" in enabled_tests:
    from tests.dcr_test import TestDiscoveryDCR

    suite.addTests(loader.loadTestsFromTestCase(TestDiscoveryDCR))

if "DcrConformanceTest" in enabled_tests:
    from tests.dcr_test import TestConformanceDCR

    suite.addTests(loader.loadTestsFromTestCase(TestConformanceDCR))

if "DcrAlignmentTest" in enabled_tests:
    from tests.dcr_test import TestAlignment
    suite.addTests(loader.loadTestsFromTestCase(TestAlignment))


if failed > 0:
    print("-- PRESS ENTER TO CONTINUE --")
    input()

def main():
    if EXECUTE_TESTS:
        runner = unittest.TextTestRunner()
        runner.run(suite)

    print("numpy version: "+str(numpy.__version__))
    print("pandas version: "+str(pandas.__version__))
    print("networkx version: "+str(networkx.__version__))

    if importlib.util.find_spec("scipy"):
        import scipy
        print("scipy version: "+str(scipy.__version__))

    if importlib.util.find_spec("lxml"):
        import lxml
        print("lxml version: "+str(lxml.__version__))

    if importlib.util.find_spec("matplotlib"):
        import matplotlib
        print("matplotlib version: "+str(matplotlib.__version__))

    if importlib.util.find_spec("sklearn"):
        import sklearn
        print("sklearn version: "+str(sklearn.__version__))

    print("pm4py version: "+str(pm4py.__version__))
    print("Python version: "+str(sys.version))


if __name__ == "__main__":
    import warnings
    from pandas.errors import SettingWithCopyWarning, PerformanceWarning
    import pandas as pd
    pd.set_option('future.no_silent_downcasting', True)
    warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
    warnings.simplefilter(action="ignore", category=PerformanceWarning)
    warnings.filterwarnings(
        action='ignore', category=UserWarning, message=r"Boolean Series.*"
    )
    main()
