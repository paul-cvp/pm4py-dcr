import os

import pm4py
from pm4py.algo.transformation.log_to_features.util import locally_linear_embedding
from examples import examples_conf
import importlib.util


def execute_script():
    log = pm4py.read_xes(os.path.join("..", "tests", "input_data", "receipt.xes"))

    if importlib.util.find_spec("scipy") and importlib.util.find_spec("sklearn"):
        # calculates the graph:
        # values of y more distant from 0 signal executions that differ from the mainstream behavior
        x, y = locally_linear_embedding.apply(log)

        if importlib.util.find_spec("matplotlib") and importlib.util.find_spec("graphviz"):
            from pm4py.visualization.graphs import visualizer
            gviz = visualizer.apply(x, y, variant=visualizer.Variants.DATES,
                                    parameters={"title": "Locally Linear Embedding", "format": examples_conf.TARGET_IMG_FORMAT, "y_axis": "Intensity"})
            visualizer.view(gviz)


if __name__ == "__main__":
    execute_script()
