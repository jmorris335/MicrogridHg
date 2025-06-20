"""Helper class for plotting."""
import matplotlib.pyplot as plt
import constrainthg as chg
from collections import defaultdict
from itertools import zip_longest

plt.rcParams['font.family'] = 'times'
plt.rcParams['font.size'] = 14
plt.rcParams['font.weight'] = 'bold'

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
        found_values = solve_and_append(hg, found_values, node, inputs, min_index, to_print=False)
        if found_values is not None:
            if len(found_values[node.label]) < min_index:
                found_values[node.label] = [] #clear previous find
                for index in range(min_index):
                    found_values = solve_and_append(hg, found_values, node, inputs, index, to_print=False)

    labels = [n.label for n in nodes if n.label in found_values]
    plot_time_values(labels, found_values, 'time')

def solve_and_append(hg: chg.Hypergraph, found_values: dict, node: chg.Node, inputs: dict, min_index: int, **kwargs):
    """Solves the graph for the node at the given index and adds its value to the dict of found values."""
    t = hg.solve(node, inputs, min_index=min_index, to_print=False)
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
        times = [t / 3600 for t in found_values[time_step]]
    for label in labels:
        dash = dashes[labels.index(label) % len(dashes)]
        if isinstance(label, chg.Node):
            legend_label = label.label + f', ({label.units})' if label.units is not None else ''
            label = label.label
        else:
            legend_label = label
        values = found_values[label]
        if not isinstance(time_step, str):
            times = [time_step * i / 3600 for i in range(len(values))]
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
                          state_vector: str='state_vector', time: str='time', 
                          **kwargs):
    """Solves the Hypergraph for the `state_vector`, then plots the 
    state of each actor on the grid."""
    t = mg.solve(state_vector, inputs=inputs, min_index=min_index, **kwargs)
    fv = t.values
    names = fv.get('names', [mg.solve('names', inputs=inputs).value])[0]
    states = defaultdict(list)
    states['time'] = fv['time']
    for sv in fv[state_vector]:
        for state_value, name in zip(sv, names):
            if 'bus' in name.lower():
                continue
            states[name].append(state_value)
    outnames = [n for n in names if 'bus' not in n.lower()]
    plot_time_values(outnames, states, time, 
                     title='States of Grid Actors', ylabel='Power (kW)')
    
def plot_general_study(mg: chg.Hypergraph, **inputs: dict):
    """Solves the microgrid and plots the states over a 168 hour period 
    (roughly one week)."""

    fig, axs = plt.subplots(2,1, figsize=(10,4))

    default_inputs = {
        'start_day': 100,
        'start_year': 2005,
        'start_hour': 6,
        'use_random_date': False,
        'has_random_failure': False,
        'island_mode': True,
        'time_step': 3600,
    }
    inputs.update(**default_inputs)

    plot_data = [
        ('Battery1', 'BESS', '#00bb55', '-'),
        ('Building5Warehouse', 'Warehouse', '#002266', '-'),
        ('Building1Small', 'Small Building (1)', '#0055aa', '--'),
        ('Building2Small', 'Small Building (2)', '#0055aa', '-.'),
        ('Building3Medium', 'Medium Building', '#0055aa', ':'),
        ('Building4Large', 'Large Building', '#0055aa', '-'),
        ('Generator1', 'Generator (1)', '#8833bb', '-'),
        ('Generator2', 'Generator (2)', '#8833bb', '--'),
        ('PV1', 'Photovoltaic Array', '#ddaa00', '-'),
    ]

    for ax in axs:
        mg.reset()
        if not inputs['island_mode']:
            plot_data.append(('UtilityGrid', 'Utility Grid', '#ff5555', '-'))

        t = mg.solve('state_vector', inputs=inputs, min_index=168)
        fv = t.values
        times = [t/3600 for t in fv['time']]
        names = fv['names'][0]

        states = {}
        for actor_tuple in plot_data:
            name = actor_tuple[0]
            values = [sv[names.index(name)] for sv in fv['state_vector']]
            states[name] = values

        lines = []
        for name, label, color, dash in plot_data:
            values = states[name]
            lines.append(ax.plot(times[:len(values)], values[:len(times)],
                        lw=2, label=label, color=color, linestyle=dash)[0])
            
        
        ax.set_ylabel('Power (kW)')
        inputs['island_mode'] = False

    axs[-1].legend(handles=lines,
               loc='lower center',
               bbox_to_anchor=(0.5, -0.4),
               ncols=5,
               frameon=False,
    )

    axs[-1].set_xlabel('Time (hours)')
    plt.show()


    
def plot_validation_study(sg: chg.Hypergraph, inputs: dict, min_index: int=2500,
                           **kwargs):
    """Solves the validation microgrid and plots the validation study."""
    t = sg.solve('state_vector', inputs=inputs, min_index=min_index, 
                 search_depth=500000, **kwargs)
    fv = t.values
    names = fv['names'][0]
    csvdata = fv['validation_data']
    times = [t / 3600 for t in fv['time']]
    labels = ['BESS', 'Generator', 'Photovoltaic Array', 'Test Load']
    # csv_tags = ['Battery Power (kW)', 'Generator power (kW)', 'Solar Power (kW)', 'Powerload (kW)']
    csv_tags = ['Battery Power (kW)', 'Generator power (kW)']
    csv_labels = ['BESS (measured)', 'Generator (measured)']
    colors = ['#00bb55', '#8833bb', '#ddaa00', '#0055aa']
    styles = ['-', '-', '--', '--']

    states = defaultdict(list)
    for sv in fv['state_vector']:
        for state_value, name in zip(sv, names):
            if name not in labels:
                continue
            states[name].append(state_value)

    fig, ax = plt.subplots(figsize=(10,4))

    csv_lines = []
    for tag, color, label in zip(csv_tags, colors[:len(csv_tags)], csv_labels):
        csvvalues = [float(d[tag]) for d in csvdata[0]]
        csv_lines.append(ax.plot(times[:len(csvvalues)], csvvalues[:len(times)],
                lw=5, color=color + '55', linestyle='-', label=label)[0])

    chg_lines = []
    for label, color, style in zip(labels, colors, styles):
        values = states[label]
        if label is labels[-1]:
            values = [-a for a in values]
        chg_lines.append(ax.plot(times[:len(values)], values[:len(times)],
                lw=2, color=color, linestyle=style, label=label)[0])

    ordered_lines = []
    for pair in zip_longest(chg_lines, csv_lines):
        ordered_lines.extend([val for val in pair if val is not None])

    # Place legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + 0.2, box.width, box.height * 0.75])

    plt.legend(handles=ordered_lines,
               loc='lower center',
               bbox_to_anchor=(0.5, -0.2),
               ncols=len(labels),
               frameon=False,
    )

    ax.set_ylabel('Power (kW)')
    ax.set_xlabel('Time (hours)')
    # plt.title('Simluated Microgrid States vs. Measured Performance')
    plt.show()