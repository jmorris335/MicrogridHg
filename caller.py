from microgrid import *
from plotter import *

## Inputs
inputs = {
    use_random_date: False,
    start_day: 5,
    start_year: 2006,
    start_hour: 0,
    has_random_failure: False
}

## Debugging options, also set logging_level to 12 or lower
debug_nodes = {elapsed_hours, start_year} if False else None
debug_edges = {'form demand matrix'} if False else None

# print([mg.solve(sunlight, inputs, min_index=i).value for i in range(10)])

t = mg.solve(state_matrix, inputs, min_index=2, to_print=False, search_depth=3000, 
             debug_nodes=debug_nodes, debug_edges=debug_edges)
print(t.value)

# solve_and_plot(mg, [BATTERYs[0].state, elapsed_hours, sunlight, BUILDINGs[0].state], inputs, 
#                     indices=[5, 5, 5, 5])

# print(t)

#TODO: Need some kind of function that repeatedly calls the hypergraph until paths for each index of a node are found, building up a dictionary of found nodes on the way, and using the last index of the found nodes as inputs for the next iterative call.