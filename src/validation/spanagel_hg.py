"""This is a digital twin of the Spanagel Rooftop Microgrid, a benchtop 
microgrid installed at the Naval Postgraduate School in Monterrey, CA.

Comparative test results come from a run from Apr 29 through 
May 1st, 2025.
"""
from constrainthg import Node, Hypergraph
import constrainthg.relations as R
import random

from model.microgrid_actors import *
from model.microgrid_relations import *

random.seed(3)

sg = Hypergraph(no_weights=True)

## Nodes
PVs = [
    PhotovoltaicArray(
        name='PV1', 
        cost=0.001,
    )
]

GENs = [
    Generator(
        name='Generator1', 
        fuel_capacity=28., 
        starting_fuel_level=28., 
        max_output=6.2, 
    ),
]

BATTERYs = [
    Battery(
        name='BESS', 
        charge_capacity=18.,
        charge_level=13, 
        max_output=350.,
        charge_efficiency=0.85,
        max_charge_rate=10.,
        trickle_prop=0.9,
    ),
]

LOADs = [
    Load(name='TestLoad',
         benefit=100,
    ),
]

BUSs = [
    Bus('Bus1')
]

WINDs, BUILDINGs, UGs = [], [], []

ACTORS = GENs + BATTERYs + UGs + BUSs + PVs + BUILDINGs + WINDs + LOADs

### Connectivity
for ACTOR in ACTORS: #Set default as not connected
    for SRC in ACTORS:
        ACTOR.add_source(SRC, SRC is ACTOR)

for SRC in ACTORS:
    BUSs[0].add_source(SRC, True)
    SRC.add_source(BUSs[0], True)

### Other nodes
valid_data_path = Node('validation_data_path')
valid_data = Node('validation_data')
time_column = Node('time_data_column', 1)
pv_power_label = Node('pv_power_label', 'Solar Power (kW)')
load_label = Node('node_label', 'Powerload (kW)')



#####################################################
# DEFAULT MICROGRID MODEL
#####################################################

def make_demand_tuple_edge(ACTOR: GridActor, dynamic: list):
    """Convenience function for making the demand tuple edge.
    
    #TODO: This function is provided for convenience. Eventually there 
    needs to be a way to specify disposal doesn't affect input nodes. 
    (Issue #1) Otherwise we need to make a index_via/disposal method for 
    each object since some treat these nodes statically, while others do not.
    """
    sg.add_edge({'label': ACTOR.name,
                 'benefit': ACTOR.benefit,
                 'req_demand': ACTOR.req_demand,
                 'max_demand': ACTOR.max_demand},
                target=ACTOR.demand_tuple,
                rel=lambda **kw : R.to_tuple(['label', 'benefit', 'req_demand',
                                               'max_demand'], **kw),
                disposable=dynamic,
                index_via=lambda **kw : R.Rsame(*[kw[key] for key in dynamic]),
                label='make_demand_tuple')
    
def make_supply_tuple_edge(ACTOR: GridActor, dynamic: list):
    """Convenience function for making the supply tuple edge."""
    sg.add_edge({'label': ACTOR.name,
                 'cost': ACTOR.cost,
                 'supply': ACTOR.supply,
                 'is_cost_per_unit': ACTOR.is_cost_per_unit},
                target=ACTOR.supply_tuple,
                rel=lambda **kw : R.to_tuple(['label', 'cost', 'supply', 'is_cost_per_unit'], **kw),
                disposable=dynamic,
                index_via=lambda **kw : R.Rsame(*[kw[key] for key in dynamic]),
                label='make_supply_tuple')

#### Active receivers (initialize nodes for actors actively receiving power from other actors)
for ACTOR in ACTORS:
    for SRC in ACTORS:
        ACTOR.add_active_source(SRC, None)


## ----- Nodes ----- ##
### Constants
key_sep = Node('key_sep', KEY_SEP, 
    description='A unique constant for seperating strings in paired keywords')
days_in_year = Node('days_in_year', 365, description='number of days in a year')
days_in_leapyear = Node('days_in_leapyear', description='number of days in a leapyear')
hours_in_day = Node('hours_in_day', 24, description='number of hours in a day')
hours_in_year = Node('hours_in_year', description='number of hours in a year')
hours_in_leapyear = Node('hours_in_leapyear', description='number of hours in a leapyear')
seconds_in_minute = Node('seconds_in_minute', 60, description='number of seconds in a minute')
minutes_in_hour = Node('minutes_in_hour', 60, description='number of minutes in an hour')
seconds_in_hour = Node('seconds_in_hour', description='num seconds in an hour')

### Setup Conditions
island_mode = Node('island_mode', 
    description='true if the utility grid is to be treated as disconnected')
has_random_failure = Node('has_random_failure', False, 
    description='true if random failure is allowed')
use_random_date = Node('use_random_date', True, 
    description='true if the start date is set randomly')
min_year = Node('min year', 2000, description='minimum year of simulation data')
max_year = Node('max year', 2009, description='maximum year of simulation data')
prob_daily_refueling = Node('prob of daily refueling', 0.25, 
    description='probability that the generators receive new fuel every day')

### Grid
conn_matrix = Node('connectivity matrix', 
    description='cell ij indicates actor[i] receives power from actor[j]')
state_vector = Node('state_vector', 
    description='state from each actor on the grid')
islanded_balance = Node('islanded_balance', description='balance of grid sans Utility Grid')
total_power_balance = Node('total power supplied', 0., 
    description='total balance of power supplied (+) or demanded (-) by grid (W)')
power_wasted = Node('power wasted', 0., 
    description='cumulative power supplied to grid in excess of current demand (W)')
list_load_shedding = Node('list of load shedding', 
    description='a list of actors whose loads are removed from the grid')
all_loads_shed = Node('all loads shed', 
    description='true if all loads in the graph have been shed (Bool)')
num_loads = Node('num loads', 
    description='number of loads (buildings) on grid')
names = Node('names', 
    description='ordered list of names of actors considered in the model')

### Simulation
time_step = Node('time_step', units='hr',
    description='hours since last time calculation')
time = Node('time', 0, units='s',
    description='total seconds passed during the simulation')
elapsed_hours = Node('elapsed_hours', 
    description='number of hours that have passed during the simulation')
elapsed_minutes = Node('elapsed_minutes', 0,
    description='number of minutes that have passed during the simulation')
start_year = Node('start year', description='starting year for the simulation')
start_day = Node('start day', 
    description='starting day for the simulation (1-366)')
start_hour = Node('start hour', 1, 
    description='starting hour for the simulation (1-24)')
year = Node('year', description='current year')
day = Node('day', description='current day of the year (1-366)')
hour = Node('hour', description='current hour (0-23)')
hour_idx = Node('hour index', description='current hour of the year (1-8784)')
num_leapyears = Node('num leapyears', 
    description='number of leapyears encountered during the simulation')
max_hour_index = Node('max_hour_index', 
    description='maximum hour index for the year')
is_leapyear = Node('is leapyear', 
    description='true if the current year is a leapyear')
tol = Node('tolerance', 0.001, description='float tolerance to be ignored')

### Components
is_islanded = Node('is islanded', 
    description='true if the utiliy grid is disconnected')
sunlight_directory = Node('sunlight_directory', 'src/solar_data',
    description='directory for solar data')
sunlight = Node('sunlight', units='W-hr/m^2',
    description='energy from sun for a specific hour')
sunlight_data = Node('sunlight_data', 
    description='dict of yearly sunlight values by hour')
sunlight_filename = Node('sunlight_filename', 
    description='filename for sunlight csv file')
sunlight_data_label = Node('sunlight_data_label', 'SUNY Dir (Wh/m^2)', 
    description='name of column for sunlight data')
wind_speed = Node('wind_speed', 
    description='average wind speed over the last hour', units='m/s')
air_density = Node('air_density', 
    description='average density of the air', units='kg/m^3')
load_directory = Node('load_directory', 'src/building_data',
    description='directory for building load data')
load_filename = Node('load filename',
    description='filename for load information')
batt_trickle = Node('battery trickle charge rate prop', 0.25, 
    description='proportion of maximum charging rate to reduce batteries to after 80% charged')
cost_of_diesel = Node('cost of diesel', 0.92,
    description='cost of diesel fuel',
    units='$/L')
next_refuel_hour = Node('next refuel hour', 0, 
    description='next hour generators will be refueled')
failing_actors = Node('failing_actors',
    description='list of failing components')


## ----- Edges ----- ##
### Simulation
sg.add_edge(days_in_year, days_in_leapyear, lambda s1, **kw : s1 + 1)

sg.add_edge({'days':days_in_year,
             'hours':hours_in_day},
            target=hours_in_year,
            rel=R.Rmultiply,
            )
sg.add_edge({'days':days_in_leapyear,
             'hours':hours_in_day}, 
            target=hours_in_leapyear,
            rel=R.Rmultiply
            )
sg.add_edge({'use_rand_date': use_random_date,
             'min_year': min_year,
             'max_year': max_year},
            target=start_year, 
            rel=Rget_random_year,
            via=lambda use_rand_date, **kwargs : use_rand_date
            )
sg.add_edge({'random': use_random_date,
             'days_in_year': days_in_year},
            target=start_day, 
            rel=Rget_random_day,
            via=lambda random, **kw : random is True
            )
sg.add_edge({'random': use_random_date,
             'hours_in_day': hours_in_day},
            target=start_hour, 
            rel=Rget_random_hour,
            via=lambda random, **kw : random is True
            )
sg.add_edge({'start_year': start_year,
             'elapsed_hours': elapsed_hours, 
             'hours_in_year': hours_in_year,
             'hours_in_leapyear': hours_in_leapyear}, 
            target=num_leapyears,
            rel=Rcalc_num_leapyears,
            label='calc_num_leapyears',
            )
sg.add_edge({'time': time, 
             'step': time_step}, 
            target=time,
            rel=R.Rsum,
            index_offset=1,
            )
sg.add_edge({'sec_in_min': seconds_in_minute,
             'min_in_hour': minutes_in_hour},
             target=seconds_in_hour,
             rel=R.Rmultiply,
             )
sg.add_edge({'time': time, 
             'seconds_in_hour': seconds_in_hour}, 
            target=elapsed_hours,
            rel=Rcalc_elapsed_hours,
            disposable=['time'])

sg.add_edge({'elapsed_hours': elapsed_hours,
             'start_year': start_year, 
             'num_leapyears': num_leapyears,
             'start_day': start_day, 
             'start_hour': start_hour,
             'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year},
            target=year,
            rel=Rcalc_year,
            disposable=['elapsed_hours', 'num_leapyears'],
            index_via=lambda elapsed_hours, num_leapyears, **kw :
                       R.Rsame(elapsed_hours, num_leapyears)
            )
sg.add_edge({'elapsed_hours': elapsed_hours,
             'start_year': start_year, 
             'year': year,
             'num_leapyears': num_leapyears,
             'start_day': start_day, 
             'start_hour': start_hour,
             'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year},
            target=day,
            rel=Rcalc_day, 
            disposable=['elapsed_hours', 'year', 'num_leapyears'],
            index_via=lambda elapsed_hours, year, **kw : 
                      R.Rsame(elapsed_hours, year)
            )
sg.add_edge({'elapsed_hours': elapsed_hours,
             'start_hour': start_hour, 
             'hours_in_day': hours_in_day},
            target=hour,
            rel=Rcalc_hour,
            )
sg.add_edge({'day': day,
             'hour': hour,
             'is_leapyear': is_leapyear, 
             'hours_in_year': hours_in_year,
             'hours_in_leapyear': hours_in_leapyear, 
             'hours_in_day': hours_in_day},
            target=hour_idx,
            rel=Rget_hour_index,
            disposable=['day', 'hour', 'is_leapyear'],
            index_via=lambda day, hour, is_leapyear, **kw : 
                      R.Rsame(day, hour, is_leapyear)
            )
sg.add_edge(year, is_leapyear, Rcalc_year_is_leapyear)

### Grid
sg.add_edge(state_vector, 
            target=total_power_balance, 
            rel=lambda s1, **kwargs : sum(s1),
            index_offset=1
            )
sg.add_edge({'wasted': power_wasted,
             'balance': total_power_balance},
            target=power_wasted, 
            rel=lambda wasted, balance, **kwargs : wasted + min(0., balance), 
            index_offset=1,
            edge_props=['LEVEL', 'DISPOSE_ALL']
            )
sg.add_edge(state_vector,
            target=num_loads, 
            rel=lambda s1, **kw : sum([a > 0 for a in s1]),
            )
sg.add_edge({'l': list_load_shedding,
             'num': num_loads},
            target=all_loads_shed, 
            rel=lambda l, num, **kwargs : len(l) >= num
            )

### Actors
sg.add_edge([A.state for A in ACTORS if A not in UGs], 
            target=islanded_balance,
            rel=R.Rsum, 
            label='calc_island_balance',
            edge_props=['LEVEL', 'DISPOSE_ALL'],
            )
sg.add_edge({str(A) : A.is_failing for A in ACTORS} | {'names': names},
            target=failing_actors,
            rel=Rget_failing_actors,
            label='get_failing_actors',
            disposable=[str(A) for A in ACTORS],
            index_via=lambda *ar, **kwargs : R.Rsame(*[val for key,val in kwargs.items() 
                                                       if key != 'names']),
            )
sg.add_edge({A.name for A in ACTORS}, names, Rsort_names)

keyed_receiving_nodes = {}
for ACTOR in ACTORS:
    #### Power Flow
    sg.add_edge(ACTOR.is_connected, ACTOR.state, 
                rel=lambda **kwargs : 0., 
                via=lambda s1, **kwargs : s1 is False
                )
    sg.add_edge({'x': state_vector,
                 'name': ACTOR.name,
                 'names': names}, 
                target=ACTOR.state, 
                rel=Rget_state_from_vector, 
                label=f'retrieve state of {str(ACTOR)}', index_offset=1
                )
    for SRC in ACTORS:
        if SRC is ACTOR:
            sg.add_edge({'receives_from': ACTOR.receives_from[str(SRC)], 
                         'is_conn': ACTOR.is_connected}, 
                        target=ACTOR.receiving_from[str(SRC)], 
                        rel=lambda receives_from, is_conn, **kwargs : 
                            receives_from and is_conn,
                        disposable=['is_conn'],
                        label=f'{str(ACTOR)} receiving from itself',
                        )
        else:
            sg.add_edge({'receives_from': ACTOR.receives_from[str(SRC)], 
                         'receiver_conn': ACTOR.is_connected, 
                         'provider_conn': SRC.is_connected}, 
                        target=ACTOR.receiving_from[str(SRC)], 
                        rel=Rcalc_if_receiving_power, 
                        label=f'{str(ACTOR)} receiving from {str(SRC)}',
                        disposable=['receiver_conn', 'provider_conn'],
                        index_via=lambda receiver_conn, provider_conn, **kw : 
                                  R.Rsame(receiver_conn, provider_conn)
                        )
        keyed_receiving_nodes.update({generate_connectivity_keyword(ACTOR, SRC) : 
                                      ACTOR.receiving_from[str(SRC)]})

    #### Failures and Load Shedding
    sg.add_edge({'random_fail': has_random_failure, 
                 'is_failing': ACTOR.is_failing},
                target=ACTOR.is_failing, 
                index_offset=1,
                rel=lambda **kw : False,
                label='set_no_failures',
                disposable=['is_failing'],
                via=lambda random_fail, **kw : random_fail is False,
                )
    sg.add_edge({'is_failing': ACTOR.is_failing,
                 'random_fail': has_random_failure, 
                 'p_fail': ACTOR.prob_failing,
                 'p_fix': ACTOR.prob_fixed},
                target=ACTOR.is_failing, 
                rel=Rdeterming_if_failing,
                label='determine_if_failing',
                index_offset=1,
                disposable=['is_failing'],
                via=lambda random_fail, **kwargs : random_fail is True,
                )

    sg.add_edge({'req_demand': ACTOR.req_demand,
                 'state': ACTOR.state,
                 'tol': tol},
                 target=ACTOR.is_load_shedding,
                 rel=Rdetermine_if_loadshedding,
                 disposable=['req_demand', 'state'],
                 index_via=lambda req_demand, state, **kw : 
                            R.Rsame(req_demand, state),
                )
    if ACTOR not in UGs:
        sg.add_edge({'is_failing': ACTOR.is_failing}, 
                    ACTOR.is_connected,
                    R.Rnot_any,
                    edge_props=['LEVEL', 'DISPOSE_ALL'],
                    )

sg.add_edge(keyed_receiving_nodes | {'names': names, 'key_sep': key_sep},
            target=conn_matrix, 
            rel=Rform_connectivity_matrix, 
            label='form connectivity matrix',
            disposable=[key for key in keyed_receiving_nodes],
            index_via=lambda **kwargs : R.Rsame(*[kwargs[key] for key in keyed_receiving_nodes])
            )

#### Demand vector
actor_lists = [UGs, BUSs, PVs, WINDs, LOADs, BUILDINGs, GENs, BATTERYs]
s_dynamic = [[], [], ['supply'], ['supply'], [], [], [], ['cost', 'supply']]
d_dynamic = [[], [], [], [], ['req_demand', 'max_demand'], ['req_demand', 'max_demand'], [], ['benefit', 'max_demand']]

demand_sources, dynamic_sources, i = {}, [], 0
for ACTORS, s_d, d_d in zip(actor_lists, s_dynamic, d_dynamic):
    for A in ACTORS:
        make_supply_tuple_edge(A, s_d)
        make_demand_tuple_edge(A, d_d)

        i += 1
        demand_sources[f'demand_tuple{i}'] = A.demand_tuple
        demand_sources[f'supply_tuple{i}'] = A.supply_tuple
        if len(s_d) > 0:
            dynamic_sources.append(f'supply_tuple{i}')
        if len(d_d) > 0:
            dynamic_sources.append(f'demand_tuple{i}')
demand_sources.update({'conn': conn_matrix, 'names': names, 'tol': tol})
dynamic_sources.append('conn')

sg.add_edge(demand_sources,
            target=state_vector,
            rel=Rmake_state_vector,
            label='make_state_vector',
            disposable=dynamic_sources,
            index_via = lambda **kwargs : 
                R.Rsame(*[kwargs[key] for key in dynamic_sources if key in kwargs]),
            )

### Busses

### Utility Grids
sg.add_edge([UG.is_connected for UG in UGs], 
            target=is_islanded, 
            rel=lambda *args, **kwargs : not any(R.extend(args, kwargs)),
            edge_props=['LEVEL', 'DISPOSE_ALL']
            )
for UG in UGs:
    sg.add_edge({'island': island_mode,
                 'failing': UG.is_failing}, 
                target=UG.is_connected,
                disposable=['failing'],
                rel=R.Rnot_any,
                )

### Solar
sg.add_edge({'directory': sunlight_directory,
             'year': year}, 
            sunlight_filename, 
            Rget_solar_filename,
            )

# sg.add_edge(sunlight_filename, sunlight_data, Rget_data_from_csv_file)

sg.add_edge({'csv_data': sunlight_data,
             'row': hour_idx,
             'col': sunlight_data_label}, 
            target=sunlight,
            rel=Rget_float_from_csv_data,
            index_via=lambda csv_data, row, **kw: R.Rsame(csv_data, row), 
            disposable=['csv_data', 'row']
            )

for PV in PVs:
    sg.add_edge({'conn': PV.is_connected,
                 'area': PV.area,
                 'efficiency': PV.efficiency,
                 'sunlight': sunlight},
                target=PV.supply, 
                rel=Rcalc_solar_supply,
                label='calc_solar_supply',
                disposable=['sunlight', 'conn'],
                index_via=lambda conn, sunlight, **kw : R.Rsame(conn, sunlight)
                )
    
### Wind
for W in WINDs:
    sg.add_edge({'area': W.rotor_area, 
                 'power_coef': W.power_coef, 
                 'velocity': wind_speed,
                 'density': air_density}, 
                target=W.supply, 
                rel=Rcalc_wind_supply,
                disposable=['velocity', 'density'],
                index_via=lambda density, velocity, **kw : R.Rsame(density, velocity)
                )
    
### Loads
for L in LOADs + BUILDINGs:
    sg.add_edge(L.req_demand, L.max_demand, R.Rfirst)

    sg.add_edge({'conn': L.is_connected, 
                 'normal': L.normal_load, 
                 'critical': L.critical_load,
                 'island': is_islanded}, 
                target=L.req_demand, 
                rel=Rdetermine_building_load, 
                edge_props=['LEVEL', 'DISPOSE_ALL'], 
                label='calc building demand'
                )

### Buildings
for B in BUILDINGs:
    sg.add_edge({'directory': load_directory,
                 'building_type': B.type},
                B.building_filename,
                Rget_building_filename)

    sg.add_edge(B.building_filename, B.load_data, Rget_data_from_csv_file)

    sg.add_edge({'csv_data': B.load_data,
                 'row': hour_idx,
                 'col': B.normal_col_name}, 
                target=B.normal_load,
                rel=Rget_float_from_csv_data
                )
    sg.add_edge({'csv_data': B.load_data, 
                 'row': hour_idx, 
                 'col': B.lights_col_name}, 
                target=B.lights_load,
                rel=Rget_float_from_csv_data
                )
    sg.add_edge({'csv_data': B.load_data, 
                 'row': hour_idx, 
                 'col': B.equipment_col_name}, 
                target=B.equipment_load, 
                rel=Rget_float_from_csv_data
                )
    sg.add_edge({'lights': B.lights_load,
                 'equipment': B.equipment_load},
                target=B.critical_load,
                rel=Rcalc_critical_load,
                edge_props=['LEVEL', 'DISPOSE_ALL']
                )


### Generators
sg.add_edge({'refuel_time': next_refuel_hour,
             'curr_hour': hour_idx, 
             'prob': prob_daily_refueling,
             'hours_in_day': hours_in_day}, 
            target=next_refuel_hour, 
            rel=Rcalc_next_time_for_refueling, 
            index_offset=1,
            disposable=['refuel_time', 'curr_hour'],
            index_via=lambda refuel_time, curr_hour, **kw : 
                      R.Rsame(refuel_time, curr_hour)
            )
i = 0
for G in GENs:
    sg.add_edge({'fl': G.fuel_level, 
                 'tol': tol}, 
                target=G.out_of_fuel, 
                rel=lambda fl, tol, **kwargs :abs(fl) < tol
                )
    sg.add_edge({'init': G.starting_fuel_level, 
                 'max': G.fuel_capacity}, 
                G.fuel_level, 
                R.Rmin,
                )
    sg.add_edge({'refuel_time': next_refuel_hour, 
                 'curr_hour': hour_idx, 
                 'curr_level': G.fuel_level,
                 'max_level': G.fuel_capacity}, 
                target=G.fuel_level, 
                rel=Rcalc_generator_fuel_level, 
                disposable=['refuel_time', 'curr_hour', 'curr_level'], 
                index_offset=1,
                index_via=lambda refuel_time, curr_hour, curr_level, **kw : 
                          R.Rsame(refuel_time, curr_hour, curr_level)
                )
    sg.add_edge({'load': G.state,
                 'max_load': G.max_output,
                 'seconds_in_hour': seconds_in_hour,
                 'time_step': time_step},
                target=G.consumption,
                rel=Rcalc_generator_fuel_consumption,
                disposable=['load'],
                )
    
    #Added in response to Issue #6 in ConstraintHg regarding resolving duplicate nodes
    sg.add_edge(G.max_output, f'max_output{GENs.index(G)}', R.Rfirst)
    sg.add_edge({'load': f'max_output{GENs.index(G)}',
                 'max_load': G.max_output,
                 'seconds_in_hour': seconds_in_hour,
                 'time_step': time_step},
                target=G.max_consumption,
                rel=Rcalc_generator_fuel_consumption,
                )
    sg.add_edge({'fuel_cost': cost_of_diesel,
                 'output': G.max_output,
                 'consumption': G.max_consumption},
                target=G.cost,
                rel=Rcalc_generator_cost,
                )
    sg.add_edge(G.max_output, G.supply, R.Rfirst)


### Batteries
for B in BATTERYs:
    sg.add_edge(B.state, B.is_charging, lambda s1, **kw : s1 < 0)

    sg.add_edge({'output': B.max_output, 
                 'level': B.charge_level}, 
                 target=B.supply, 
                 rel=R.Rmin,
                 disposable=['level']
                )

    sg.add_edge({'state': B.state, 
                 'level': B.charge_level, 
                 'max_level': B.charge_capacity,
                 'time_step': time_step,
                 'efficiency': B.charge_efficiency,
                 'seconds_in_hour': seconds_in_hour}, 
                target=B.charge_level, 
                rel=Rcalc_battery_charge_level, 
                label='calc_battery_charge_level',
                disposable=['level', 'state'],
                index_via=lambda state, level, **kw: R.Rsame(state-1, level)
                )
    sg.add_edge({'level': B.charge_level, 
                 'capacity': B.charge_capacity}, 
                target=B.soc,
                rel=lambda level, capacity, **kw : level / capacity, 
                edge_props=['LEVEL, DISPOSE_ALL']
                )
    # sg.add_edge({'ug_cost': UGs[0].cost, 
    #              'tol': tol, 
    #              'level': B.charge_level, 
    #              'capacity': B.charge_capacity, 
    #              'factor': B.scarcity_factor}, 
    #             target=B.cost, 
    #             disposable=['level'],
    #             rel=Rcalc_battery_cost
    #             )
    # sg.add_edge({'ug_cost': UGs[0].cost, 
    #              'level': B.charge_level, 
    #              'capacity': B.charge_capacity, 
    #              'factor': B.scarcity_factor},
    #             target=B.benefit, 
    #             disposable=['level'],
    #             rel=Rcalc_battery_benefit,
    #             )    
    sg.add_edge({'level': B.charge_level,
                 'capacity': B.charge_capacity,
                 'max_rate': B.max_charge_rate,
                 'trickle_prop': B.trickle_prop,
                 'trickle_rate': batt_trickle,
                 'time_step': time_step}, 
                target=B.max_demand, 
                disposable=['level'],
                rel=Rcalc_battery_max_demand,
                )


###################################################
# END DEFAULT MICROGRID MODEL
###################################################

## Relationships
def Rcalc_battery_cost_spanagel(is_charging: bool, trickle_prop: float, 
                                tol: float, level: float, capacity: float):
    """Calculate the cost of using the battery."""
    if level <= tol:
        return float('inf')
    if level > capacity * trickle_prop:
        return 0.1
    elif level < capacity * 0.5:
        return 100
    elif is_charging:
        return 0.2
    return 0.1

def Rcalc_battery_benefit_spanagel(level: float, capacity:float, **kwargs):
    """Calculate the benefit of charging the battery."""
    if level >= capacity:
        return 0.0
    return 0.05

## Edges
sg.add_edge(valid_data_path, valid_data, Rget_data_from_csv_file)

sg.add_edge({'time': time,
             'seconds_in_minute': seconds_in_minute},
            target=elapsed_minutes,
            rel=Rcalc_elapsed_minutes,
            disposable=['time']
            )

for PV in PVs:
    sg.add_edge({'csv_data': valid_data,
                 'row': elapsed_minutes,
                 'col': pv_power_label}, 
                target=PV.supply,
                rel=Rget_float_from_csv_data,
                disposable=['row'],
                )
    
for L in LOADs:
    sg.add_edge(L.normal_load, L.critical_load, R.Rfirst)

    sg.add_edge({'csv_data': valid_data,
                 'row': elapsed_minutes,
                 'col': load_label}, 
                target=L.normal_load,
                rel=Rget_float_from_csv_data,
                disposable=['row'],
                )
    
    sg.add_edge(L.normal_load, L.req_demand, R.Rfirst)
    
for B in BATTERYs:
    sg.add_edge({'is_charging': B.is_charging, 
                 'trickle_prop': B.trickle_prop,
                 'tol': tol, 
                 'level': B.charge_level, 
                 'capacity': B.charge_capacity}, 
                target=B.cost, 
                rel=Rcalc_battery_cost_spanagel,
                label='calc_battery_cost',
                disposable=['level', 'is_charging'],
                index_via=lambda level, is_charging, **kw : R.Rsame(level, is_charging),
                )
    sg.add_edge({'level': B.charge_level, 
                 'capacity': B.charge_capacity},
                target=B.benefit, 
                label='calc_battery_benefit',
                disposable=['level'],
                rel=Rcalc_battery_benefit_spanagel,
                )
