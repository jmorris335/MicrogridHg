from constrainthg import Node, Hypergraph
import constrainthg.relations as R
import numpy as np
import random
import csv

from microgrid_objects import *

random.seed(3)

KEY_SEP = '¦&¦' #A unique constant for seperating strings in paired keywordss
DAYS_IN_YEAR = 365
DAYS_IN_LEAPYEAR = 366
HOURS_IN_DAY = 24
HOURS_IN_YEAR = DAYS_IN_YEAR * HOURS_IN_DAY
HOURS_IN_LEAPYEAR = DAYS_IN_LEAPYEAR * HOURS_IN_DAY

mg = Hypergraph()

## ----- Objects ----- ##
### Initialize Objects
UGs = [GridObject('UtilityGrid')]
BUSs = [
    GridObject('Bus1', demand=0),
    GridObject('Bus2', demand=0),
]
PVs = [
    PhotovoltaicArray('PV1', area=10000, efficiency=.18)
]
GENs = [
    Generator('Generator1', fuel_capacity=2500., starting_fuel_level=2500., max_output=300., efficiency=0.769), 
    Generator('Generator2', fuel_capacity=2500., starting_fuel_level=2500., max_output=300., efficiency=0.769), 
]
BATTERYs = [
    Battery('Battery1', charge_capacity=10000., charge_level=10000., max_output=1000., efficiency=0.9747, max_charge_rate=2000.),
]
BUILDINGs = [
    Building('Building1Small', BUILDING_TYPE.SMALL, priority=10),
    Building('Building2Small', BUILDING_TYPE.SMALL, priority=15),
    Building('Building3Medium', BUILDING_TYPE.MEDIUM, priority=61),
    Building('Building4Large', BUILDING_TYPE.LARGE, priority=93),
    Building('Building5Warehouse', BUILDING_TYPE.WAREHOUSE, priority=74),
]
OBJECTS = GENs + BATTERYs + UGs + BUSs + PVs + BUILDINGs
def get_names_of_objects(objects: list):
    return [str(o) for o in objects]

NAMES = get_names_of_objects(OBJECTS)

### Connectivity
#### Receivers (set which objects are wired to receive power from which other objects)
for OBJ in OBJECTS: #Set default as not connected
    for SRC in OBJECTS:
        OBJ.add_source(SRC, SRC is OBJ)

for SRC in list(BUSs + UGs + GENs):
    BUSs[0].add_source(SRC, True)
for SRC in list(BUSs + BATTERYs + PVs):
    BUSs[1].add_source(SRC, True)
BUILDINGs[0].add_source(BUSs[0], True)
BUILDINGs[1].add_source(BUSs[1], True)
BUILDINGs[2].add_source(BUSs[1], True)
BUILDINGs[3].add_source(BUSs[0], True)
BUILDINGs[4].add_source(BUSs[0], True)
BATTERYs[0].add_source(BUSs[1], True)

def generate_connectivity_keyword(OBJ_to, OBJ_from):
    """Generates a keyword for referencing the cell connecting OBJ_from to OBJ_to."""
    name_to, name_from = [str(OBJ) for OBJ in (OBJ_to, OBJ_from)]
    keyword = f'{name_to}{KEY_SEP}{name_from}'
    return keyword
KEYNAMES = [generate_connectivity_keyword(o1, o2) for o1 in OBJECTS for o2 in OBJECTS]

def generate_building_keyword(building: GridObject, keyword: str):
    """Generates a keyword for referencing the value of the building."""
    key = f'{keyword}{KEY_SEP}{str(building)}'
    return key

#### Active receivers (initialize nodes for objects actively receiving power from other objects)
for OBJ in OBJECTS:
    for SRC in OBJECTS:
        OBJ.add_active_source(SRC, None)


## ----- Nodes ----- ##
### Setup Conditions
mg_mode = Node('microgrid mode', MICROGRID_MODE.GRID_CONNECTED, description='mode of microgrid (Enum)')
has_random_failure = Node('has_random_failure', False, description='true if random failure is allowed')
is_islanded = Node('is islanded', description='true if the utiliy grid is disconnected')
sim_length = Node('sim_length', description='num days to simulate')
sim_length_hours = Node('sim_length_hours', description='num hours to simulate')
use_random_date = Node('use_random_date', True, description='true if the start date is set randomly')
num_mc_iterations = Node('num_mc_iterations', 1000, description='number of Monte Carlo iterations')
min_year = Node('min year', 2000, description='minimum year of simulation data')
max_year = Node('max year', 2009, description='maximum year of simulation data')
prob_daily_refueling = Node('prob of daily refueling', 0.25, description='probability that the generators receive new fuel every day')

### Grid
conn_matrix = Node('connectivity matrix', description='cell ij indicates object[i] receives power from object[j]')
demand_matrix = Node('demand matrix', description='desired state for each object on the grid')
state_matrix = Node('state matrix', description='state from each object on the grid')
total_power_balance = Node('total power supplied', 0., description='total balance of power supplied (+) or demanded (-) by grid (W)')
power_wasted = Node('power wasted', 0., description='cumulative power supplied to grid in excess of current demand (W)')
list_load_shedding = Node('list of load shedding', description='a list of objects whose loads are removed from the grid')
all_loads_shed = Node('all loads shed', description='true if all loads in the graph have been shed (Bool)')
num_loads = Node('num loads', description='number of loads (buildings) on grid')

### Simulation
elapsed_hours = Node('elapsed hour', 0, description='number of hours that have passed during the simulation.')
start_year = Node('start year', description='starting year for the simulation')
start_day = Node('start day', description='starting day for the simulation (1-366)')
start_hour = Node('start hour', 1, description='starting hour for the simulation (1-24)')
year = Node('year', description='current year')
day = Node('day', description='current day of the year (1-366)')
hour = Node('hour', description='current hour (0-23)')
hour_idx = Node('hour index', description='current hour of the year (1-8784)')
num_leapyears = Node('num leapyears', description='number of leapyears encountered during the simulation')
max_hour_index = Node('max_hour_index', description='maximum hour index for the year')
is_leapyear = Node('is leapyear', description='true if the current year is a leapyear')
tol = Node('tolerance', 0.5, description='float tolerance to be ignored')

### Components
sunlight = Node('sunlight', description='energy from sun for a specific hour (W-hr/m^2)')
sunlight_data = Node('sunlight_data', description='dict of yearly sunlight values by hour')
sunlight_filename = Node('sunlight_filename', description='filename for sunlight csv file')
sunlight_data_label = Node('sunlight_data_label', 'SUNY Dir (Wh/m^2)', description='name of column for sunlight data')
load_filename = Node('load filename', description='filename for load information')
batt_trickle = Node('battery trickle charge rate prop', 0.25, description='proportion of maximum charging rate to reduce batteries to after 80% charged')
next_refuel_hour = Node('next refuel hour', 0, description='next hour generators will be refueled')

### Outputs
output_filename = Node('output filename', 'output.txt', description='name of output file')
failing_objects = Node('failing_objects', description='list of failing components')


## ----- Relationships ----- ##
### Simulation
def Rget_random_year(min_year: int, max_year: int, **kwargs):
    """Returns a random year from the maximum range."""
    rand_year = random.randint(int(min_year), int(max_year))
    return rand_year

def Rget_random_day(**kwargs)-> int:
    """Returns a random int for a day (1-366)."""
    rand_day = random.randint(1, DAYS_IN_YEAR)
    return rand_day

def Rget_random_hour(**kwargs)-> int:
    """Returns a random int for an hour (0-23)."""
    rand_hour = random.randint(0, HOURS_IN_DAY-1)
    return rand_hour

def Rcalc_elapsed_time(elapsed_hours: int, **kwargs)-> int:
    """Iterates the elapsed time by one hour."""
    elapsed_hours += 1
    return elapsed_hours

def Rcalc_year(elapsed_hours: int, num_leapyears: int, start_year: int, 
               start_day: int, start_hour: int, **kwargs)-> int:
    """Calculates the current year of the simulation."""
    elapsed_hours += ((start_day - 1) * HOURS_IN_DAY + start_hour)
    elapsed_hours -= HOURS_IN_DAY * num_leapyears
    year = start_year + elapsed_hours // HOURS_IN_YEAR
    return year

def Rcalc_day(elapsed_hours: int, start_year: int, year: int, num_leapyears: int,
              start_day: int, start_hour: int, **kwargs)-> int:
    """Calculates the current day of the simulation."""
    elapsed_years = year - start_year
    elapsed_hours -= HOURS_IN_YEAR * elapsed_years
    elapsed_hours -= (HOURS_IN_DAY * num_leapyears)
    elapsed_hours += start_hour
    day =  start_day + elapsed_hours // HOURS_IN_DAY
    return day

def Rcalc_hour(elapsed_hours: int, **kwargs)-> int:
    """Calculates the current day of the simulation."""
    hour = elapsed_hours % HOURS_IN_DAY
    return hour

def Rcalc_num_leapyears(start_year: int, elapsed_hours: int, **kwargs)-> int:
    """Returns the number of leapyears that the simulation has covered (not counting the present year)."""
    num_leapyears = 0
    year = start_year
    while elapsed_hours > 0:
        year += 1
        is_leapyear = year % 4 == 0
        num_leapyears += is_leapyear
        elapsed_hours -= HOURS_IN_LEAPYEAR if is_leapyear else HOURS_IN_YEAR
    return num_leapyears

def Rget_hour_index(day: int, hour: int, is_leapyear: bool, **kwargs):
    """Converts the day and hour into a integer for the hour of the year (1-8784)"""
    max_h_i = HOURS_IN_LEAPYEAR if is_leapyear else HOURS_IN_YEAR
    hour_idx = max(0, min(int(day * HOURS_IN_DAY + hour), max_h_i))
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

## Microgrid
def Rdetermine_if_connected(is_failing: bool, is_load_shedding: bool, **kwargs)-> bool:
    """Determines whether or not the object is connected to the grid."""
    return not (is_failing or is_load_shedding)

def Rcalc_if_receiving_power(receives_from: bool, receiver_conn: bool, provider_conn: bool, **kwargs)-> bool:
    """Determines if the receiver object is receiving power from the provider object."""
    return receives_from and receiver_conn and provider_conn

def Rform_connectivity_matrix(*args, **kwargs)-> np.ndarray:
    """Forms the connectivity (A) matrix where the ij-th cell indicates power is flowing from object j to object i."""
    A = np.zeros((len(OBJECTS), len(OBJECTS)))
    args, kwargs = R.get_keyword_arguments(args, kwargs, KEYNAMES)
    for key, val in kwargs.items():
        if key in KEYNAMES:
            object_names = key.split(KEY_SEP)[:2]
            i,j = [NAMES.index(name) for name in object_names]
            A[i][j] = 1 if bool(val) else 0
    return A

def Rform_demand_matrix(**kwargs)-> np.ndarray:
    """Forms the demand (B) matrix where the i-th cell indicates the demand for object i."""
    B = [float(kwargs[name]) if name in kwargs else 0. for name in NAMES]
    return np.array(B)

def Rget_state_from_matrix(x: np.ndarray, name: str, **kwargs)-> float:
    """Indexes and returns the state of the object in the state matrix."""
    i = NAMES.index(name)
    out = x[i]
    return out

def Rlinear_solve(A: np.ndarray, B: np.ndarray, **kwargs)-> np.ndarray:
    """Solves the system of equations Ax = B for x."""
    x = np.linalg.solve(A, B)
    return x

def Rdetermine_load_shedding(balance: float, **kwargs)-> list:
    """Returns a list of buildings that are being load shed.
    
    Parameters
    ----------
    - `balance` : float
        the total system balance
    - `load` & OBJ : str (split by KEY_SEP)
        load of the object 
    - `priority` & OBJ : str (split by KEY_SEP)
        priority rating of the object
    """
    keyed_args = {}
    for key, val in kwargs.items():
        var, OBJ = key.split(KEY_SEP)[:2]
        if OBJ not in NAMES: continue
        if OBJ not in keyed_args:
            keyed_args[OBJ] = {}
        keyed_args[OBJ].update({var: val})

    vals = [(OBJ, keyed_args[OBJ]['load'], keyed_args[OBJ]['priority']) for OBJ in keyed_args]
    vals.sort(key=lambda a : a[-1])

    to_shed = []
    while balance < 0 and len(vals) > 0:
        name, load, priority = vals.pop(0)
        to_shed.append(name)
        balance += load
    
    return to_shed

def Vload_nodes_are_level(**kwargs)-> bool:
    '''Returns true if all the indices for the load nodes are the same.'''
    load_node_indices = {kwargs[kw] for kw in kwargs if kw.split(KEY_SEP)[0] == 'index'}
    return len(load_node_indices) == 1

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
    power = min(0, area * efficiency * sunlight / -1000)
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
    return critical if island else normal

## Generators
def Rcalc_generator_demand(demand: float, max_out: float, out_of_fuel: bool, conn: bool, **kwargs)-> float:
    """Calculates how much power the generator is capable of supplying."""
    if not conn or out_of_fuel:
        return 0.
    return max(0., min(demand, max_out))

def Rcalc_next_time_for_refueling(refuel_time: int, curr_hour: int, prob: float, **kwargs):
    """Calculates the next time for refueling based on the current time."""
    if refuel_time > curr_hour:
        return refuel_time
    days_until_refuel = 0
    while prob < random.random(): 
        days_until_refuel += 1
    hours_until_refuel = random.randint(0, HOURS_IN_DAY-1)
    next_time = refuel_time + days_until_refuel * HOURS_IN_DAY + hours_until_refuel
    return next_time

def Rcalc_generator_fuel_level(refuel_time: int, curr_hour: int, curr_level: float, max_level: float, **kwargs)-> float:
    """Determines the fuel level of the generator."""
    if refuel_time > curr_hour:
        return curr_level
    return max_level

## Batteries
def Rcalc_battery_demand(is_charging: bool, grid_balance: float, level: float, capacity: float, max_rate: float, 
                         max_output: float, trickle_prop: float, **kwargs)-> float:
    """Calculates the demand of the battery."""
    if grid_balance < 0:
        highest_output = min(max_output, level)
        demand = max(0, min(grid_balance, highest_output))
    elif is_charging:
        if level < 0.8 * capacity:
            demand = trickle_prop * max_rate
        else:
            demand = max_rate
    else:
        demand = 0
    return demand

def Rdetermine_battery_is_charging(island: bool, balance: float, level: float, capacity: float, all_loads_shed: bool, **kwargs)-> bool:
    """Determines if the battery should be charging or not."""
    if island or balance < 0 or all_loads_shed:
        return False
    return level < capacity

def Rcalc_battery_charge_level(state: float, level: float, max_level: float, eff: float, **kwargs)-> float:
    """Calculates the charge level of the battery based on power flow (W)."""
    expected_level = level + (eff * state)
    new_level = max(0, min(expected_level, max_level))
    return new_level


## ----- Edges ----- ##
### Simulation
mg.add_edge(sim_length, sim_length_hours, lambda sim_length, **kw : sim_length * HOURS_IN_DAY)
# mg.add_edge(sim_length_hours, sim_length, lambda sim_length_hours, **kw : sim_length_hours / HOURS_IN_DAY)
mg.add_edge({'use_rand_date': use_random_date, 'min_year': min_year, 'max_year': max_year}, start_year, 
            Rget_random_year, via=lambda use_rand_date, **kwargs : use_rand_date)
mg.add_edge(use_random_date, start_day, Rget_random_day, via=lambda s1, **kwargs : s1 is True)
mg.add_edge(use_random_date, start_hour, Rget_random_hour, via=lambda s1, **kwargs : s1)
mg.add_edge({'start_year': start_year, 'elapsed_hours': elapsed_hours}, num_leapyears, Rcalc_num_leapyears)
mg.add_edge({'elapsed_hours': elapsed_hours, 'sim_length_hours': sim_length_hours}, 
            elapsed_hours, Rcalc_elapsed_time, index_offset=1,
            via=lambda elapsed_hours, sim_length_hours : elapsed_hours < sim_length_hours)
mg.add_edge({'elapsed_hours': elapsed_hours, 'start_year': start_year, 'num_leapyears': num_leapyears,
             'start_day': start_day, 'start_hour': start_hour}, year, Rcalc_year,
             disposable=['elapsed_hours', 'num_leapy3ears'],
             index_via=lambda elapsed_hours, num_leapyears, **kw : R.Rsame(elapsed_hours, num_leapyears))
mg.add_edge({'elapsed_hours': elapsed_hours, 'start_year': start_year, 'year': year, 'num_leapyears': num_leapyears,
             'start_day': start_day, 'start_hour': start_hour}, day, Rcalc_day, 
             disposable=['elapsed_hours', 'year', 'num_leapyears'],
             index_via=lambda elapsed_hours, year, **kw : R.Rsame(elapsed_hours, year))
mg.add_edge(elapsed_hours, hour, Rcalc_hour)
mg.add_edge({'day': day, 'hour': hour, 'is_leapyear': is_leapyear}, hour_idx, Rget_hour_index,
            edge_props='DISPOSE_ALL',
            index_via=lambda day, hour, is_leapyear, **kw : R.Rsame(day, hour, is_leapyear))
mg.add_edge(year, is_leapyear, Rcalc_year_is_leapyear)

### Grid
mg.add_edge({'A': conn_matrix, 'B': demand_matrix}, state_matrix, Rlinear_solve, 
            label='solve state matrix', edge_props=['LEVEL', 'DISPOSE_ALL'])
mg.add_edge(state_matrix, total_power_balance, lambda s1, **kwargs : sum(s1), index_offset=1)
mg.add_edge({'wasted': power_wasted, 'balance': total_power_balance}, power_wasted, 
            lambda wasted, balance, **kwargs : wasted + min(0., balance), index_offset=1, edge_props=['LEVEL', 'DISPOSE_ALL'])
mg.add_edge([B.name for B in BUILDINGs], num_loads, lambda *args, **kwargs : len(R.extend(args, kwargs)))

mg.add_edge({'l': list_load_shedding, 'num': num_loads}, all_loads_shed, lambda l, num, **kwargs : len(l) >= num)

### Objects
keyed_receiving_nodes = {}
for OBJ in OBJECTS:
    #### Power Flow
    mg.add_edge({'state': OBJ.state, 'demand': OBJ.demand}, OBJ.is_overloaded, 
                lambda state, demand, **kwargs :demand > state, edge_props=['LEVEL', 'DISPOSE_ALL'])
    # mg.add_edge(OBJ.is_connected, OBJ.demand, lambda **kwargs : 0., via=lambda s1, **kwargs : s1 is False)
    mg.add_edge(OBJ.is_connected, OBJ.state, lambda **kwargs : 0., via=lambda s1, **kwargs : s1 is False)
    mg.add_edge({'x': state_matrix, 'name': OBJ.name}, OBJ.state, Rget_state_from_matrix, label=f'retrieve state of {str(OBJ)}', index_offset=1)
    for SRC in OBJECTS:
        if SRC is OBJ:
            mg.add_edge({'receives_from': OBJ.receives_from[str(SRC)], 'is_conn': OBJ.is_connected}, 
                        OBJ.receiving_from[str(SRC)], label=f'{str(OBJ)} receiving from itself',
                        rel=lambda receives_from, is_conn, **kwargs : receives_from and is_conn,
                        disposable=['is_conn'])
        else:
            mg.add_edge({'receives_from': OBJ.receives_from[str(SRC)], 'receiver_conn': OBJ.is_connected, 
                         'provider_conn': SRC.is_connected}, OBJ.receiving_from[str(SRC)], 
                        label=f'{str(OBJ)} receiving from {str(SRC)}',
                        rel=Rcalc_if_receiving_power, disposable=['receiver_conn', 'provider_conn'],
                        index_via=lambda receiver_conn, provider_conn, **kw : R.Rsame(receiver_conn, provider_conn))
        keyed_receiving_nodes.update({generate_connectivity_keyword(OBJ, SRC) : OBJ.receiving_from[str(SRC)]})

    #### Failures and Load Shedding
    mg.add_edge({'is_failing': OBJ.is_failing, 'random_fail': has_random_failure, 'p': OBJ.prob_failing}, 
                OBJ.is_failing, lambda p, **kwargs : p > random.random(), index_offset=1,
                via=lambda random_fail, is_failing, **kwargs : random_fail is True and is_failing is False)
    mg.add_edge({'is_failing': OBJ.is_failing, 'p': OBJ.prob_fixed}, OBJ.is_failing, 
                lambda p, **kwargs : not (p > random.random()), index_offset=1,
                via=lambda is_failing, **kwargs : is_failing is True)
    #TODO: Need a way to specify failures of connectivity (like BUS1/BUS2 line)
    mg.add_edge({'shedding_list': list_load_shedding, 'name': OBJ.name}, OBJ.is_load_shedding, 
                lambda shedding_list, name, **kwargs :name in shedding_list)
    mg.add_edge({'is_failing': OBJ.is_failing, 'is_load_shedding': OBJ.is_load_shedding}, 
                OBJ.is_connected, Rdetermine_if_connected)

mg.add_edge(keyed_receiving_nodes, conn_matrix, Rform_connectivity_matrix, label='form connectivity matrix', 
            edge_props=['LEVEL', 'DISPOSE_ALL'])
OBJS_WO_BUSs = set(NAMES) - set(get_names_of_objects(BUSs))
mg.add_edge({name : demand for name, demand in zip(NAMES, [OBJ.demand for OBJ in OBJECTS])}, demand_matrix, 
            Rform_demand_matrix, label='form demand matrix',
            disposable=list(set(NAMES) - set(get_names_of_objects(BUSs))),
            index_via=lambda **kwargs : R.Rsame(**{key:kwargs[key] for key in OBJS_WO_BUSs}))

### Utility Grids
for UG in UGs:
    mg.add_edge({'conn': UG.is_connected, 'balance': total_power_balance}, UG.demand, 
                lambda conn, balance, **kw : balance if conn else 0., edge_props='LEVEL')
mg.add_edge(*[UG.is_connected for UG in UGs], is_islanded, lambda *args, **kwargs :not any(R.extend(args, kwargs)))

### Solar
mg.add_edge(year, sunlight_filename, Rget_solar_filename)
mg.add_edge(sunlight_filename, sunlight_data, Rget_data_from_csv_file)
mg.add_edge({'csv_data': sunlight_data, 'row': hour_idx, 'col': sunlight_data_label}, sunlight, Rget_float_from_csv_data,
            index_via=lambda csv_data, row, **kw: R.Rsame(csv_data, row), disposable=['csv_data', 'row'])
for PV in PVs:
    mg.add_edge({'conn': PV.is_connected,'area': PV.area, 'efficiency': PV.efficiency, 'sunlight': sunlight}, 
                PV.demand, Rcalc_solar_demand, disposable=['sunlight', 'conn'],
                index_via=lambda conn, sunlight, **kw : R.Rsame(conn, sunlight))

### Buildings
shedding_nodes = {'balance': total_power_balance, generate_building_keyword('balance', 'index') : ('balance', 'index')}
for B in BUILDINGs:
    mg.add_edge(B.type, B.building_filename, Rget_building_filename)
    mg.add_edge(B.building_filename, B.load_data, Rget_data_from_csv_file)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.normal_col_name}, 
                B.normal_load, Rget_float_from_csv_data)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.lights_col_name}, 
                B.lights_load, Rget_float_from_csv_data)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.equipment_col_name}, 
                B.equipment_load, Rget_float_from_csv_data)
    mg.add_edge({'lights': B.lights_load, 'equipment': B.equipment_load}, 
                B.critical_load, Rcalc_critical_load, edge_props=['LEVEL', 'DISPOSE_ALL'])
    #TODO: Need a way to tell if a building is connected to the Utility Grid for bus failures that should induce critical loads
    mg.add_edge({'conn': B.is_connected, 'normal': B.normal_load, 'critical': B.critical_load, 'island': is_islanded}, 
                B.demand, Rdetermine_building_load, edge_props=['LEVEL', 'DISPOSE_ALL'], label='calc building demand')
    state_label, priority_label, index_label = [generate_building_keyword(B, s) for s in ['load', 'priority', 'index']]
    shedding_nodes[state_label] = B.state
    shedding_nodes[priority_label] = B.priority
    shedding_nodes[index_label] = (state_label, 'index')
mg.add_edge(shedding_nodes, list_load_shedding, Rdetermine_load_shedding, via=Vload_nodes_are_level, 
            disposable=[generate_building_keyword(B, 'load') for B in BUILDINGs] + ['balance'])

### Generators
mg.add_edge({'refuel_time': next_refuel_hour, 'curr_hour': hour_idx, 'prob': prob_daily_refueling}, 
            next_refuel_hour, Rcalc_next_time_for_refueling, index_offset=1,
            disposable=['refuel_time', 'curr_hour'],
            index_via=lambda refuel_time, curr_hour, **kw : R.Rsame(refuel_time, curr_hour))
for G in GENs:
    mg.add_edge({'fl': G.fuel_level, 'tol': tol}, G.out_of_fuel, lambda fl, tol, **kwargs :abs(fl) < tol)
    mg.add_edge({'demand': G.demand, 'max_out': G.max_output, 'conn': G.is_connected, 'out_of_fuel': G.out_of_fuel}, 
                G.demand, Rcalc_generator_demand, index_offset=1, label=f'calc demand for {G}',
                disposable=['demand', 'conn', 'out_of_fuel'],
                index_via=lambda demand, conn, out_of_fuel, **kw : R.Rsame(demand, conn, out_of_fuel))
    mg.add_edge({'init': G.starting_fuel_level, 'max': G.fuel_capacity}, G.fuel_level, R.Rmin)
    mg.add_edge({'refuel_time': next_refuel_hour, 'curr_hour': hour_idx, 'curr_level': G.fuel_level,
                 'max_level': G.fuel_capacity}, G.fuel_level, Rcalc_generator_fuel_level, 
                disposable=['refuel_time', 'curr_hour', 'curr_level'], index_offset=1,
                index_via=lambda refuel_time, curr_hour, curr_level, **kw : R.Rsame(refuel_time, curr_hour, curr_level))

### Batteries
for B in BATTERYs:
    mg.add_edge({'island': is_islanded, 'balance': total_power_balance, 'all_loads_shed': all_loads_shed,
                 'level': B.charge_level, 'capacity': B.charge_capacity}, 
                B.is_charging, Rdetermine_battery_is_charging, label='determine if battery is charging',
                disposable=['island', 'balance', 'all_loads_shed'],
                index_via=lambda island, balance, level, all_loads_shed, **kw : 
                    R.Rsame(island, balance, level, all_loads_shed-1))
    mg.add_edge({'is_charging': B.is_charging, 'grid_balance': total_power_balance, 'level':B.charge_level, 
                 'capacity': B.charge_capacity, 'max_rate': B.max_charge_rate, 'max_output': B.max_output, 
                 'trickle_prop': batt_trickle}, 
                B.demand, Rcalc_battery_demand, label='calc battery demand',
                disposable=['level', 'is_charging', 'balance'],
                index_via=lambda is_charging, grid_balance, level, **kw : R.Rsame(is_charging-1, grid_balance, level))
    mg.add_edge({'state': B.state, 'level': B.charge_level, 'max_level': B.charge_capacity, 'eff': B.efficiency}, 
                B.charge_level, Rcalc_battery_charge_level, label='calc battery charge level',
                index_via=lambda state, level, **kw: R.Rsame(state-1, level))
