from validation.spanagel_hg import *
from aux.plotter import *
import logging

# Inputs
inputs = {
    valid_data_path: 'src/validation/Spanagel_Test_29APR-1MAY2025.csv',
    use_random_date: False,
    start_day: 119,
    start_year: 2025,
    start_hour: 15,
    has_random_failure: False,
    island_mode: True,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_matrix'} if False else None
debug_edges = {'calc_solar_supply'} if False else None

# Solve for a single node
t = shg.solve(
            target=GENs[0].state,
            inputs=inputs,
            min_index=0, 
            search_depth=1000, to_print=False,
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