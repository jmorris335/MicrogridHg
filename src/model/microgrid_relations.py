import constrainthg.relations as R
import random
import csv
import numpy as np
import logging

from model.microgrid_actors import *

#TODO: We shouldn't be passing information by node IDs, this should be implemented with tuples
KEY_SEP = '¦&¦' #A unique constant for seperating strings in paired keywordss

def generate_connectivity_keyword(OBJ_to, OBJ_from):
    """Generates a keyword for referencing the cell connecting OBJ_from 
    to OBJ_to."""
    name_to, name_from = [str(OBJ) for OBJ in (OBJ_to, OBJ_from)]
    keyword = f'{name_to}{KEY_SEP}{name_from}'
    return keyword

def generate_building_keyword(building: GridActor, keyword: str):
    """Generates a keyword for referencing the value of the building."""
    key = f'{keyword}{KEY_SEP}{str(building)}'
    return key


## Simulation
def Rget_random_year(min_year: int, max_year: int, **kwargs):
    """Returns a random year from the maximum range."""
    rand_year = random.randint(int(min_year), int(max_year))
    return rand_year

def Rget_random_day(days_in_year: int, **kwargs)-> int:
    """Returns a random int for a day (1-365)."""
    rand_day = random.randint(1, days_in_year)
    return rand_day

def Rget_random_hour(hours_in_day: int, **kwargs)-> int:
    """Returns a random int for an hour (0-23)."""
    rand_hour = random.randint(0, hours_in_day-1)
    return rand_hour

def Rcalc_year(elapsed_hours: int, num_leapyears: int, start_year: int, 
               start_day: int, start_hour: int, hours_in_day: int, 
               hours_in_year: int, **kwargs)-> int:
    """Calculates the current year of the simulation."""
    elapsed_hours += ((start_day - 1) * hours_in_day + start_hour)
    elapsed_hours -= hours_in_day * num_leapyears
    year = start_year + elapsed_hours // hours_in_year
    return year

def Rcalc_day(elapsed_hours: int, start_year: int, year: int, num_leapyears: int,
              start_day: int, start_hour: int, hours_in_day: int, 
               hours_in_year: int, **kwargs)-> int:
    """Calculates the current day of the simulation."""
    elapsed_years = year - start_year
    elapsed_hours -= hours_in_year * elapsed_years
    elapsed_hours -= (hours_in_day * num_leapyears)
    elapsed_hours += start_hour
    day =  start_day + elapsed_hours // hours_in_day
    return day

def Rcalc_hour(elapsed_hours: int, start_hour: int, hours_in_day: int, **kwargs)-> int:
    """Calculates the current hour of the simulation."""
    hour = (start_hour + elapsed_hours) % hours_in_day
    return hour

def Rcalc_num_leapyears(start_year: int, elapsed_hours: int, 
                        hours_in_year: int, hours_in_leapyear: int, **kwargs)-> int:
    """Returns the number of leapyears that the simulation has covered 
    (not counting the present year)."""
    num_leapyears = 0
    year = start_year
    while elapsed_hours > 0:
        year += 1
        is_leapyear = year % 4 == 0
        num_leapyears += is_leapyear
        elapsed_hours -= hours_in_leapyear if is_leapyear else hours_in_year
    return num_leapyears

def Rget_hour_index(day: int, hour: int, is_leapyear: bool, hours_in_day: int, 
                    hours_in_year: int, hours_in_leapyear: int, **kwargs):
    """Converts the day and hour into a integer for the hour of the year 
    (1-8784)"""
    max_h_i = hours_in_leapyear if is_leapyear else hours_in_year
    hour_idx = max(0, min(int(day * hours_in_day + hour), max_h_i))
    return hour_idx

def Rcalc_year_is_leapyear(year: int, **kwargs)-> bool:
    """Returns true if the year is a leapyear."""
    is_leapyear = year % 4 == 0
    return is_leapyear

def Rcalc_elapsed_minutes(elapsed_hours: int, **kwargs)-> int:
    """Returns the number of minutes passed in the simulation."""
    minutes = elapsed_hours * 60
    return minutes


### Data
def Rget_data_from_csv_file(filename: str, **kwargs)-> list:
    """Converts a CSV file to a list of dictionaries."""
    with open(filename, newline='') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data

def Rget_float_from_csv_data(csv_data: dict, row, col, **kwargs):
    """Returns the value in the row and column from the CSV dict reader."""
    value = float(csv_data[row][col])
    return value


## Microgrid
def Rsort_names(*args, **kwargs)->list:
    """Sorts the object names into a prefered list."""
    names = R.extend(args, kwargs)
    names.sort()
    return names

def Rdetermine_load(*args, **kwargs)->float:
    """Determines the amount of energy necessary to run the microgrid.
    
    Note output is always negative or zero, since loads are always 
    negative.
    """
    demands = R.extend(args, kwargs)
    load = -sum([abs(d) for d in demands if d < 0.])
    return load

def Rdetermine_if_connected(is_failing: bool, is_load_shedding: bool, **kwargs)-> bool:
    """Determines whether or not the object is connected to the grid."""
    return not (is_failing or is_load_shedding)

def Rcalc_if_receiving_power(receives_from: bool, receiver_conn: bool, 
                             provider_conn: bool, **kwargs)-> bool:
    """Determines if the receiver object is receiving power from the 
    provider object."""
    return receives_from and receiver_conn and provider_conn

def Rform_connectivity_matrix(names: list, key_sep: str, *args, **kwargs)-> np.ndarray:
    """Forms the connectivity (A) matrix where the ij-th cell indicates 
    power is flowing from object j to object i."""
    A = np.zeros((len(names), len(names)))
    # args, kwargs = R.get_keyword_arguments(args, kwargs, KEYNAMES)
    for key, val in kwargs.items():
        if key_sep in key:
            i,j = [names.index(name) for name in key.split(key_sep)[:2]]
            A[i][j] = 1 if bool(val) else 0
    return A

def Rget_state_from_matrix(x: np.ndarray, name: str, names: list, **kwargs)-> float:
    """Indexes and returns the state of the object in the state matrix."""
    i = names.index(name)
    out = x[i]
    return out

def Rlinear_solve(A: np.ndarray, B: np.ndarray, **kwargs)-> np.ndarray:
    """Solves the system of equations Ax = B for x."""
    x = np.linalg.solve(A, B)
    return x

def Rdeterming_if_failing(is_failing: bool, p_fail: float, p_fix: float, 
                          *args, **kwargs)-> bool:
    """Returns true if the actor is failing."""
    p = random.random()
    if not is_failing:
        return p > p_fail
    return not (p > p_fix)

def Rget_failing_actors(names: list, *args, **kwargs)-> list:
    """Returns a list of actors that are failing, where kwargs are of the 
    form ``{label : is_failing}."""
    failing = []
    for name in names:
        if kwargs.get(name, False):
            failing.append(name)
    return failing

def Rdetermine_if_loadshedding(state: float, req_demand: float, tol: float)-> bool:
    """Determines if the actor was required to be load shed from the grid."""
    if req_demand > tol:
        return state > tol
    return False

## Utility Grid
def Rcalc_ug_demand(conn: bool, islanded_balance: float, *args, **kwargs)-> float:
    """Calculates the demand of the utility grid based off of current 
    balance."""
    if not conn or islanded_balance > 0.:
        return 0.
    return abs(islanded_balance)


## Solar
def Rget_solar_filename(directory: str, year: str, **kwargs)-> str:
    """Returns the name of the CSV file with the solar data 
    corresponding to the given year."""
    out = f'{directory}/724915'
    if year >= 2000 and year <= 2009:
        out += f'_{year}_solar'
    else:
        out += 'TY'
    out += '.csv'
    return out

def Rcalc_solar_supply(conn: bool, area: float, efficiency: float, 
                       sunlight: float, **kwargs)-> float:
    """Calculates the power (in kW) produced by a photovoltaic cell over one hour."""
    # if not conn:
    #     return 0.0
    power = max(0, area * efficiency * sunlight)
    power = power / 1000
    return power


## Wind
def Rcalc_wind_supply(area: float, power_coef: float, velocity: float,
                      density: float)-> float:
    """Calculates the power (in kW) produced by a wind turbine over one hour."""
    supply = abs(1/2 * density * area * velocity**3 * power_coef)
    return supply

## Buildings
def Rget_building_filename(directory: str, building_type: BUILDING_TYPE, **kwargs)-> str:
    """Returns the name of the CSV file with the load data corresponding to the 
    building type."""
    out = f'{directory}/RefBldg{building_type.value}New2004_7-1_5-0_3C_USA_CA_SAN_FRANCISCO.csv'
    return out

def Rcalc_critical_load(lights: float, equipment: float, **kwargs)-> float:
    """Calculates the critical load for a building based on its light 
    and equipment usage."""
    cl = 0.5 * lights + 0.67 * equipment
    return cl

def Rdetermine_building_load(conn: bool, normal: float, critical: float, 
                             island: bool, **kwargs)-> float:
    """Determines the load of a building."""
    if not conn:
        return 0.0
    load = critical if island else normal
    return load

## Generators
def Rcalc_generator_demand(is_islanded: bool, load: float, max_out: float, 
                           out_of_fuel: bool, conn: bool, **kwargs)-> float:
    """Calculates how much power the generator is capable of supplying."""
    if any([not conn, not is_islanded, out_of_fuel]):
        return 0.
    return max(0., min(abs(load), max_out))

def Rcalc_next_time_for_refueling(refuel_time: int, curr_hour: int, 
                                  prob: float, hours_in_day: int, **kwargs):
    """Calculates the next time for refueling based on the current time."""
    if refuel_time > curr_hour:
        return refuel_time
    days_until_refuel = 0
    while prob < random.random(): 
        days_until_refuel += 1
    hours_until_refuel = random.randint(0, hours_in_day-1)
    next_time = refuel_time + days_until_refuel * hours_in_day + hours_until_refuel
    return next_time

def Rcalc_generator_fuel_level(refuel_time: int, curr_hour: int, curr_level: float, 
                               max_level: float, **kwargs)-> float:
    """Determines the fuel level of the generator."""
    if refuel_time > curr_hour:
        return curr_level
    return max_level

def Rcalc_generator_fuel_consumption(load: float, max_load: float, 
                                     *args, **kwargs)-> float:
    """Determines the fuel consumption of the generator. Data taken from
    https://generator.kubota.com/products/60hz/gl_7000.html, and are given
    in L/h."""
    load_prop = load / max_load
    consumption_rates = [2.6, 2.1, 1.7, 1.4] #L/h
    load_prop_intervals = [0.75, 0.5, 0.25, 0.]
    diff = [abs(load_prop - i) for i in load_prop_intervals]
    index = diff.index(min(diff))
    return consumption_rates[index]

def Rcalc_generator_cost(fuel_cost: float, output: float, consumption: float, 
                         *args, **kwargs)-> float:
    """Determines the cost of running the generator."""
    cost = fuel_cost * consumption / output
    return cost

## Batteries
def Rcalc_battery_demand(island: bool, is_charging: bool, load: float, 
                         level: float, capacity: float, max_rate: float, 
                         max_output: float, trickle_prop: float, **kwargs)-> float:
    """Calculates the demand of the battery."""
    if load < 0 and not island:
        highest_output = min(max_output, level)
        demand = max(0, min(abs(load), highest_output))
    elif is_charging:
        if level > 0.8 * capacity:
            demand = trickle_prop * max_rate
        else:
            demand = max_rate
        demand = -demand
    else:
        demand = 0
    return demand

def Rdetermine_battery_is_charging(island: bool, load: float, level: float, 
                                   capacity: float, **kwargs)-> bool:
    """Determines if the battery should be charging or not."""
    if not island or load < 0:
        return False
    return level < capacity

def Rcalc_battery_charge_level(state: float, level: float, max_level: float, 
                               time_step: float, **kwargs)-> float:
    """Calculates the charge level of the battery based on power flow (W)."""
    expected_level = level + state * time_step
    new_level = max(0, min(expected_level, max_level))
    return new_level

def Rcalc_battery_cost(ug_cost: float, tol: float, level: float, 
                       capacity: float, factor: float):
    """Calculate the cost of using the battery."""
    if level <= tol:
        return float('inf')
    level_factor = (1 - level / capacity) * factor
    cost = ug_cost + (ug_cost * level_factor)
    return cost

def Rcalc_battery_benefit(ug_cost: float, level: float, capacity:float, factor: float):
    """Calculate the benefit of charging the battery."""
    if level >= capacity:
        return 0.
    level_factor = level / capacity * factor
    benefit = ug_cost + (ug_cost * level_factor)
    return benefit

def Rcalc_battery_max_demand(level: float, capacity: float, max_rate: float, 
                             trickle_prop: float, **kwargs)-> float:
    """Calculates the maximum power the battery can receive."""
    if level > 0.8 * capacity:
        demand = trickle_prop * max_rate
    else:
        demand = max_rate
    demand = -abs(demand)
    return demand


## Power distribution strategy
def Rmake_demand_vector(conn: list, names: list, tol: float, 
                       *args, **kwargs)->list:
    """Determines the demand for each object on the grid.

    Parameters
    ----------
    conn : List[List] | Dict[List] | Dict[Dict]
        A nxn boolean matrix where each entry describes whether the ith 
        element can send power to the jth element.
    names : list
        List of n ordered labels of actors on the grid corresponding 
        both the rows and columns of ``conn``.
    tol : float
        Minimum value used for floating point comparisons with zero.
    **kwargs : dict
        Must contain n source tuples and n demand tuples keyed with a 
        keyword containing either ``source_tuples`` or ``demand_tuples`` 
        respectively. Source tuples are of the format ``(label, cost, 
        supply)``, while demand tuples should follow ``(label, benefit, 
        req_demand, max_demand)``, with the label corresponding to the 
        name in ``names``.

    Process
    -------
    1. Use connectivity matrix to determine connected circuits.
    2. Generate a supply queue and demand queue from each circuit based 
    on the cost and profits (respectively) from each actor in the circuit.
    3. Create a state vector for each circuit, based on the power 
    distribution strategy.
    4. Concantenate the individual state vectors from each circuit to 
    represent the entire grid.
    5. Set any remaining unknown states to zero.

    Notes
    -----
    The power distribution strategy cannot account for non-independent 
    grid circuit, and will default to skipping the smallest dependent 
    circuit encountered. A set of dependent circuits are circuits that 
    each contain the same grid actor(s). In this case, the distribution 
    strategy will produce conflicting states for the shared actors, so 
    the default behavior is to take the most viable strategy (affecting 
    the most nodes) and neglecting the other circuits (setting them to 
    zero). This will effectively disconnect actors that are only 
    connected to a neglected circuit to prevent them from being set to a
    conflicting state.
    """
    supply_tuples, demand_tuples, states = [], [], {}
    for key, val in kwargs.items():
        if 'supply_tuple' in key.lower():
            supply_tuples.append(val)
        elif 'demand_tuple' in key.lower():
            demand_tuples.append(val)

    circuits = get_circuits(conn, names)
    circuits.sort(key=lambda c : sum([len(a) for a in c]), reverse=True)

    for suppliers, demanders in circuits:
        ind_suppliers = set(suppliers).difference(states.keys())
        ind_demanders = set(demanders).difference(states.keys())

        if len(ind_suppliers) != len(suppliers) or len(ind_demanders) != len(demanders):
            msg = 'Non-independent grid circuit encountered.'
            msg += 'Repeated actors may not be optimally considered by power distribution strategy.'
            msg += f'\n - Repeated actors: {[a for a in suppliers + demanders if a in states]}'
            logging.warning(msg)

        sts_filtered = [st for st in supply_tuples if st[0] in ind_suppliers]
        dts_filtered = [dt for dt in demand_tuples if dt[0] in ind_demanders]
        supply_queue = make_supply_queue(tol, *sts_filtered)
        demand_queue = make_demand_queue(tol, *dts_filtered)

        found_states = meet_circuit_demand(demand_queue, supply_queue, tol)
        if any([fs in states for fs in found_states]):
            msg = 'Non-independent grid circuit neglected: power distribution ' \
            'strategy may be faulty and some actors\' state set to 0.'
            msg += f'\n - Repeated actors: {[fs for fs in found_states if fs in states]}'
            msg += f'\n - Possibly lost actors: {[fs for fs in found_states if fs not in states]}'
            logging.warning(msg)
            continue
        states = states | found_states
    
    state_list = [states.get(name, 0.) for name in names]
    return state_list

def get_circuits(conn: list, names: list)->list:
    """Parses a connectivity matrix and returns a list of 2 list pairs 
    (tuples) representing the supplying and demanding actors in a 
    connected circuit.

    Actors that give power to another actor can form the supply list, 
    while actors that receive power from another actor go to demand list. 
    The method produces pairs such that every actor in the demand list 
    is capable of receiving energy from any actor in the supply list.
    """
    circuits, n = [], len(conn)
    conns = {src : {sink for sink in range(n) 
                    if can_send_to(src, sink, conn)} for src in range(n)}

    for src, sinks in conns.items():
        if len(sinks) == 0:
            continue
        for suppliers, demanders in circuits:
            if all([d in sinks for d in demanders]):
                suppliers.add(src)
        if sinks not in [c[1] for c in circuits]:
            circuits.append(({src}, sinks))

    circuits = [tuple([names[a] for a in s] for s in c) for c in circuits]

    return circuits

def can_send_to(src, sink, conn: list, visited: set=None):
    """Returns true if the source is able to send power to the sink. 
    ``conn`` is a list (or dict) of lists, where the keyword is an actor 
    and the value is a list of actors the key actor can send power to."""
    if visited is None:
        visited = set()

    labels = conn.keys() if conn is dict else range(len(conn))

    direct_sinks = {d_sink for d_sink in labels if conn[src][d_sink]}
    direct_sinks = direct_sinks.difference(visited)

    if sink in direct_sinks:
        return True
    else:
        visited.add(src)
        return any([can_send_to(new_src, sink, conn, visited) 
                    for new_src in direct_sinks])

def make_demand_queue(tol: float, *args, **kwargs):
    """Compiles the demand queue from the demand tuples, sorted by 
    benefit. Queue is compiled from tuples passed to *args or **kwargs 
    of the following form: ``(label, benefit, req_demand, max_demand)``

    *Note: Future versions may update the sorting scheme from a linear 
    sort based on maximum benefit (current version) to something that 
    considers the efficiency of the load.*
    """
    args = R.extend(args, kwargs)
    demand_queue = [val for val in args if all([
                        isinstance(val, tuple),
                        len(val) == 4,
                        val[1] > -tol,
                        val[2] > -tol])]
    demand_queue.sort(key=lambda a : a[1], reverse=True)
    return demand_queue

def make_supply_queue(tol: float, *args, **kwargs):
    """Compiles the supply queue from the supply tuples, sorted by cost. 
    Queue is compiled from tuples passed to *args or **kwargs of the 
    following form: ``(label, cost, supply)``
    """
    args = R.extend(args, kwargs)
    supply_queue = [val for val in args if all([
                        isinstance(val, tuple),
                        len(val) == 3,
                        val[1] != float('inf'),
                        val[2] > -tol])]
    supply_queue.sort(key=lambda a : a[1])

    return supply_queue

def meet_circuit_demand(demand_queue: list, supply_queue: list, tol: float):
    """Returns a dict of grid states derived from logic on how to 
    prioritize meeting the demands of the grid."""
    states = {}
    if len(demand_queue) == 0 or len(supply_queue) == 0:
        return {}
    
    states, s_idx, unused_s = meet_req_demands(demand_queue, supply_queue, states, tol)
    states = meet_max_demands(demand_queue, supply_queue, states, tol, unused_s, s_idx=s_idx)

    return states

def meet_req_demands(demand_q: list, supply_q: list, states: dict, tol: float, 
                     current_supply: float=None, s_idx: int=0, d_idx: int=0)-> tuple:
    """Balances the supplied power to strategically meet the provided 
    grid demands.

    Returns
    -------
    out : tuple
        A tuple containing the following values:

        - dict: A dictionary of assigned states following 
        ``{label:state}`` format.
        - int: Index of latest used supplying actor that still has power 
        that can be provided.
        - float: Amount of remaining power for the actor at the given 
        index.

    Process
    -------
    Takes the top element of the demand and supply queue and matches them
    against each other. If an actor's required demand cannot be met by 
    the grid, then the actor is dropped and the index resets to its 
    previous state. This proceeds until either all demands are met or 
    the supply is exhuasted.
    """
    s_label, cost, supply = supply_q[s_idx]
    d_label, benefit, req_d, _ = demand_q[d_idx]

    unused_s = supply if current_supply is None else current_supply
    unmet_d = req_d
    current_suppliers, keyframe_s_idx, keyframe_supply = {}, s_idx, unused_s
    
    try:
        while benefit >= cost:
            while (unused_s < tol or 
                   actor_is_receiving(s_label, states)):
                s_label, cost, supply = supply_q[s_idx := s_idx + 1]
                unused_s = supply

            while any((unmet_d < tol, d_label in states, 
                       d_label == s_label, 
                       actor_is_supplying(d_label, states))):
                d_label, benefit, req_d, _ = demand_q[d_idx := d_idx + 1]
                unmet_d = req_d
            
            unmet_d, unused_s = meet_actor_demand(unmet_d, unused_s)
            current_suppliers[s_label] = abs(supply - unused_s)
            if unmet_d < tol: 
                states[d_label] = -abs(req_d)
                states = states | current_suppliers
                current_suppliers, keyframe_s_idx, keyframe_supply = {}, s_idx, unused_s
    except: IndexError

    if len(current_suppliers) > 0 and d_idx < len(demand_q) - 1:
        states, s_idx, unused_s = meet_req_demands(demand_q, supply_q, states, 
                                  tol, d_idx=d_idx+1,
                                  s_idx=keyframe_s_idx, current_supply=keyframe_supply)
        
    return states, s_idx, unused_s

def meet_max_demands(demand_q: list, supply_q: list, states: dict, 
                     tol: float, current_supply: float=None, 
                     d_idx: int=0, s_idx: int=0)-> dict:
    """Iterates through the suppliers to meet the maximum amount of 
    maximum demands for the receiving actors.
    
    Returns
    -------
    out : dict
        The updated states in ``{name : state}`` format.
    """
    s_label, cost, supply = supply_q[s_idx]
    d_label, benefit, req_d, max_d = demand_q[d_idx]

    unused_s = supply if current_supply is None else current_supply
    unmet_d = max_d - req_d

    try:
        while True:
            while unused_s < tol or actor_is_receiving(s_label, states):
                s_label, cost, supply = supply_q[s_idx := s_idx + 1]
                unused_s = supply

            while any((unmet_d < tol, 
                       actor_is_supplying(d_label, states), 
                       d_label == s_label)):
                d_label, benefit, req_d, max_d = demand_q[d_idx := d_idx + 1]
                unmet_d = max_d - req_d

            if benefit < cost:
                break
            unmet_d, unused_s = meet_actor_demand(unmet_d, unused_s)
            states[s_label] = abs(supply - unused_s)
            states[d_label] = -abs(max_d - unmet_d)
    except: IndexError

    return states

def actor_is_supplying(label: str, grid_states: dict)-> bool:
    """Returns True if the given actor is listed as supplying power."""
    return grid_states.get(label, float('-inf')) > 0

def actor_is_receiving(label: str, grid_states: dict)-> bool:
    """Returns True if given actor is listed as receiving power."""
    return grid_states.get(label, float('inf')) < 0

def meet_actor_demand(demand: float, supply: float)-> tuple:
    """Matches the maximum amount of demand that can be met by the given
    supply."""
    diff = demand - supply
    demand_out = max(0., diff)
    supply_out = max(0., -diff)
    return demand_out, supply_out