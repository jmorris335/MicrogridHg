from constrainthg import Node, Hypergraph
import constrainthg.relations as R
import random

from microgrid_objects import *
from microgrid_relations import *

#TODO: Singular matrices coming if source is not sufficient, need to have error 
#   handling for when the grid collapses (set the state to 0 basically)

random.seed(3)

mg = Hypergraph(no_weights=True)

## ----- Objects ----- ##
### Initialize Objects
UG = GridObject('UtilityGrid', is_load_shedding=False)
BUSs = [
    GridObject('Bus1'),
    GridObject('Bus2'),
]
PVs = [
    PhotovoltaicArray('PV1', area=10000, efficiency=.18)
]
GENs = [
    Generator('Generator1', fuel_capacity=2500., starting_fuel_level=2500., 
              max_output=30000., efficiency=0.769), 
    Generator('Generator2', fuel_capacity=2500., starting_fuel_level=2500., 
              max_output=30000., efficiency=0.769), 
]
BATTERYs = [
    Battery('Battery1', charge_capacity=10000., charge_level=10000., 
            max_output=100000., efficiency=0.9747, max_charge_rate=2000.),
]
BUILDINGs = [
    Building('Building1Small', BUILDING_TYPE.SMALL, priority=10),
    Building('Building2Small', BUILDING_TYPE.SMALL, priority=15),
    Building('Building3Medium', BUILDING_TYPE.MEDIUM, priority=61),
    Building('Building4Large', BUILDING_TYPE.LARGE, priority=93),
    Building('Building5Warehouse', BUILDING_TYPE.WAREHOUSE, priority=74),
]
OBJECTS = GENs + BATTERYs + [UG] + BUSs + PVs + BUILDINGs

### Connectivity
#### Receivers (set which objects are wired to receive power from which other objects)
for OBJ in OBJECTS: #Set default as not connected
    for SRC in OBJECTS:
        OBJ.add_source(SRC, SRC is OBJ)

for SRC in list(BUSs + GENs):
    BUSs[0].add_source(SRC, True)
for SRC in list(BUSs + BATTERYs + PVs):
    BUSs[1].add_source(SRC, True)
BUILDINGs[0].add_source(BUSs[0], True)
BUILDINGs[1].add_source(BUSs[1], True)
BUILDINGs[2].add_source(BUSs[1], True)
BUILDINGs[3].add_source(BUSs[0], True)
BUILDINGs[4].add_source(BUSs[0], True)
BATTERYs[0].add_source(BUSs[1], True)

#### Active receivers (initialize nodes for objects actively receiving power from other objects)
for OBJ in OBJECTS:
    for SRC in OBJECTS:
        OBJ.add_active_source(SRC, None)


## ----- Nodes ----- ##
### Constants
key_sep = Node('key_sep', KEY_SEP, 
    description='A unique constant for seperating strings in paired keywords')
days_in_year = Node('days_in_year', 365, description='number of days in a year')
days_in_leapyear = Node('days_in_leapyear', description='number of days in a leapyear')
hours_in_day = Node('hours_in_day', 24, description='number of hours in a day')
hours_in_year = Node('hours_in_year', description='number of hours in a year')
hours_in_leapyear = Node('hours_in_leapyear', description='number of hours in a leapyear')

### Setup Conditions
island_mode = Node('island_mode', 
    description='true if the utility grid is to be treated as disconnected')
has_random_failure = Node('has_random_failure', False, 
    description='true if random failure is allowed')
use_random_date = Node('use_random_date', True, 
    description='true if the start date is set randomly')
# num_mc_iterations = Node('num_mc_iterations', 1000, description='number of Monte Carlo iterations')
min_year = Node('min year', 2000, description='minimum year of simulation data')
max_year = Node('max year', 2009, description='maximum year of simulation data')
prob_daily_refueling = Node('prob of daily refueling', 0.25, 
    description='probability that the generators receive new fuel every day')

### Grid
conn_matrix = Node('connectivity matrix', 
    description='cell ij indicates object[i] receives power from object[j]')
demand_matrix = Node('demand matrix', 
    description='desired state for each object on the grid')
state_matrix = Node('state matrix', 
    description='state from each object on the grid')
total_load = Node('total_load', description='total power required to run the microgrid')
islanded_balance = Node('islanded_balance', description='balance of grid sans Utility Grid')
total_power_balance = Node('total power supplied', 0., 
    description='total balance of power supplied (+) or demanded (-) by grid (W)')
power_wasted = Node('power wasted', 0., 
    description='cumulative power supplied to grid in excess of current demand (W)')
list_load_shedding = Node('list of load shedding', 
    description='a list of objects whose loads are removed from the grid')
all_loads_shed = Node('all loads shed', 
    description='true if all loads in the graph have been shed (Bool)')
num_loads = Node('num loads', 
    description='number of loads (buildings) on grid')
names = Node('names', 
    description='ordered list of names of objects considered in the model')

### Simulation
elapsed_hours = Node('elapsed hours', 0, 
    description='number of hours that have passed during the simulation.')
start_year = Node('start year', description='starting year for the simulation')
start_day = Node('start day', description='starting day for the simulation (1-366)')
start_hour = Node('start hour', 1, description='starting hour for the simulation (1-24)')
year = Node('year', description='current year')
day = Node('day', description='current day of the year (1-366)')
hour = Node('hour', description='current hour (0-23)')
hour_idx = Node('hour index', description='current hour of the year (1-8784)')
num_leapyears = Node('num leapyears', 
    description='number of leapyears encountered during the simulation')
max_hour_index = Node('max_hour_index', description='maximum hour index for the year')
is_leapyear = Node('is leapyear', description='true if the current year is a leapyear')
tol = Node('tolerance', 0.5, description='float tolerance to be ignored')

### Components
is_islanded = Node('is islanded', 
    description='true if the utiliy grid is disconnected')
sunlight = Node('sunlight', units='W-hr/m^2',
    description='energy from sun for a specific hour')
sunlight_data = Node('sunlight_data', 
    description='dict of yearly sunlight values by hour')
sunlight_filename = Node('sunlight_filename', 
    description='filename for sunlight csv file')
sunlight_data_label = Node('sunlight_data_label', 'SUNY Dir (Wh/m^2)', 
    description='name of column for sunlight data')
load_filename = Node('load filename',
    description='filename for load information')
batt_trickle = Node('battery trickle charge rate prop', 0.25, 
    description='proportion of maximum charging rate to reduce batteries to after 80% charged')
next_refuel_hour = Node('next refuel hour', 0, 
    description='next hour generators will be refueled')

### Outputs
# output_filename = Node('output filename', 'output.txt', description='name of output file')
# failing_objects = Node('failing_objects', description='list of failing components')


## ----- Edges ----- ##
### Simulation
mg.add_edge(days_in_year, days_in_leapyear, lambda s1, **kw : s1 + 1)
mg.add_edge({'days':days_in_year, 'hours':hours_in_day}, hours_in_year, R.Rmultiply)
mg.add_edge({'days':days_in_leapyear, 'hours':hours_in_day}, 
            hours_in_leapyear, R.Rmultiply)
mg.add_edge({'use_rand_date': use_random_date, 'min_year': min_year, 'max_year': max_year}, start_year, 
            Rget_random_year, via=lambda use_rand_date, **kwargs : use_rand_date)
mg.add_edge({'random': use_random_date, 'days_in_year': days_in_year}, start_day, 
            Rget_random_day, via=lambda random, **kw : random is True)
mg.add_edge({'random': use_random_date, 'hours_in_day': hours_in_day}, start_hour, 
            Rget_random_hour, via=lambda random, **kw : random is True)
mg.add_edge({'start_year': start_year, 'elapsed_hours': elapsed_hours, 
             'hours_in_year': hours_in_year, 'hours_in_leapyear': hours_in_leapyear}, 
            num_leapyears, Rcalc_num_leapyears, label='calc_num_leapyears')
mg.add_edge(elapsed_hours, elapsed_hours, R.Rincrement, index_offset=1)
mg.add_edge({'elapsed_hours': elapsed_hours, 'start_year': start_year, 
             'num_leapyears': num_leapyears, 'start_day': start_day, 
             'start_hour': start_hour, 'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year}, year, Rcalc_year,
             disposable=['elapsed_hours', 'num_leapyears'],
             index_via=lambda elapsed_hours, num_leapyears, **kw :
                       R.Rsame(elapsed_hours, num_leapyears))
mg.add_edge({'elapsed_hours': elapsed_hours, 'start_year': start_year, 
             'year': year, 'num_leapyears': num_leapyears, 'start_day': start_day, 
             'start_hour': start_hour, 'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year}, day, Rcalc_day, 
             disposable=['elapsed_hours', 'year', 'num_leapyears'],
             index_via=lambda elapsed_hours, year, **kw : R.Rsame(elapsed_hours, year))
mg.add_edge({'elapsed_hours': elapsed_hours, 'start_hour': start_hour, 
             'hours_in_day': hours_in_day}, hour, Rcalc_hour)
mg.add_edge({'day': day, 'hour': hour, 'is_leapyear': is_leapyear, 
             'hours_in_year': hours_in_year, 'hours_in_leapyear': hours_in_leapyear, 
             'hours_in_day': hours_in_day}, hour_idx, Rget_hour_index,
            disposable=['day', 'hour', 'is_leapyear'],
            index_via=lambda day, hour, is_leapyear, **kw : R.Rsame(day, hour, is_leapyear))
mg.add_edge(year, is_leapyear, Rcalc_year_is_leapyear)

### Grid
mg.add_edge({'A': conn_matrix, 'B': demand_matrix}, state_matrix, Rlinear_solve, 
            label='solve state matrix', edge_props=['LEVEL', 'DISPOSE_ALL'])
mg.add_edge(state_matrix, total_power_balance, 
            lambda s1, **kwargs : sum(s1), index_offset=1)
mg.add_edge({'wasted': power_wasted, 'balance': total_power_balance}, power_wasted, 
            lambda wasted, balance, **kwargs : wasted + min(0., balance), 
            index_offset=1, edge_props=['LEVEL', 'DISPOSE_ALL'])
mg.add_edge([B.name for B in BUILDINGs], num_loads, 
            lambda *args, **kwargs : len(R.extend(args, kwargs)))
mg.add_edge({'l': list_load_shedding, 'num': num_loads}, all_loads_shed, 
            lambda l, num, **kwargs : len(l) >= num)

### Objects
mg.add_edge([o.demand for o in OBJECTS if o != UG], islanded_balance, R.Rsum, 
            label='calc_island_balance', edge_props=['LEVEL', 'DISPOSE_ALL'])
mg.add_edge({o.name for o in OBJECTS}, names, Rsort_names)
keyed_receiving_nodes = {}
for OBJ in OBJECTS:
    #### Power Flow
    mg.add_edge({'state': OBJ.state, 'demand': OBJ.demand}, OBJ.is_overloaded, 
                lambda state, demand, **kwargs : demand > state, 
                edge_props=['LEVEL', 'DISPOSE_ALL'])
    # mg.add_edge(OBJ.is_connected, OBJ.demand, lambda **kwargs : 0., via=lambda s1, **kwargs : s1 is False) #TODO: This should be a super node
    mg.add_edge(OBJ.is_connected, OBJ.state, lambda **kwargs : 0., 
                via=lambda s1, **kwargs : s1 is False)
    mg.add_edge({'x': state_matrix, 'name': OBJ.name, 'names': names}, 
                OBJ.state, Rget_state_from_matrix, 
                label=f'retrieve state of {str(OBJ)}', index_offset=1)
    for SRC in OBJECTS:
        if SRC is OBJ:
            mg.add_edge({'receives_from': OBJ.receives_from[str(SRC)], 
                         'is_conn': OBJ.is_connected}, 
                        OBJ.receiving_from[str(SRC)], 
                        disposable=['is_conn'],
                        label=f'{str(OBJ)} receiving from itself',
                        rel=lambda receives_from, is_conn, **kwargs : 
                            receives_from and is_conn)
        else:
            mg.add_edge({'receives_from': OBJ.receives_from[str(SRC)], 
                         'receiver_conn': OBJ.is_connected, 
                         'provider_conn': SRC.is_connected}, 
                        OBJ.receiving_from[str(SRC)], 
                        rel=Rcalc_if_receiving_power, 
                        label=f'{str(OBJ)} receiving from {str(SRC)}',
                        disposable=['receiver_conn', 'provider_conn'],
                        index_via=lambda receiver_conn, provider_conn, **kw : 
                                  R.Rsame(receiver_conn, provider_conn))
        keyed_receiving_nodes.update({generate_connectivity_keyword(OBJ, SRC) : 
                                      OBJ.receiving_from[str(SRC)]})

    #### Failures and Load Shedding
    mg.add_edge({'is_failing': OBJ.is_failing, 'random_fail': has_random_failure, 
                 'p': OBJ.prob_failing}, OBJ.is_failing, 
                rel=lambda p, **kwargs : p > random.random(), index_offset=1,
                via=lambda random_fail, is_failing, **kwargs : 
                    random_fail is True and is_failing is False)
    mg.add_edge({'is_failing': OBJ.is_failing, 'p': OBJ.prob_fixed}, OBJ.is_failing, 
                rel=lambda p, **kwargs : not (p > random.random()), index_offset=1,
                via=lambda is_failing, **kwargs : is_failing is True)
    #TODO: Need a way to specify failures of connectivity (like BUS1/BUS2 line)
    mg.add_edge({'shedding_list': list_load_shedding, 'name': OBJ.name}, 
                OBJ.is_load_shedding, 
                rel=lambda shedding_list, name, **kwargs : name in shedding_list)
    if OBJ != UG:
        mg.add_edge({'is_failing': OBJ.is_failing, 'is_load_shedding': OBJ.is_load_shedding}, 
                    OBJ.is_connected, R.Rnot_any)

mg.add_edge(keyed_receiving_nodes | {'names': names, 'key_sep': key_sep}, conn_matrix, 
            rel=Rform_connectivity_matrix, 
            label='form connectivity matrix',
            disposable=[key for key in keyed_receiving_nodes],
            index_via=lambda **kwargs : R.Rsame(*[kwargs[key] for key in keyed_receiving_nodes]))

#### Demand matrix
demand_pairs = {'names': names}
for i, OBJ in enumerate(OBJECTS):
    mg.add_edge({'name': OBJ.name, 'demand': OBJ.demand}, OBJ.demand_pair, 
                rel=lambda name, demand : R.Rtuple(name, demand), 
                disposable='demand')
    demand_pairs[f's{i}'] = OBJ.demand_pair
mg.add_edge(demand_pairs, demand_matrix, Rform_demand_matrix, 
            label='form demand matrix', 
            disposable=[key for key in demand_pairs if key != 'names'],
            index_via=lambda **kwargs : R.Rsame(*[kwargs[key] for key in demand_pairs 
                                                  if key != 'names']))

### Busses
for BUS in BUSs:
    mg.add_edge(elapsed_hours, BUS.demand, R.Rnull)

### Utility Grids
mg.add_edge({'island': island_mode, 'failing': UG.is_failing, 'load_shedding': UG.is_load_shedding}, 
            UG.is_connected, R.Rnot_any, disposable='failing')
mg.add_edge({'conn': UG.is_connected, 'load': islanded_balance}, UG.demand, 
            #TODO: This really should be the load of everything connected to the UG
            lambda conn, load, **kw : abs(load) if conn else 0., edge_props='LEVEL')
mg.add_edge(UG.is_connected, is_islanded, 
            rel=lambda *args, **kwargs : not any(R.extend(args, kwargs)),
            edge_props=['LEVEL', 'DISPOSE_ALL'])

### Solar
mg.add_edge(year, sunlight_filename, Rget_solar_filename)
mg.add_edge(sunlight_filename, sunlight_data, Rget_data_from_csv_file)
mg.add_edge({'csv_data': sunlight_data, 'row': hour_idx, 'col': sunlight_data_label}, 
            sunlight, Rget_float_from_csv_data,
            index_via=lambda csv_data, row, **kw: R.Rsame(csv_data, row), disposable=['csv_data', 'row'])
for PV in PVs:
    mg.add_edge({'conn': PV.is_connected,'area': PV.area, 'efficiency': 
                 PV.efficiency, 'sunlight': sunlight}, PV.demand, 
                rel=Rcalc_solar_demand, disposable=['sunlight', 'conn'],
                index_via=lambda conn, sunlight, **kw : R.Rsame(conn, sunlight))

### Buildings
mg.add_edge([B.demand for B in BUILDINGs], total_load, Rdetermine_load, 
            edge_props=['LEVEL', 'DISPOSE_ALL'])
#TODO: There needs to be a more systematic way of indicating that an object solves for load_shedding.
shedding_nodes = {'balance': total_power_balance, 
                  generate_building_keyword('balance', 'index') : ('balance', 'index')}
for B in BUILDINGs:
    mg.add_edge(B.type, B.building_filename, Rget_building_filename)
    mg.add_edge(B.building_filename, B.load_data, Rget_data_from_csv_file)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.normal_col_name}, 
                B.normal_load, Rget_load_from_building_data)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.lights_col_name}, 
                B.lights_load, Rget_load_from_building_data)
    mg.add_edge({'csv_data': B.load_data, 'row': hour_idx, 'col': B.equipment_col_name}, 
                B.equipment_load, Rget_load_from_building_data)
    mg.add_edge({'lights': B.lights_load, 'equipment': B.equipment_load},
                B.critical_load, Rcalc_critical_load,
                edge_props=['LEVEL', 'DISPOSE_ALL'])
    #TODO: Need a way to tell if a building is connected to the Utility 
    #   Grid for bus failures that should induce critical loads
    mg.add_edge({'conn': B.is_connected, 'normal': B.normal_load, 
                 'critical': B.critical_load, 'island': is_islanded}, 
                B.demand, Rdetermine_building_load, 
                edge_props=['LEVEL', 'DISPOSE_ALL'], 
                label='calc building demand')
    state_label, priority_label, index_label = [generate_building_keyword(B, s) 
                                                for s in ['load', 'priority', 'index']]
    shedding_nodes[state_label] = B.state
    shedding_nodes[priority_label] = B.priority
    shedding_nodes[index_label] = (state_label, 'index')
mg.add_edge(shedding_nodes | {'names': names, 'key_sep': key_sep}, list_load_shedding, 
            rel=Rdetermine_load_shedding, 
            via=Vload_nodes_are_level, 
            disposable=[generate_building_keyword(B, 'load') for B in BUILDINGs] + ['balance'])

### Generators
mg.add_edge({'refuel_time': next_refuel_hour, 'curr_hour': hour_idx, 
             'prob': prob_daily_refueling, 'hours_in_day': hours_in_day}, 
            next_refuel_hour, Rcalc_next_time_for_refueling, 
            index_offset=1,
            disposable=['refuel_time', 'curr_hour'],
            index_via=lambda refuel_time, curr_hour, **kw : 
                      R.Rsame(refuel_time, curr_hour))
for G in GENs:
    mg.add_edge({'fl': G.fuel_level, 'tol': tol}, G.out_of_fuel, 
                lambda fl, tol, **kwargs :abs(fl) < tol)
    mg.add_edge({'is_islanded': is_islanded, 'load': total_load, 
                 'max_out': G.max_output, 'conn': G.is_connected, 
                 'out_of_fuel': G.out_of_fuel}, G.demand,
                rel=Rcalc_generator_demand, label=f'calc demand for {G}',
                disposable=['is_islanded', 'load', 'conn', 'out_of_fuel'],
                index_via=lambda is_islanded, load, conn, out_of_fuel, **kw : 
                          R.Rsame(is_islanded, load, conn, out_of_fuel))
    mg.add_edge({'init': G.starting_fuel_level, 'max': G.fuel_capacity}, 
                G.fuel_level, R.Rmin)
    mg.add_edge({'refuel_time': next_refuel_hour, 'curr_hour': hour_idx, 
                 'curr_level': G.fuel_level, 'max_level': G.fuel_capacity}, 
                G.fuel_level, Rcalc_generator_fuel_level, 
                disposable=['refuel_time', 'curr_hour', 'curr_level'], index_offset=1,
                index_via=lambda refuel_time, curr_hour, curr_level, **kw : 
                          R.Rsame(refuel_time, curr_hour, curr_level))

### Batteries
for B in BATTERYs:
    mg.add_edge({'island': is_islanded, 'load': total_load, 'level': B.charge_level, 
                 'capacity': B.charge_capacity}, B.is_charging,
                rel=Rdetermine_battery_is_charging, 
                label='determine if battery is charging',
                disposable=['island', 'load'],
                index_via=lambda island, load, level, **kw : R.Rsame(island, load, level))
    mg.add_edge({'is_charging': B.is_charging, 'load': total_load, 'level':B.charge_level, 
                 'capacity': B.charge_capacity, 'max_rate': B.max_charge_rate, 'max_output': B.max_output, 
                 'trickle_prop': batt_trickle}, B.demand, 
                rel=Rcalc_battery_demand, 
                label='calc battery demand',
                disposable=['level', 'is_charging', 'load'],
                index_via=lambda is_charging, load, level, **kw : R.Rsame(is_charging, load, level))
    mg.add_edge({'state': B.state, 'level': B.charge_level, 
                 'max_level': B.charge_capacity, 'eff': B.efficiency}, 
                B.charge_level, 
                rel=Rcalc_battery_charge_level, 
                label='calc battery charge level',
                index_via=lambda state, level, **kw: R.Rsame(state-1, level))
