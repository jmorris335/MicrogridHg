from microgrid import *
from plotter import *
import logging

# Inputs
inputs = {
    use_random_date: False,
    start_day: 5,
    start_year: 2006,
    start_hour: 9,
    has_random_failure: False,
    island_mode: False,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_matrix'} if False else None
debug_edges = {'calc_solar_demand'} if True else None

# Solve for a single node
t = mg.solve(state_matrix,
             inputs, min_index=4, 
             search_depth=3000, to_print=False,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.DEBUG)
if t is not None:
    print(t.value)
else:
    print("No solutions found")

# Solve for multiple nodes and indices (exhaustive)
# solve_and_plot(mg, [PVs[0].demand, elapsed_hours, sunlight, 
#                BUILDINGs[0].demand], inputs, indices=[5, 5, 5, 5])