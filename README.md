# A DCR Exentionsion for pm4py
Welcome to the pm4py extension for [pm4py](https://github.com/pm4py/pm4py-core/tree/release).
This exentionsion currently supports the discovery and conformance checking of DCR Graph, in addtition to import/export using xml for possible cross platform usage and visualization.
The github repo, is a forked repository of the pm4py-core and therefore holds the same functionality as the original library. This github repo has been created with the intension of developing an extension to library, such that it could be incorporated into the main pm4py-core.


## Documentation
The documentation can be autogenerated by using sphinx Visit [https://www.sphinx-doc.org/en/master/](https://www.sphinx-doc.org/en/master/)
For details of generating the sphinx document can be found in the docs/README.md

For the documentation of the implemented functionalities can found in the following generated html files:
* pm4py.algo.discovery.dcr_discover
* pm4py.algo.conformance.dcr
* pm4py.algo.conformance.alignment.dcr
* pm4py.objects.dcr


## usage
For usage, import the pm4py library, call the function
```
import pm4py


# to discover dcr graph
log_path = os.path.join("..","tests","input_data","running-example.xes")
log = pm4py.read_xes(log_path)
graph, _ = pm4py.discover_dcr(log)

# export dcr graph
output_path = os.path.join("..","tests","test_output_data","dcr.xml")
pm4py.write_dcr_xml(graph,path=output_path,
                        variant=Variants.XML_DCR_PORTAL, dcr_title="dcr graph of running-example")
```
For more indepth tutorial look at tutorial in  

## Requirements
Contains the same requirements for installation as provided in [PM4Py-core
](https://github.com/pm4py/pm4py-core/tree/release)

## Installation
create a a virtual environment in python and
```
pip install -r requirements.text


```

## License
licensed under [GPLv3](https://github.com/paul-cvp/pm4py-dcr/blob/develop/LICENSE)
