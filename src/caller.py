from model.microgrid import *
from aux.plotter import *
import logging

# Inputs
inputs = {
    use_random_date: False,
    start_day: 100,
    start_year: 2004,
    start_hour: 12,
    has_random_failure: False,
    island_mode: False,
    time_step: 3600,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_vector'} if False else None
debug_edges = {'make_state_vector'} if False else None

# Solve for a single node
t = mg.solve(target=BATTERYs[0].soc,
             inputs=inputs, min_index=0, 
             search_depth=5000, to_print=False,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.INFO)
if t is not None:
    print(t.value)
else:
    print("No solutions found")

# Solve for and plot actor states
solve_and_plot_states(mg, inputs, 72)

# Solve for multiple nodes and indices (exhaustive)
# solve_and_plot(mg, [BATTERYs[0].cost, GENs[1].cost], inputs, indices=[0, 0])