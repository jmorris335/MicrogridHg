from model.microgrid import *
from aux.plotter import *
import logging

# Inputs
inputs = {
    use_random_date: False,
    start_day: 100,
    start_year: 2004,
    start_hour: 9,
    has_random_failure: False,
    island_mode: True,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_matrix'} if False else None
debug_edges = {'calc_solar_supply'} if True else None

# Solve for a single node
t = mg.solve(
            target=state_matrix,
            # target=GENs[0].max_consumption,
            inputs=inputs, min_index=3, 
            search_depth=3000, to_print=False,
            debug_nodes=debug_nodes, debug_edges=debug_edges, 
            logging_level=logging.INFO)
if t is not None:
    print(t.value)
else:
    print("No solutions found")

# Solve for and plot actor states
# solve_and_plot_states(mg, inputs, 72)

# Solve for multiple nodes and indices (exhaustive)
# solve_and_plot(mg, [PVs[0].demand, elapsed_hours, sunlight, 
#                BUILDINGs[0].demand], inputs, indices=[5, 5, 5, 5])