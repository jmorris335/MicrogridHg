import constrainthg.relations as R
import random
import csv
import numpy as np

from microgrid_objects import *

#TODO: We shouldn't be passing information by node IDs, this should be implemented with tuples
KEY_SEP = '¦&¦' #A unique constant for seperating strings in paired keywordss

def generate_connectivity_keyword(OBJ_to, OBJ_from):
    """Generates a keyword for referencing the cell connecting OBJ_from to OBJ_to."""
    name_to, name_from = [str(OBJ) for OBJ in (OBJ_to, OBJ_from)]
    keyword = f'{name_to}{KEY_SEP}{name_from}'
    return keyword

def generate_building_keyword(building: GridObject, keyword: str):
    """Generates a keyword for referencing the value of the building."""
    key = f'{keyword}{KEY_SEP}{str(building)}'
    return key

## ----- Relationships ----- ##
### Simulation
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
    """Returns the number of leapyears that the simulation has covered (not counting the present year)."""
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
    """Converts the day and hour into a integer for the hour of the year (1-8784)"""
    max_h_i = hours_in_leapyear if is_leapyear else hours_in_year
    hour_idx = max(0, min(int(day * hours_in_day + hour), max_h_i))
    return hour_idx

def Rcalc_year_is_leapyear(year: int, **kwargs)-> bool:
    """Returns true if the year is a leapyear."""
    is_leapyear = year % 4 == 0
    return is_leapyear

### Data
def Rget_data_from_csv_file(filename: str, **kwargs):
    """Converts a CSV file to a list of dictionaries."""
    with open(filename, newline='') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data

def Rget_float_from_csv_data(csv_data: dict, row, col, **kwargs):
    """Returns the value in the row and column from the CSV dict reader."""
    value = float(csv_data[row][col])
    return value

def Rget_load_from_building_data(csv_data: dict, row, col, **kwargs):
    """Returns the value in the row and column from the CSV dict reader."""
    value = float(csv_data[row][col])
    value *= 1000 #convert from kW to W
    return value

## Microgrid
def Rsort_names(*args, **kwargs)->list:
    """Sorts the object names into a prefered list."""
    names = R.extend(args, kwargs)
    names.sort()
    return names

def Rdetermine_load(*args, **kwargs)->float:
    """Determines the amount of energy necessary to run the microgrid.
    
    Note output is always negative or zero, since loads are always negative."""
    demands = R.extend(args, kwargs)
    load = -sum([abs(d) for d in demands if d < 0.])
    return load

def Rdetermine_if_connected(is_failing: bool, is_load_shedding: bool, **kwargs)-> bool:
    """Determines whether or not the object is connected to the grid."""
    return not (is_failing or is_load_shedding)

def Rcalc_if_receiving_power(receives_from: bool, receiver_conn: bool, provider_conn: bool, **kwargs)-> bool:
    """Determines if the receiver object is receiving power from the provider object."""
    return receives_from and receiver_conn and provider_conn

def Rform_connectivity_matrix(names: list, key_sep: str, *args, **kwargs)-> np.ndarray:
    """Forms the connectivity (A) matrix where the ij-th cell indicates power is flowing from object j to object i."""
    A = np.zeros((len(names), len(names)))
    # args, kwargs = R.get_keyword_arguments(args, kwargs, KEYNAMES)
    for key, val in kwargs.items():
        if key_sep in key:
            i,j = [names.index(name) for name in key.split(key_sep)[:2]]
            A[i][j] = 1 if bool(val) else 0
    return A

def Rform_demand_matrix(**kwargs)-> np.ndarray:
    """Forms the demand (B) matrix where the i-th cell indicates the demand for object i."""
    names = kwargs.get('names')
    demands = {}
    for value in kwargs.values():
        if isinstance(value, tuple):
            name, demand = value
            demands[name] = demand
    B = [float(demands.get(name, 0.)) for name in names]
    return np.array(B)

def Rget_state_from_matrix(x: np.ndarray, name: str, names: list, **kwargs)-> float:
    """Indexes and returns the state of the object in the state matrix."""
    i = names.index(name)
    out = x[i]
    return out

def Rlinear_solve(A: np.ndarray, B: np.ndarray, **kwargs)-> np.ndarray:
    """Solves the system of equations Ax = B for x."""
    x = np.linalg.solve(A, B)
    return x

def Rdetermine_load_shedding(names: list, balance: float, key_sep: str, **kwargs)-> list:
    """Returns a list of buildings that are being load shed.
    
    Parameters
    ----------
    - `balance` : float
        the total system balance
    - `load` & OBJ : str (split by `key_sep`)
        load of the object 
    - `priority` & OBJ : str (split by `key_sep`)
        priority rating of the object
    - `key_sep` : str for splitting `load` and `priority`
    """
    keyed_args = {}
    for key, val in kwargs.items():
        var, OBJ = key.split(key_sep)[:2]
        if OBJ not in names: continue
        if OBJ not in keyed_args:
            keyed_args[OBJ] = {}
        keyed_args[OBJ].update({var: val})

    vals = [(OBJ, keyed_args[OBJ]['load'], keyed_args[OBJ]['priority']) for OBJ in keyed_args]
    vals.sort(key=lambda a : a[-1])

    to_shed = []
    while balance < 0 and len(vals) > 0:
        name, load, priority = vals.pop(0)
        to_shed.append(name)
        balance += abs(load)
    
    return to_shed

def Vload_nodes_are_level(key_sep: str, **kwargs)-> bool:
    """Returns true if all the indices for the load nodes are the same."""
    load_node_indices = {kwargs[kw] for kw in kwargs if kw.split(key_sep)[0] == 'index'}
    return len(load_node_indices) == 1

## Utility Grid
def Rcalc_ug_demand(conn: bool, islanded_balance: float, *args, **kwargs)-> float:
    """Calculates the demand of the utility grid based off of current balance."""
    if not conn or islanded_balance > 0.:
        return 0.
    return abs(islanded_balance)

## Solar
def Rget_solar_filename(year: str, **kwargs)-> str:
    """Returns the name of the CSV file with the solar data corresponding to the given year."""
    out = 'solar_data/724915'
    if year == 0 or str(year).upper() == 'TY':
        out += 'TY'
    else:
        out += f'_{year}_solar'
    out += '.csv'
    return out

def Rcalc_solar_demand(conn: bool, area: float, efficiency: float, sunlight: float, **kwargs)-> float:
    """Calculates the power (in W) produced by a photovoltaic cell for one hour."""
    if not conn:
        return 0.0
    power = max(0, area * efficiency * sunlight / 1000)
    return power

## Buildings
def Rget_building_filename(building_type: BUILDING_TYPE, **kwargs)-> str:
    """Returns the name of the CSV file with the load data corresponding to the building type."""
    out = f'building_data/RefBldg{building_type.value}New2004_7-1_5-0_3C_USA_CA_SAN_FRANCISCO.csv'
    return out

def Rcalc_critical_load(lights: float, equipment: float, **kwargs)-> float:
    """Calculates the critical load for a building based on its light and equipment usage."""
    cl = 0.5 * lights + 0.67 * equipment
    return cl

def Rdetermine_building_load(conn: bool, normal: float, critical: float, island: bool, **kwargs)-> float:
    """Determines the load of a building."""
    if not conn:
        return 0.0
    load = critical if island else normal
    load = -load
    return load

## Generators
def Rcalc_generator_demand(is_islanded: bool, load: float, max_out: float, out_of_fuel: bool, conn: bool, **kwargs)-> float:
    """Calculates how much power the generator is capable of supplying."""
    if any([not conn, not is_islanded, out_of_fuel]):
        return 0.
    return max(0., min(abs(load), max_out))

def Rcalc_next_time_for_refueling(refuel_time: int, curr_hour: int, prob: float, hours_in_day: int, **kwargs):
    """Calculates the next time for refueling based on the current time."""
    if refuel_time > curr_hour:
        return refuel_time
    days_until_refuel = 0
    while prob < random.random(): 
        days_until_refuel += 1
    hours_until_refuel = random.randint(0, hours_in_day-1)
    next_time = refuel_time + days_until_refuel * hours_in_day + hours_until_refuel
    return next_time

def Rcalc_generator_fuel_level(refuel_time: int, curr_hour: int, curr_level: float, max_level: float, **kwargs)-> float:
    """Determines the fuel level of the generator."""
    if refuel_time > curr_hour:
        return curr_level
    return max_level

## Batteries
def Rcalc_battery_demand(is_charging: bool, load: float, level: float, capacity: float, max_rate: float, 
                         max_output: float, trickle_prop: float, **kwargs)-> float:
    """Calculates the demand of the battery."""
    if load < 0:
        highest_output = min(max_output, level)
        demand = max(0, min(abs(load), highest_output))
    elif is_charging:
        if level < 0.8 * capacity:
            demand = trickle_prop * max_rate
        else:
            demand = max_rate
    else:
        demand = 0
    return demand

def Rdetermine_battery_is_charging(island: bool, load: float, level: float, capacity: float, all_loads_shed: bool, **kwargs)-> bool:
    """Determines if the battery should be charging or not."""
    if not island or load < 0 or all_loads_shed:
        return False
    return level < capacity

def Rcalc_battery_charge_level(state: float, level: float, max_level: float, eff: float, **kwargs)-> float:
    """Calculates the charge level of the battery based on power flow (W)."""
    expected_level = level + (eff * state)
    new_level = max(0, min(expected_level, max_level))
    return new_level