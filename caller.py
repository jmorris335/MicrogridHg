from microgrid import *
from plotter import *
import logging

## Inputs
inputs = {
    use_random_date: False,
    start_day: 5,
    start_year: 2006,
    start_hour: 9,
    has_random_failure: False,
    island_mode: False
}

## Debugging options, also set logging_level to 12 or lower
debug_nodes = {'is_connected_Building1Small'} if True else None
debug_edges = {'calc building demand', '(is_f,Buil)->is_conne'} if True else None

# Solve for a single node
#FIXME: The UG is one step behind all of the load decisions. It should be moved to be one step ahead of decisions, but that might require and initial state input.
    #There should be a way to make it so the first index of UG's demand is the total balance of the grid
    #Need to add a node that calculates the total load on the microgrid, which would be used to control the UG. Batteries and Gens can be a step behind.
t = mg.solve(UGs[0].demand, inputs, min_index=1, to_print=False, search_depth=3000, 
             debug_nodes=debug_nodes, debug_edges=debug_edges, logging_level=logging.DEBUG+1)
print(t.value)

# Solve for multiple nodes and indices (exhaustive)
# solve_and_plot(mg, [PVs[0].demand, elapsed_hours, sunlight, BUILDINGs[0].demand], inputs, indices=[5, 5, 5, 5])