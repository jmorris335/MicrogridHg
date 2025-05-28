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
    time_step: 60,
}

# Debugging options, also set logging_level to 12 or lower
debug_nodes = {'state_vector'} if False else None
debug_edges = {'calc_battery_charge_level'} if True else None

# Solve for a single node
t = sg.solve(target=BATTERYs[0].state,
             inputs=inputs,
             min_index=3, 
             search_depth=3000, to_print=False,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.INFO)

if t is not None:
    print(t.value)
else:
    print("No solutions found")

nodes_to_solve = [PVs[0].state]
# solve_and_plot(sg, nodes_to_solve, inputs, [43 for a in nodes_to_solve])

# Solve for and plot actor states
solve_and_plot_states(sg, inputs, 1000)