from microgrid import *
from plotter import plotTimeValues

## Inputs
inputs = {
    use_random_date: False,
    start_day: 41,
    start_year: 2006,
    start_hour: 13,
    sim_length_hours: 24,
}

## Debugging options, also set __init__.LOG_LEVEL equal to logging.DEBUG
debug_nodes = {conn_matrix} if False else None
debug_edges = {'calc building demand'} if False else None


t, found_values = mg.solve(GENs[0].state, inputs, min_index=10, to_print=False, 
                           search_depth=5000, debug_nodes=debug_nodes, debug_edges=debug_edges)
print(t)

if t is not None:
    labels = [n.label for n in [BUILDINGs[0].state, PVs[0].state, BATTERYs[0].state, GENs[0].state, UGs[0].state]]
    labels = [l for l in labels if l in found_values]
    plotTimeValues(labels, found_values, 'elapsed hour')