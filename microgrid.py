from constrainthg import Node, Hypergraph
import constrainthg.relations as R
import random

from microgrid_actors import *
from microgrid_relations import *

#TODO: Singular matrices coming if source is not sufficient, need to have error 
#   handling for when the grid collapses (set the state to 0 basically)

random.seed(3)

mg = Hypergraph(no_weights=True)

## ----- Actors ----- ##
### Initialize Actors
UGs = [
    GridActor(
        name='UtilityGrid', 
        is_load_shedding=False,
        benefit=0.4,
        cost=0.13,
        req_demand=0.,
        max_demand=120.,
        supply=20000.,
    )
]

BUSs = [Bus('Bus1'), Bus('Bus2')]

PVs = [
    PhotovoltaicArray(
        name='PV1', 
        area=10000,
        efficiency=.18,
        cost=0.02,
    )
]

WINDs = [
    #TODO: Wind speed and density data need to be supplied
    # WindTurbine(
    #     name='Wind1',
    #     rotor_area=3800.,
    #     power_coef=0.36,
    #     cost=0.05,
    # )
]

GENs = [
    Generator(
        name='Generator1', 
        fuel_capacity=2500., 
        starting_fuel_level=2500., 
        max_output=30., 
        efficiency=0.769,
        cost=10.,
    ), 
    Generator(
        name='Generator2', 
        fuel_capacity=2500., 
        starting_fuel_level=2500., 
        max_output=100., 
        efficiency=0.769,
        cost=25.,
    ), 
]

BATTERYs = [
    Battery(
        name='Battery1', 
        charge_capacity=10000.,
        charge_level=10000., 
        max_output=100.,
        efficiency=0.9747,
        max_charge_rate=2.,
        scarcity_factor=1.5,
    ),
]

BUILDINGs = [
    Building('Building1Small', BUILDING_TYPE.SMALL, benefit=10),
    Building('Building2Small', BUILDING_TYPE.SMALL, benefit=15),
    Building('Building3Medium', BUILDING_TYPE.MEDIUM, benefit=61),
    Building('Building4Large', BUILDING_TYPE.LARGE, benefit=93),
    Building('Building5Warehouse', BUILDING_TYPE.WAREHOUSE, benefit=74),
]

ACTORS = GENs + BATTERYs + UGs + BUSs + PVs + BUILDINGs + WINDs

### Connectivity
#### Receivers (set which actors are wired to receive power from which other actors)
for ACTOR in ACTORS: #Set default as not connected
    for SRC in ACTORS:
        ACTOR.add_source(SRC, SRC is ACTOR)

bus0 = UGs + GENs + WINDs + [BUILDINGs[i] for i in [0, 3, 4]] + [BUSs[1]]
bus1 = BATTERYs + PVs + [b for b in set(BUILDINGs).difference(bus0)] + [BUSs[0]]

for SRC in bus0:
    BUSs[0].add_source(SRC, True)
    SRC.add_source(BUSs[0], True)
for SRC in bus1:
    BUSs[1].add_source(SRC, True)
    SRC.add_source(BUSs[1], True)

def make_demand_tuple_edge(ACTOR: GridActor, dynamic: list):
    """Convenience function for making the demand tuple edge.
    
    #TODO: This function is provided for convenience. Eventually there 
    needs to be a way to specify disposal doesn't affect input nodes. 
    Otherwise we need to make a index_via/disposal method for each 
    object since some treat these nodes statically, while others do not.
    """
    mg.add_edge({'label': ACTOR.name,
                 'benefit': ACTOR.benefit,
                 'req_demand': ACTOR.req_demand,
                 'max_demand': ACTOR.max_demand},
                ACTOR.demand_tuple,
                rel=lambda **kw : R.to_tuple(['label', 'benefit', 'req_demand',
                                               'max_demand'], **kw),
                disposable=dynamic,
                index_via=lambda **kw : R.Rsame(*[kw[key] for key in dynamic]),
                label='make_demand_tuple')
    
def make_supply_tuple_edge(ACTOR: GridActor, dynamic: list):
    """Convenience function for making the supply tuple edge."""
    mg.add_edge({'label': ACTOR.name,
                 'cost': ACTOR.cost,
                 'supply': ACTOR.supply},
                ACTOR.supply_tuple,
                rel=lambda **kw : R.to_tuple(['label', 'cost', 'supply'], **kw),
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
    description='cell ij indicates actor[i] receives power from actor[j]')
demand_vector = Node('demand vector', 
    description='desired state for each actor on the grid')
state_matrix = Node('state matrix', 
    description='state from each actor on the grid')
# total_load = Node('total_load', description='total power required to run the microgrid')
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
elapsed_hours = Node('elapsed hours', 0, 
    description='number of hours that have passed during the simulation.')
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
wind_speed = Node('wind_speed', 
    description='average wind speed over the last hour', units='m/s')
air_density = Node('air_density', 
    description='average density of the air', units='kg/m^3')
load_filename = Node('load filename',
    description='filename for load information')
batt_trickle = Node('battery trickle charge rate prop', 0.25, 
    description='proportion of maximum charging rate to reduce batteries to after 80% charged')
next_refuel_hour = Node('next refuel hour', 0, 
    description='next hour generators will be refueled')
failing_actors = Node('failing_actors',
    description='list of failing components')


## ----- Edges ----- ##
### Simulation
mg.add_edge(days_in_year, days_in_leapyear, lambda s1, **kw : s1 + 1)

mg.add_edge({'days':days_in_year,
             'hours':hours_in_day},
            hours_in_year,
            rel=R.Rmultiply,
            )
mg.add_edge({'days':days_in_leapyear,
             'hours':hours_in_day}, 
            hours_in_leapyear,
            rel=R.Rmultiply
            )
mg.add_edge({'use_rand_date': use_random_date,
             'min_year': min_year,
             'max_year': max_year},
            start_year, 
            rel=Rget_random_year,
            via=lambda use_rand_date, **kwargs : use_rand_date
            )
mg.add_edge({'random': use_random_date,
             'days_in_year': days_in_year},
            start_day, 
            rel=Rget_random_day,
            via=lambda random, **kw : random is True
            )
mg.add_edge({'random': use_random_date,
             'hours_in_day': hours_in_day},
            start_hour, 
            rel=Rget_random_hour,
            via=lambda random, **kw : random is True
            )
mg.add_edge({'start_year': start_year,
             'elapsed_hours': elapsed_hours, 
             'hours_in_year': hours_in_year,
             'hours_in_leapyear': hours_in_leapyear}, 
            num_leapyears,
            rel=Rcalc_num_leapyears,
            label='calc_num_leapyears',
            )
mg.add_edge(elapsed_hours, elapsed_hours, R.Rincrement, index_offset=1)

mg.add_edge({'elapsed_hours': elapsed_hours,
             'start_year': start_year, 
             'num_leapyears': num_leapyears,
             'start_day': start_day, 
             'start_hour': start_hour,
             'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year},
            year,
            rel=Rcalc_year,
            disposable=['elapsed_hours', 'num_leapyears'],
            index_via=lambda elapsed_hours, num_leapyears, **kw :
                       R.Rsame(elapsed_hours, num_leapyears)
            )
mg.add_edge({'elapsed_hours': elapsed_hours,
             'start_year': start_year, 
             'year': year,
             'num_leapyears': num_leapyears,
             'start_day': start_day, 
             'start_hour': start_hour,
             'hours_in_day': hours_in_day, 
             'hours_in_year': hours_in_year},
            day,
            rel=Rcalc_day, 
            disposable=['elapsed_hours', 'year', 'num_leapyears'],
            index_via=lambda elapsed_hours, year, **kw : 
                      R.Rsame(elapsed_hours, year)
            )
mg.add_edge({'elapsed_hours': elapsed_hours,
             'start_hour': start_hour, 
             'hours_in_day': hours_in_day},
            hour,
            rel=Rcalc_hour,
            )
mg.add_edge({'day': day,
             'hour': hour,
             'is_leapyear': is_leapyear, 
             'hours_in_year': hours_in_year,
             'hours_in_leapyear': hours_in_leapyear, 
             'hours_in_day': hours_in_day},
            hour_idx,
            rel=Rget_hour_index,
            disposable=['day', 'hour', 'is_leapyear'],
            index_via=lambda day, hour, is_leapyear, **kw : 
                      R.Rsame(day, hour, is_leapyear)
            )
mg.add_edge(year, is_leapyear, Rcalc_year_is_leapyear)

### Grid
# mg.add_edge({'A': conn_matrix,
#              'B': demand_vector},
#             state_matrix,
#             rel=Rlinear_solve, 
#             label='solve state matrix',
#             edge_props=['LEVEL', 'DISPOSE_ALL']
# )
mg.add_edge(demand_vector, state_matrix, R.Rfirst) #TODO: removing matrix solving due to singularities

mg.add_edge(state_matrix, 
            total_power_balance, 
            rel=lambda s1, **kwargs : sum(s1),
            index_offset=1
            )
mg.add_edge({'wasted': power_wasted,
             'balance': total_power_balance},
            power_wasted, 
            rel=lambda wasted, balance, **kwargs : wasted + min(0., balance), 
            index_offset=1,
            edge_props=['LEVEL', 'DISPOSE_ALL']
            )
mg.add_edge(state_matrix,
            num_loads, 
            rel=lambda s1, **kw : sum([a > 0 for a in s1]),
            )
mg.add_edge({'l': list_load_shedding,
             'num': num_loads},
            all_loads_shed, 
            rel=lambda l, num, **kwargs : len(l) >= num
            )

### Actors
mg.add_edge([A.demand for A in ACTORS if A not in UGs], 
            islanded_balance,
            rel=R.Rsum, 
            label='calc_island_balance',
            edge_props=['LEVEL', 'DISPOSE_ALL'],
            )
mg.add_edge({str(A) : A.is_failing for A in ACTORS} | {'names': names},
            failing_actors,
            rel=lambda *args, **kw : args,
            disposable=[str(A) for A in ACTORS],
            index_via=lambda *ar, **kw : R.Rsame(*[str(A) for A in ACTORS]),
            )
mg.add_edge({A.name for A in ACTORS}, names, Rsort_names)

keyed_receiving_nodes = {}
for ACTOR in ACTORS:
    #### Power Flow
    mg.add_edge({'state': ACTOR.state,
                 'demand': ACTOR.demand},
                ACTOR.is_overloaded, 
                rel=lambda state, demand, **kwargs : demand > state, 
                edge_props=['LEVEL', 'DISPOSE_ALL']
                )
    mg.add_edge(ACTOR.is_connected, ACTOR.state, 
                rel=lambda **kwargs : 0., 
                via=lambda s1, **kwargs : s1 is False
                )
    mg.add_edge({'x': state_matrix,
                 'name': ACTOR.name,
                 'names': names}, 
                ACTOR.state, 
                rel=Rget_state_from_matrix, 
                label=f'retrieve state of {str(ACTOR)}', index_offset=1
                )
    for SRC in ACTORS:
        if SRC is ACTOR:
            mg.add_edge({'receives_from': ACTOR.receives_from[str(SRC)], 
                         'is_conn': ACTOR.is_connected}, 
                        ACTOR.receiving_from[str(SRC)], 
                        rel=lambda receives_from, is_conn, **kwargs : 
                            receives_from and is_conn,
                        disposable=['is_conn'],
                        label=f'{str(ACTOR)} receiving from itself',
                        )
        else:
            mg.add_edge({'receives_from': ACTOR.receives_from[str(SRC)], 
                         'receiver_conn': ACTOR.is_connected, 
                         'provider_conn': SRC.is_connected}, 
                        ACTOR.receiving_from[str(SRC)], 
                        rel=Rcalc_if_receiving_power, 
                        label=f'{str(ACTOR)} receiving from {str(SRC)}',
                        disposable=['receiver_conn', 'provider_conn'],
                        index_via=lambda receiver_conn, provider_conn, **kw : 
                                  R.Rsame(receiver_conn, provider_conn)
                        )
        keyed_receiving_nodes.update({generate_connectivity_keyword(ACTOR, SRC) : 
                                      ACTOR.receiving_from[str(SRC)]})

    #### Failures and Load Shedding
    mg.add_edge({'random_fail': has_random_failure, 
                 'is_failing': ACTOR.is_failing},
                ACTOR.is_failing, 
                index_offset=1,
                rel=lambda **kw : False,
                label='set_no_failures',
                disposable=['is_failing'],
                via=lambda random_fail, **kw : random_fail is False,
                )
    mg.add_edge({'is_failing': ACTOR.is_failing,
                 'random_fail': has_random_failure, 
                 'p_fail': ACTOR.prob_failing,
                 'p_fix': ACTOR.prob_fixed},
                ACTOR.is_failing, 
                rel=Rdeterming_if_failing,
                label='determine_if_failing',
                index_offset=1,
                disposable=['is_failing'],
                via=lambda random_fail, **kwargs : random_fail is True,
                ) #TODO: Need a way to specify failures of connectivity (like BUS1/BUS2 line)

    mg.add_edge({'req_demand': ACTOR.req_demand,
                 'state': ACTOR.state,
                 'tol': tol},
                 ACTOR.is_load_shedding,
                 rel=Rdetermine_if_loadshedding,
                 disposable=['req_demand', 'state'],
                 index_via=lambda req_demand, state, **kw : 
                            R.Rsame(req_demand, state),
                )
    if ACTOR not in UGs:
        mg.add_edge({'is_failing': ACTOR.is_failing}, 
                    ACTOR.is_connected,
                    R.Rnot_any,
                    edge_props=['LEVEL', 'DISPOSE_ALL'],
                    )

mg.add_edge(keyed_receiving_nodes | {'names': names, 'key_sep': key_sep},
            conn_matrix, 
            rel=Rform_connectivity_matrix, 
            label='form connectivity matrix',
            disposable=[key for key in keyed_receiving_nodes],
            index_via=lambda **kwargs : R.Rsame(*[kwargs[key] for key in keyed_receiving_nodes])
            )

#### Demand vector
actor_lists = [UGs, BUSs, PVs, WINDs, BUILDINGs, GENs, BATTERYs]
s_dynamic = [[], [], ['supply'], ['supply'], [], [], ['cost']]
d_dynamic = [[], [], [], [], ['req_demand', 'max_demand'], [], ['benefit', 'max_demand']]

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

mg.add_edge(demand_sources,
            demand_vector,
            rel=Rmake_demand_vector,
            label='make_demand_vector',
            disposable=dynamic_sources,
            index_via = lambda **kwargs : 
                R.Rsame(*[kwargs[key] for key in dynamic_sources if key in kwargs]),
            )

### Busses

### Utility Grids
mg.add_edge([UG.is_connected for UG in UGs], 
            is_islanded, 
            rel=lambda *args, **kwargs : not any(R.extend(args, kwargs)),
            edge_props=['LEVEL', 'DISPOSE_ALL']
            )
for UG in UGs:
    mg.add_edge({'island': island_mode,
                 'failing': UG.is_failing}, 
                UG.is_connected,
                disposable=['failing'],
                rel=R.Rnot_any,
                )

### Solar
mg.add_edge(year, sunlight_filename, Rget_solar_filename)

mg.add_edge(sunlight_filename, sunlight_data, Rget_data_from_csv_file)

mg.add_edge({'csv_data': sunlight_data,
             'row': hour_idx,
             'col': sunlight_data_label}, 
            sunlight,
            rel=Rget_float_from_csv_data,
            index_via=lambda csv_data, row, **kw: R.Rsame(csv_data, row), 
            disposable=['csv_data', 'row']
            )
for PV in PVs:
    mg.add_edge({'conn': PV.is_connected,
                 'area': PV.area,
                 'efficiency': PV.efficiency,
                 'sunlight': sunlight},
                PV.supply, 
                rel=Rcalc_solar_supply,
                label='calc_solar_supply',
                disposable=['sunlight', 'conn'],
                index_via=lambda conn, sunlight, **kw : R.Rsame(conn, sunlight)
                )
    
### Wind
for W in WINDs:
    mg.add_edge({'area': W.rotor_area, 
                 'power_coef': W.power_coef, 
                 'velocity': wind_speed,
                 'density': air_density}, 
                W.supply, 
                rel=Rcalc_wind_supply,
                disposable=['velocity', 'density'],
                index_via=lambda density, velocity, **kw : R.Rsame(density, velocity)
                )

### Buildings
for B in BUILDINGs:
    mg.add_edge(B.req_demand, B.max_demand, R.Rfirst)
        
    mg.add_edge(B.type, B.building_filename, Rget_building_filename)

    mg.add_edge(B.building_filename, B.load_data, Rget_data_from_csv_file)

    mg.add_edge({'csv_data': B.load_data,
                 'row': hour_idx,
                 'col': B.normal_col_name}, 
                B.normal_load,
                rel=Rget_load_from_building_data
                )
    mg.add_edge({'csv_data': B.load_data, 
                 'row': hour_idx, 
                 'col': B.lights_col_name}, 
                B.lights_load,
                rel=Rget_load_from_building_data
                )
    mg.add_edge({'csv_data': B.load_data, 
                 'row': hour_idx, 
                 'col': B.equipment_col_name}, 
                B.equipment_load, 
                rel=Rget_load_from_building_data
                )
    mg.add_edge({'lights': B.lights_load,
                 'equipment': B.equipment_load},
                B.critical_load,
                rel=Rcalc_critical_load,
                edge_props=['LEVEL', 'DISPOSE_ALL']
                )
    #TODO: Need to implement a way for the critical load to be passed as well.
    mg.add_edge({'conn': B.is_connected, 
                 'normal': B.normal_load, 
                 'critical': B.critical_load,
                 'island': is_islanded}, 
                B.req_demand, 
                rel=Rdetermine_building_load, 
                edge_props=['LEVEL', 'DISPOSE_ALL'], 
                label='calc building demand'
                )


### Generators
mg.add_edge({'refuel_time': next_refuel_hour,
             'curr_hour': hour_idx, 
             'prob': prob_daily_refueling,
             'hours_in_day': hours_in_day}, 
            next_refuel_hour, 
            rel=Rcalc_next_time_for_refueling, 
            index_offset=1,
            disposable=['refuel_time', 'curr_hour'],
            index_via=lambda refuel_time, curr_hour, **kw : 
                      R.Rsame(refuel_time, curr_hour)
            )
for G in GENs:
    mg.add_edge({'fl': G.fuel_level, 
                 'tol': tol}, 
                G.out_of_fuel, 
                rel=lambda fl, tol, **kwargs :abs(fl) < tol
                )
    mg.add_edge({'init': G.starting_fuel_level, 
                 'max': G.fuel_capacity}, 
                G.fuel_level, 
                R.Rmin,
                )
    mg.add_edge({'refuel_time': next_refuel_hour, 
                 'curr_hour': hour_idx, 
                 'curr_level': G.fuel_level,
                 'max_level': G.fuel_capacity}, 
                G.fuel_level, 
                rel=Rcalc_generator_fuel_level, 
                disposable=['refuel_time', 'curr_hour', 'curr_level'], 
                index_offset=1,
                index_via=lambda refuel_time, curr_hour, curr_level, **kw : 
                          R.Rsame(refuel_time, curr_hour, curr_level)
                )
    mg.add_edge(G.max_output, G.supply, R.Rfirst)


### Batteries
for B in BATTERYs:
    mg.add_edge(B.state, B.is_charging, lambda s1, **kw : s1 < 0)

    mg.add_edge(B.max_output, B.supply, R.Rfirst)

    mg.add_edge({'state': B.state, 'level': B.charge_level, 
                 'max_level': B.charge_capacity, 'eff': B.efficiency}, 
                B.charge_level, 
                rel=Rcalc_battery_charge_level, 
                label='calc battery charge level',
                disposable=['level', 'state'],
                index_via=lambda state, level, **kw: R.Rsame(state-1, level)
                )
    mg.add_edge({'level': B.charge_level, 
                 'capacity': B.charge_capacity}, 
                B.soc,
                rel=lambda level, capacity, **kw : level / capacity, 
                edge_props=['LEVEL, DISPOSE_ALL']
                )
    mg.add_edge({'ug_cost': UGs[0].cost, 
                 'tol': tol, 
                 'level': B.charge_level, 
                 'capacity': B.charge_capacity, 
                 'factor': B.scarcity_factor}, 
                B.cost, 
                disposable=['level'],
                rel=Rcalc_battery_cost
                )
    mg.add_edge({'ug_cost': UGs[0].cost, 
                 'level': B.charge_level, 
                 'capacity': B.charge_capacity, 
                 'factor': B.scarcity_factor},
                B.benefit, 
                disposable=['level'],
                rel=Rcalc_battery_benefit,
                )    
    mg.add_edge({'level': B.charge_level,
                 'capacity': B.charge_capacity,
                 'max_rate': B.max_charge_rate,
                 'trickle_prop': batt_trickle}, 
                B.max_demand, 
                disposable=['level'],
                rel=Rcalc_battery_max_demand,
                )
