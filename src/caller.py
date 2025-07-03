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
t = mg.solve(target=state_vector,
             inputs=inputs,
             min_index=1, 
             search_depth=5000,
             to_print=True,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.INFO)
if t is not None:
    print(t.value)
else:
    print("No solutions found")