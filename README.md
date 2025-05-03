# Microgrid Constraint Hypergraph

This model describes the behavior of a microgrid, formalized in a constraint hypergraph.

<h1 align="center">
<img src="https://github.com/jmorris335/MicrogridHg/blob/4289387eb6b0bc1965528751422b321f03f0e465/media/microgrid.png?raw=true" width="500">
</h1>

## Files:
- `microgrid.py`: The main model, as well as the caller for the simulation. Described in detail below in [Usage](#usage).
- `microgrid_actors.py`: Class definitions for the actors composing the grid.
- `microgrid_relations.py`: Methods providing custom rules for the functional relations of the edges in the constraint hypergraph.
- `building_data/`: directory of CSV files specifying loads for various buildings used on the grid.
- `solar_data/`: directory of data on historical solar radiation received for ten different years as CSV files, as well as a typical year (non-historical).
- `media/`: images for the hypergraph that cannot be republished.

## Usage
This package has been released under the MIT license. Though not 
required by the license, if you do end up using this package or making 
changes we would love to hear about it! Please reach out via our GitHub 
profiles.

## Overview
The default configuration of the microgrid consists of 12 actors of 5 
different types: batteries (2), buildings (5), generators (2), 
photovoltaic arrays (1), all connected to each other and the greater 
utility grid along 2 busses. An overview of their connections is given 
in the 
[visual plot](https://github.com/jmorris335/MicrogridHg/blob/main/media/microgrid%20chg.png) 
of the constraint hypergraph.

## Structure
The only package requirements are ConstraintHg, a breadth-first 
hypergraph solver available [here](https://github.com/jmorris335/ConstraintHg) 
and on the Python Package Index. Once you've downloaded the repository, 
you can install the latest version of ConstraintHg by calling 

```
pip install constrainthg
```

The model is simulated by `caller.py`, which calls `microgrid.py` to 
build the Microgrid. The structure of the program is:

1. **Setup actors** 
The actors are techinically classes, but the data for each class is 
exclusively a set of nodes that are fully integrated into the hypergraph. 
It's better to think of the classes as containers of patterns than as 
data structures, since they don't provide methods for serialized messaging. 
The classes are defined in `microgrid_actors.py`. This section is where 
you can characterize the microgrid--adding more grid actors (such as 
buildings) as needed, as well as how the grid is initially connected.

1. **Define nodes**
Each node is defined in this section by calling the `Node` constructor 
from the ConstraintHg package. This section is where labels are provided 
for the various state variables of the system, with the exception of the 
the nodes for each grid object (provided in the previous section). 
Variables that have static values (such as the `output_filename`) 
can be set in the constructor call here. More information is available 
at the documentation 
[here](https://constrainthg.readthedocs.io/en/latest/constrainthg.html#constrainthg.hypergraph.Node.__init__).

1. **Define relationships**
The constraints in the hypergraph are given by functions, most of which 
are defined in `microgrid_relations`, though some generic ones are given 
in the `ConstraintHg.relations` module. Each function is a normal Python
 method that takes in a set of values as parameters and returns a single
 value (including arraylike values such as lists and tuples). The only 
 caveat is that each method must take in an arbitrary set of keyed and 
 unkeyed arguments--in other words the arguments must be in the following 
 style:
```python
    def method_name(arg1, arg2, ..., argn, *args, **kwargs):
```
where the arguments `arg1` through `argn` are the arguments (with 
arbitrary names), followed by `*args`, `**kwargs` (note the name is not 
necessary, only the asterisk variable packing). 

1. **Define edges**
This is the true modeling of the hypergraph. Each edge is formed by 
calling the `Hypergraph.add_edge` method (documentation 
[here](https://constrainthg.readthedocs.io/en/latest/constrainthg.html#constrainthg.hypergraph.Hypergraph.add_edge)). The first argument of the call is a list of nodes forming 
the edge's domain. If the edges need to be referenced, they can be 
provided as a dict. The second argument is the node will be set by the 
edge (the codomain of the function). The third (and final required) 
argument is the handle of the method for calculating the function mapping. 
Some of these are defined in the previous section, while others are 
taken from the `relations` module in the ConstraintHg package. Other 
options, such as setting validity frames or moving through cycles, is 
explained in the wiki for the package, 
[here](https://github.com/jmorris335/ConstraintHg/wiki) and in the 
[documentation](https://constrainthg.readthedocs.io/en/latest/constrainthg.html#constrainthg.hypergraph.Hypergraph.add_edge).

1. **Run Simulation**
The final section actually conducts the simulation. Simulation is 
performed by passing the node to be simulated to the `Hypergraph.solve` 
method (documentation 
[here](https://constrainthg.readthedocs.io/en/latest/constrainthg.html#constrainthg.hypergraph.Hypergraph.solve)). There are options here to define inputs and logging options for
 debugging. Note that if you want to debug, you'll need to set the 
 logging level to `logging.DEBUG` in the ConstraintHg `__init__` file 
 (this is inconvenient, but necessary for now), likely in your 
 `.venv/lib/constrainthg` directory. You can also solve for a specific 
 index of a node (by passing a value for the `min_index` argument). In 
 the microgrid, must cycles relate to hour-long timestepping, so to find
 the state of a battery after 14 hours you might pass `min_index=15` to
  the `solve` method.