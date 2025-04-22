from microgrid import *
from plotter import *
import logging

## Inputs
inputs = {
    use_random_date: False,
    start_day: 5,
    start_year: 2006,
    start_hour: 0,
    has_random_failure: False,
    island_mode: False
}

## Debugging options, also set logging_level to 12 or lower
debug_nodes = {'demand_pair_Generator1'} if True else None
debug_edges = {'form demand matrix'} if False else None


t = mg.solve(BATTERYs[0].state, inputs, min_index=5, to_print=False, search_depth=3000, 
             debug_nodes=debug_nodes, debug_edges=debug_edges, logging_level=logging.INFO)
print(t.value)

# solve_and_plot(mg, [BATTERYs[0].state, elapsed_hours, sunlight, BUILDINGs[0].state], inputs, 
#                     indices=[5, 5, 5, 5])