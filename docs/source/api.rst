API Reference
=============
This page provides an overview the extension ``DCR4Py`` for ``pm4py``.

Note the pm4py.discovery, pm4py.conformance etc. contain the top level api calls for pm4py, in which the function found here have been implemented.
However the subpackages should only the implemented extension.

Process Discovery (:mod:`pm4py.discovery`)
------------------------------------------
``DCR4Py`` allows for discovery of DCR graphs.
Note that the implemented algorithm always discover a perfect fitting graph.

  * :meth:`pm4py.discovery.discover_dcr`; discovers a *DCR Graph*.


Conformance Checking (:mod:`pm4py.conformance`)
-----------------------------------------------
``DCR4Py`` contains two conformance checking methods:

  * :meth:`pm4py.conformance.conformance_dcr`; rule based conformance checking using a *DCR Graph*
  * :meth:`pm4py.conformance.optimal_alignment_dcr`; optimal alignment conformance checking using a *DCR Graph*


Visualization (:mod:`pm4py.vis`)
------------------------------------------
``DCR4Py`` allow visualization of DCR graphs and storing them.

  * :meth:`pm4py.vis.view_dcr`; views a *DCR graph*.
  * :meth:`pm4py.vis.save_vis_dcr`; saves the visualization of a *DCR graph*.

Read (:mod:`pm4py.read` and :mod:`pm4py.write`)
------------------------------------------
``DCR4Py`` can import and export dcr graphs as xml.

  * :meth:`pm4py.write.write_dcr_xml`; exports a *DCR graph* to xml.
  * :meth:`pm4py.read.read_dcr_xml`; imports a *DCR graph* from xml.

Conversion (:mod:`pm4py.convert`)
-------------------------------------
``DCR4Py`` also allows for the conversion of a DCR graph to petri net.
The current existing function within pm4py has been extended to also handle DCR graphs.

  * :meth:`pm4py.convert.convert_to_petri_net` converts a process model to Petri net

Overall List of Methods
------------------------------------------

.. autosummary::
   :toctree: generated

   pm4py.read.read_dcr_xml
   pm4py.write.write_dcr_xml
   pm4py.convert.convert_to_petri_net
   pm4py.discovery.discover_dcr
   pm4py.conformance.conformance_dcr
   pm4py.conformance.optimal_alignment_dcr
   pm4py.vis.view_dcr
   pm4py.vis.save_vis_dcr
