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
debug_edges = {'calc_battery_charge_level'} if False else None

# Solve for a single node
t = sg.solve(target=state_vector,
             inputs=inputs,
             min_index=25, 
             search_depth=100000,
             to_print=False,
             debug_nodes=debug_nodes, debug_edges=debug_edges, 
             logging_level=logging.INFO)

if t is not None:
    print(t.value)
else:
    print("No solutions found")

plot_validation_study(sg, inputs, min_index=2500)
