from microgrid import *
from plotter import plot_time_values

## Inputs
inputs = {
    use_random_date: False,
    start_day: 90,
    start_year: 2006,
    start_hour: 13,
    sim_length_hours: 24,
    has_random_failure: False
}

## Debugging options, also set __init__.LOG_LEVEL equal to logging.DEBUG
debug_nodes = {conn_matrix} if False else None
debug_edges = {'form demand matrix', 'calc building demand'} if True else None

# print([mg.solve(BATTERYs[0].state, inputs, min_index=i).value for i in range(4)])


t = mg.solve(BATTERYs[0].state, inputs, min_index=3, to_print=False, 
             search_depth=5000, debug_nodes=debug_nodes, debug_edges=debug_edges)
print(t)