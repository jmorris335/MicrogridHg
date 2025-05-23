"""Helper class for plotting."""
import matplotlib.pyplot as plt
import constrainthg as chg
from collections import defaultdict

plt.rcParams['font.family'] = 'times'

def solve_and_plot(hg: chg.Hypergraph, nodes: list, inputs: dict, indices: list=None):
    """Solves the graph for each of the nodes (at the given indices) and plots the results."""
    found_values = {}
    if indices is None:
        indices = [1 for n in nodes]
    else:
        indices = [1 if i is None else i for i in indices]

    for node, min_index in zip(nodes, indices):
        if len(found_values.get(node.label, [])) >= min_index:
            continue
        found_values = solve_and_append(hg, found_values, node, inputs, min_index, to_print=False, search_depth=5000)
        if found_values is not None:
            if len(found_values[node.label]) < min_index:
                found_values[node.label] = [] #clear previous find
                for index in range(min_index):
                    found_values = solve_and_append(hg, found_values, node, inputs, index, to_print=False, search_depth=5000)

    labels = [n.label for n in nodes if n.label in found_values]
    plot_time_values(labels, found_values, 'elapsed hours')

def solve_and_append(hg: chg.Hypergraph, found_values: dict, node: chg.Node, inputs: dict, min_index: int, **kwargs):
    """Solves the graph for the node at the given index and adds its value to the dict of found values."""
    t = hg.solve(node, inputs, min_index=min_index, to_print=False, search_depth=5000)
    if t is None:
        return None
    if node.label not in found_values:
        found_values[node.label] = []
    found_values[node.label].extend(t.values[node.label])
    found_values =  t.values | found_values
    return found_values

def plot_time_values(labels: list, found_values: dict, time_step: float, 
                   title: str='Simulation', ylabel: str='Variables'):
    """Plots the values in the dictionary as a function of time.
    
    Parameters
    ----------
    labels : List[str, | Node,]
        A list of node labels to plot, either as strings or the Node objects.
    found_values : Dict{label : list}
        A list of values found for a given node label, generated by Hypergraph.solve()
    time_step : float | str
        The time step for the simulation used for calculating times, or the label of 
        the time node in the `found_values` parameter.
    title : str, optional
        The title of the plot.
    ylabel : str, optional
        The label for the vertical axis.
    """
    dashes = ['--', ':', '-.']
    legend = []
    if isinstance(time_step, str):
        times = found_values[time_step]
    for label in labels:
        dash = dashes[labels.index(label) % len(dashes)]
        if isinstance(label, chg.Node):
            legend_label = label.label + f', ({label.units})' if label.units is not None else ''
            label = label.label
        else:
            legend_label = label
        values = found_values[label]
        if not isinstance(time_step, str):
            times = [time_step * i for i in range(len(values))]
        # plt.plot(times[:len(values)], values[:len(times)], 'k', lw=2, linestyle=dash) 
        plt.plot(times[:len(values)], values[:len(times)], lw=2) 
        legend.append(legend_label)

    # Place legend
    ax = plt.gca()
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5))

    plt.ylabel(ylabel)
    plt.xlabel('Time (hours)')
    plt.title(title)
    plt.show()

def solve_and_plot_states(mg: chg.Hypergraph, inputs: dict, min_index: int=8,
                          state_vector: str='state_matrix',):
    """Solves the Hypergraph for the `state_vector`, then plots the 
    state of each actor on the grid."""
    t = mg.solve(state_vector, inputs=inputs, min_index=min_index)
    fv = t.values
    names = fv.get('names', [mg.solve('names', inputs=inputs).value])[0]
    states = defaultdict(list)
    states['elapsed_hours'] = fv['elapsed hours']
    for sv in fv[state_vector]:
        for state_value, name in zip(sv, names):
            states[name].append(state_value)
    plot_time_values(names, states, 'elapsed_hours', 
                     title='States of Grid Actors', ylabel='Power (kW)')