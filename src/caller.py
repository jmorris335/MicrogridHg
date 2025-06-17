from model.microgrid import *
from aux.plotter import *
import logging

# Inputs
inputs = {
    use_random_date: False,
    start_day: 100,
    start_year: 2005,
    start_hour: 6,
    has_random_failure: False,
    island_mode: True,
    time_step: 3600,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_vector'} if False else None
debug_edges = {'make_state_vector'} if False else None

# Solve for a single node
t = mg.solve(target=PVs[0].state,
             inputs=inputs,
             min_index=5, 
             search_depth=5000,
             to_print=False,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.INFO)
if t is not None:
    print(t.value)
else:
    print("No solutions found")

# plot_general_study(mg)