from constrainthg import Node
from enum import Enum, auto

class GridActor:
    """An entity on the grid that either receives or supplies power 
    (made of a collection of nodes)."""
    def __init__(self, name: str, **kwargs):
        self.name = Node(
            f'name_{name}', 
            name, 
            description='name of object'
            )
        self.is_connected = Node(
            f'is_connected_{name}', 
            kwargs.get('is_connected', None), 
            description='object is connected to grid'
            )
        self.is_failing = Node(
            f'is_failing{name}',
            kwargs.get('is_failing', False), 
            description='object is failing'
            )
        self.prob_failing = Node(
            f'prob_failing{name}', 
            kwargs.get('prob_failing', 0.), 
            description='probability of object failing',
            )
        self.prob_fixed = Node(
            f'prob_fixed{name}', 
            kwargs.get('prob_fixed', 0.5), 
            description='probability of failing object getting fixed',
            )
        self.is_load_shedding = Node(
            f'{name} is load shedding', 
            kwargs.get('is_load_shedding', False),
            description='true if the object is deliberately disconnected from the grid',
            )
        self.state = Node(
            f'state_{name}', 
            kwargs.get('state', None), 
            description='amount of power actively receiving (-) or providing (+)',
            units='kW'
            )
        self.benefit = Node(
            f'benefit_{name}',
            kwargs.get('benefit', None),
            description=f'Benefit of meeting {name}\'s demand',
            units='$/kW'
            )
        self.cost = Node(
            f'cost_{name}',
            kwargs.get('cost', None),
            description=f'Cost of generating {name}\'s supply',
            units='$/kW'
            )
        self.req_demand = Node(
            f'req_demand_{name}',
            kwargs.get('req_demand', None),
            description=f'Minimum load required for the actor to operate',
            units='kW'
            )
        self.max_demand = Node(
            f'max_demand_{name}',
            kwargs.get('max_demand', None),
            description=f'Maximum load that the actor can receive',
            units='kW'
            )
        self.supply = Node(
            f'supply_{name}',
            kwargs.get('supply', None),
            description=f'Current energy that the actor can supply',
            units='kW'
            )
        
        self.receives_from = {name: Node(
            f'{name} receives from itself', 
            True, 
            description=f'{name} receives power from itself (trivial)'
            )}
        for source, val in dict(kwargs.get('receives_from', {})).items():
            self.add_source(source, val)
        self.receiving_from = {}
        for source, val in dict(kwargs.get('receiving_from', {})).items():
            self.add_active_source(source, val)

        #TODO: This default value is not used because default nodes get resolved for (CHg Issue #2)
        default_d_tuple = (name,*[kwargs.get(l, None) 
                                  for l in ['benefit', 'req_demand', 'max_demand']])
        self.demand_tuple = Node(
            f'demand_tuple_{name}',
            # None if None in default_d_tuple else default_d_tuple,
            None,
            description=f'Values for calculating {name} demand',
            )
        default_s_tuple = (name,*[kwargs.get(l, None) 
                                  for l in ['cost', 'supply']])
        self.supply_tuple = Node(
            f'supply_tuple_{name}',
            # None if None in default_s_tuple else default_s_tuple,
            None,
            description=f'Values for calculating {name} supply',
            )
        
    def add_source(self, source, val: bool=True):
        """Creates a node indicating that the source GridObject is wired 
        to provide power to this GridObject."""
        description = f'true if {str(self)} receives power from {str(source)}'
        self.receives_from[str(source)] = Node(
            f'{str(self)} receives from {str(source)}', 
            val, 
            description=description
            )

    def add_active_source(self, source, val: bool=None):
        """Creates a node indicating that the source GridObject actively 
        providing power to this GridObject."""
        description = f'true if {str(self)} is actively receiving power from {str(source)}'
        self.receiving_from[str(source)] = Node(
            f'{str(self)} receiving from {str(source)}', 
            val, 
            description=description
            )

    def __str__(self):
        """Returns the name of the GridObject."""
        return self.name.static_value
    
class Bus(GridActor):
    """A connection on the grid."""
    def __init__(self, name: str, **kwargs):
        defaults = dict(
            benefit = 0.,
            cost = 0.,
            req_demand = 0.,
            max_demand = 0.,
            supply = 0.,
            )
        kwargs = defaults | kwargs

        super().__init__(name, **kwargs)

class Generator(GridActor):
    """A grid object that can only supply power converted from some type 
    of fuel."""
    def __init__(self, name: str, fuel_capacity: float=None, 
                 starting_fuel_level: float=None, max_output: float=None, 
                 **kwargs):
        defaults = dict(
            benefit = 0.,
            req_demand = 0.,
            max_demand = 0.,
            )
        kwargs = defaults | kwargs

        self.fuel_capacity = Node(
            f'fuel_capacity_{name}',
            fuel_capacity, 
            description='max amount of fuel in generator', units='liters'
            )
        self.starting_fuel_level = Node(
            f'starting_fuel_level_{name}',
            starting_fuel_level, 
            description='starting fuel level in generator', units='liters'
            )
        self.max_output = Node(
            f'max_output_{name}',
            max_output, 
            description='max charge generator can output', units='kW'
            )
        self.consumption = Node(
            f'consumption_{name}',
            kwargs.get('consumpation', None),
            description='fuel consumption for generator', units='(L/h)'
            )
        self.max_consumption = Node(
            f'max_consumption_{name}',
            kwargs.get('max_consumpation', None), 
            description='max fuel consumption for generator', units='(L/h)'
            )
        self.fuel_level = Node(
            f'fuel_level_{name}',
            kwargs.get('fuel_level', None), 
            description='amount of fuel in generator', units='liters'
            )
        self.out_of_fuel = Node(
            f'out_of_fuel_{name}',
            kwargs.get('out_of_fuel', None), 
            description='generator is out of fuel'
            )
        super().__init__(name, **kwargs)
    
class Battery(GridActor):
    """A grid object that can supply power or receive power for later 
    distribution."""
    def __init__(self, name: str, charge_level: float=None, 
                 charge_capacity: float=None, max_output: float=None, 
                 efficiency: float=None, max_charge_rate: float=None, 
                 scarcity_factor: float=None, trickle_prop: float=None, 
                 **kwargs):
        defaults = dict(
            req_demand = 0.,
            )
        kwargs = defaults | kwargs

        self.charge_level = Node(
            f'charge_level_{name}',
            charge_level, 
            description='amount of charge in battery',
            units='kWh'
            )
        self.charge_capacity = Node(
            f'charge_capacity_{name}',
            charge_capacity, 
            description='max amount of charge in battery',
            units='kWh'
            )
        self.wasted_charge = Node(
            f'wasted_charge_{name}',
            0., 
            description='charge wasted in battery'
            )
        self.max_output = Node(
            f'max_output_{name}',
            max_output, 
            description='max power battery can output', units='kW'
            )
        self.efficiency = Node(
            f'efficiency_{name}',
            efficiency, 
            description='efficiency of battery'
            )
        self.max_charge_rate = Node(
            f'max_charge_rate_{name}',
            max_charge_rate, 
            description='max charge rate for battery', units='kW/hr'
            )
        self.scarcity_factor = Node(
            f'scarcity_factor_{name}',
            scarcity_factor,
            description='cost gain based on using an increasingly depleted battery'
            )
        self.trickle_prop = Node(
            f'trickle_prop_{name}',
            trickle_prop,
            description='SOC to reduce to trickle charge'
        )
        self.is_charging = Node(
            f'{name} is charging',
            kwargs.get('is_charging', False),
            description='true if battery is set for charging'
            )
        self.soc = Node(
            f'SOC_{name}',
            kwargs.get('soc', None),
            description='state of charge (0 to 1, with 1 being full)'
            )
        super().__init__(name, **kwargs)

class PhotovoltaicArray(GridActor):
    """A grid object that distributes power converted from solar energy."""
    def __init__(self, name: str, area: float=None, efficiency: float=None, **kwargs):
        defaults = dict(
            benefit = 0.,
            req_demand = 0.,
            max_demand = 0.,
            )
        kwargs = defaults | kwargs

        self.area = Node(
            f'area_{name}',
            area,
            description='area of photovoltaic array (m^2)'
            )
        self.efficiency = Node(
            f'efficiency_{name}',
            efficiency,
            description='efficiency of photovoltaic array'
            )
        super().__init__(name, **kwargs)

class WindTurbine(GridActor):
    """A grid actor that supplies power converted from wind energy."""
    def __init__(self, name: str, rotor_area: float=None, power_coef=None, **kwargs):
        defaults = dict(
            benefit = 0.,
            req_demand = 0.,
            max_demand = 0.,
            )
        kwargs = defaults | kwargs

        self.power_coef = Node(
            f'power_coef_{name}',
            None if power_coef is None else min(power_coef, 16/27),
            description='power coefficient of the turbines'
            )
        self.rotor_area = Node(
            f'rotor_area_{name}',
            rotor_area,
            description='area of turbine rotor',
            units='m^2'
            )

        super().__init__(name, **kwargs)

class BUILDING_TYPE(Enum):
    """Sizes of buildings."""
    SMALL = 'SmallOffice'
    MEDIUM = 'MediumOffice'
    LARGE = 'LargeOffice'
    WAREHOUSE = 'Warehouse'

class Load(GridActor):
    """An actor only capable of receiving power from the grid."""
    def __init__(self, name: str, **kwargs):
        defaults = dict(
            cost = float('inf'),
            supply = 0.,
            )
        kwargs = defaults | kwargs

        self.normal_load = Node(
            f'normal_load_{name}',
            kwargs.get('normal_load', None), 
            description='normal_load of building'
            )
        self.critical_load = Node(
            f'critical_load_{name}',
            kwargs.get('critical_load', None), 
            description='critical_load of building'
            )
        
        super().__init__(name, output=0., **kwargs)

class Building(Load):
    """A grid object with a determined load."""
    def __init__(self, name: str, type: BUILDING_TYPE=None, **kwargs):
        self.type = Node(
            f'type_{name}',
            type, 
            description='type of building'
            )
        self.lights_load = Node(
            f'lights_load_{name}',
            kwargs.get('light_load', None), 
            description='lights_load of building'
            )
        self.equipment_load = Node(
            f'equipment_load_{name}', 
            kwargs.get('equipment_load', None),
            description='equipment_load of building'
            )
        self.building_filename = Node(
            f'building_filename_{name}',
            kwargs.get('building_filename', None),
            description='filename for load data for the building'
            )
        self.load_data = Node(
            f'load_data_{name}',
            kwargs.get('load_data', None),
            description='list of dictionaries for building load data'
            )
        self.normal_col_name = Node(
            f'normal_col_name_{name}', 
            kwargs.get('normal_col_name', 'Electricity:Facility [kW](Hourly)'),
            description='name of column with normal loads in building data'
            )
        self.lights_col_name = Node(
            f'lights_col_name_{name}', 
            kwargs.get('lights_col_name', 'InteriorLights:Electricity [kW](Hourly)'),
            description='name of column with lights loads in building data'
            )
        self.equipment_col_name = Node(
            f'equipment_col_name_{name}', 
            kwargs.get('equipment_col_name', 'InteriorEquipment:Electricity [kW](Hourly)'),
            description='name of column with equipment loads in building data'
            )
        super().__init__(name, **kwargs)

## Modes
class MICROGRID_MODE(Enum):
    GRID_CONNECTED = auto()
    ISLANDED = auto()
    IMPORT_STATE = auto()