# Dcr4py: An extension of pm4py for declarative Dynamic Condition Response Graphs

## Features

New features added compared to pm4py:
* DcrGraph objects: Role, MilestoneNoResponse, NestingSubprocess, Timed, Import (from DCR Portal[1] and DCR js[2]), Export (to DCR Portal[2] and DCR js[2])
* Conformance: Alignments, Rule based
* Discovery with extensions: Role, Pending, Timed
* Visualization: DcrGraph visualization with graphviz

## Runnning the demo: For ICPM 2024 demonstration purposes follow this guide

I recommend you use github codespaces: https://github.com/codespaces

Follow the steps below:

0. Create a github account if you don't already have one.
1. Got to https://github.com/codespaces
2. Find the "Jupyter Notebook" start template and click "Use this template"
3. Download the github code as a zip file: https://github.com/paul-cvp/pm4py-dcr/tree/feature/dcr_in_pm4py_revised (click on the green button and then click "download zip")
4. Unzip in your local machine
5. Drag all the unzipped files and folders into the left "EXPLORER" box of the Codespace, once you do that it will start uploading quite slowly, so wait for the upload to complete (you can also right click an empty space in the EXPLORER box and select "Upload")
6. Once at least the new "requirements.txt" file is uploaded, in the bottom box with the "TERMINAL" header type "pip install -r requirements.txt", this will also take some time.
7. Open the "dcr_tutorial.ipynb" in the notebooks folder and run the notebook cell by cell using Shift + Ctrl. If a pop up appears telling you to "Select kernel", then go to "Python Environments" and select "Python 3.1X.XX" as your python environment. 

Now you should be good to go. Any interactions with the files and folders you need to move between your machine and codespaces should be handled with right click "Upload/Download" from the "EXPLORER" box.

## Documentation: For ICPM 2024 demonstration purposes

Generated documentation available at: https://paul-cvp.github.io/dcr4pydocs/

Optionally you can generate the documentation (step 5 does not work in codespaces unless you install the HTML Preview extension inside the codespace):

1. In your virtual python environment run: 
```
pip install -U sphinx
pip install sphinx-autodoc-annotation
pip install pydata-sphinx-theme
```
2. Move to the docs folder: ```cd docs```
3. Generate all the .rst file using: ```python -m setup```
4. Run ```make html```
5. Inside "docs/build/html" you can open the ```index.html``` file in your browser and navigate around the documentation

## DCR4Py contributors

[paul-cvp](https://github.com/paul-cvp),[Timmovich](https://github.com/Timmovich), [Scones111](https://github.com/Scones111), [RagnarLaki](https://github.com/RagnarLaki), 
[simonhermansen](https://github.com/simonhermansen), [Axel](https://github.com/Axel0087), [Tijs](https://github.com/tslaats)

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# pm4py (documentation from the source repo)
pm4py is a python library that supports (state-of-the-art) process mining algorithms in python. 
It is open source (licensed under GPL) and intended to be used in both academia and industry projects.
pm4py is managed and developed by Process Intelligence Solutions (https://processintelligence.solutions/).
pm4py was initially developed at the Fraunhofer Institute for Applied Information Technology FIT.

## Documentation / API
The full documentation of pm4py can be found at https://processintelligence.solutions/

## First Example
A very simple example, to whet your appetite:

```python
import pm4py

if __name__ == "__main__":
    log = pm4py.read_xes('<path-to-xes-log-file.xes>')
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
    pm4py.view_petri_net(net, initial_marking, final_marking, format="svg")
```

## Installation
pm4py can be installed on Python 3.9.x / 3.10.x / 3.11.x / 3.12.x by invoking:
*pip install -U pm4py*

pm4py is also running on older Python environments with different requirements sets, including:
- Python 3.8 (3.8.10): third_party/old_python_deps/requirements_py38.txt

## Requirements
pm4py depends on some other Python packages, with different levels of importance:
* *Essential requirements*: numpy, pandas, deprecation, networkx
* *Normal requirements* (installed by default with the pm4py package, important for mainstream usage): graphviz, intervaltree, lxml, matplotlib, pydotplus, pytz, scipy, tqdm
* *Optional requirements* (not installed by default): requests, pyvis, jsonschema, workalendar, pyarrow, scikit-learn, polars, openai, pyemd, pyaudio, pydub, pygame, pywin32, pygetwindow, pynput

## Release Notes
To track the incremental updates, please refer to the *CHANGELOG* file.

## Third Party Dependencies
As scientific library in the Python ecosystem, we rely on external libraries to offer our features.
In the */third_party* folder, we list all the licenses of our direct dependencies.
Please check the */third_party/LICENSES_TRANSITIVE* file to get a full list of all transitive dependencies and the corresponding license.

## Citing pm4py
If you are using pm4py in your scientific work, please cite pm4py as follows:

**Alessandro Berti, Sebastiaan van Zelst, Daniel Schuster**. (2023). *PM4Py: A process mining library for Python*. Software Impacts, 17, 100556. [DOI](https://doi.org/10.1016/j.simpa.2023.100556) | [Article Link](https://www.sciencedirect.com/science/article/pii/S2665963823000933)

BiBTeX:

```bibtex
@article{pm4py,  
title = {PM4Py: A process mining library for Python},  
journal = {Software Impacts},  
volume = {17},  
pages = {100556},  
year = {2023},  
issn = {2665-9638},  
doi = {https://doi.org/10.1016/j.simpa.2023.100556},  
url = {https://www.sciencedirect.com/science/article/pii/S2665963823000933},  
author = {Alessandro Berti and Sebastiaan van Zelst and Daniel Schuster},  
}
```

