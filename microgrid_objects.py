from constrainthg import Node
from enum import Enum, auto

class GridObject:
    """An entity on the grid that either receives or supplies power (made of a collection of nodes)."""
    def __init__(self, name: str, **kwargs):
        self.name = Node(f'name_{name}', name, description='name of object')
        self.is_connected = Node(f'is_connected_{name}', kwargs.get('is_connected', None), 
                                 description='object is connected to grid')
        self.is_failing = Node(f'is_failing{name}', kwargs.get('is_failing', False),
                                 description='object is failing')
        self.prob_failing = Node(f'prob_failing{name}', kwargs.get('prob_failing', 0.), 
                                 description='probability of object failing')
        self.prob_fixed = Node(f'prob_fixed{name}', kwargs.get('prob_fixed', 0.5), 
                                 description='probability of failing object getting fixed')
        self.is_overloaded = Node(f'is_overloaded_{name}', kwargs.get('is_overloaded', None), 
                                 description='more power is being demanded of an object than can be supplied')
        self.is_load_shedding = Node(f'{name} is load shedding', kwargs.get('is_load_shedding', False),
                                description='true if the object is deliberately disconnected from the grid')
        self.demand = Node(f'demand_{name}', kwargs.get('demand', None), description='load of object demanded from grid (W)')
        self.state = Node(f'state_{name}', kwargs.get('state', None), description='amount of power actively receiving (-) or providing (+) (W)')
        self.receives_from = {name: Node(f'{name} receives from itself', True, description=f'{name} receives power from itself (trivial)')}
        for source, val in dict(kwargs.get('receives_from', {})).items():
            self.add_source(source, val)
        self.receiving_from = {}
        for source, val in dict(kwargs.get('receiving_from', {})).items():
            self.add_active_source(source, val)
    
    def add_source(self, source, val: bool=True):
        """Creates a node indicating that the source GridObject is wired to provide power to this GridObject."""
        description = f'true if {str(self)} receives power from {str(source)}'
        self.receives_from[str(source)] = Node(f'{str(self)} receives from {str(source)}', val, description=description)

    def add_active_source(self, source, val: bool=None):
        """Creates a node indicating that the source GridObject actively providing power to this GridObject."""
        description = f'true if {str(self)} is actively receiving power from {str(source)}'
        self.receiving_from[str(source)] = Node(f'{str(self)} receiving from {str(source)}', val, description=description)

    def __str__(self):
        """Returns the name of the GridObject."""
        return self.name.static_value

class Generator(GridObject):
    """A grid object that can only supply power converted from some type of fuel."""
    def __init__(self, name: str, fuel_capacity: float, starting_fuel_level: float, max_output: float, 
                 efficiency: float, **kwargs):
        self.fuel_capacity = Node(f'fuel_capacity_{name}', fuel_capacity, description='max amount of fuel in generator (Gal)')
        self.starting_fuel_level = Node(f'starting_fuel_level_{name}', starting_fuel_level, description='starting fuel level in generator (Gal)')
        self.max_output = Node(f'max_output_{name}', max_output, description='max charge generator can output (kW)')
        self.efficiency = Node(f'efficiency_{name}', efficiency, description='efficiency for generator (Gph/kW)')
        self.fuel_level = Node(f'fuel_level_{name}', kwargs.get('fuel_level', None), description='amount of fuel in generator (Gal)')
        self.out_of_fuel = Node(f'out_of_fuel_{name}', kwargs.get('out_of_fuel', None), description='generator is out of fuel')
        super().__init__(name, demand=0., **kwargs)
    
class Battery(GridObject):
    """A grid object that can supply power or receive power for later distribution."""
    def __init__(self, name: str, charge_level: float, charge_capacity: float, max_output: float, 
                 efficiency: float, max_charge_rate: float, **kwargs):
        self.charge_level = Node(f'charge_level_{name}', charge_level, description='amount of charge in battery')
        self.charge_capacity = Node(f'charge_capacity_{name}', charge_capacity, description='max amount of charge in battery')
        self.wasted_charge = Node(f'wasted_charge_{name}', 0., description='charge wasted in battery')
        self.max_output = Node(f'max_output_{name}', max_output, description='max charge battery can output (kW)')
        self.efficiency = Node(f'efficiency_{name}', efficiency, description='efficiency of battery')
        self.max_charge_rate = Node(f'max_charge_rate_{name}', max_charge_rate, description='max charge rate for battery (kW/hr)')
        self.is_charging = Node(f'{name} is charging', description='true if battery is set for charging')
        super().__init__(name, demand=0., **kwargs)

class PhotovoltaicArray(GridObject):
    """A grid object that distributes power converted from solar energy."""
    def __init__(self, name: str, area: float, efficiency: float, **kwargs):
        self.area = Node(f'area_{name}', area, description='area of photovoltaic array (m^2)')
        self.efficiency = Node(f'efficiency_{name}', efficiency, description='efficiency of photovoltaic array')
        super().__init__(name, **kwargs)

class BUILDING_TYPE(Enum):
    """Sizes of buildings."""
    SMALL = 'SmallOffice'
    MEDIUM = 'MediumOffice'
    LARGE = 'LargeOffice'
    WAREHOUSE = 'Warehouse'

class Building(GridObject):
    """A grid object with a determined load."""
    def __init__(self, name: str, type: BUILDING_TYPE, **kwargs):
        self.type = Node(f'type_{name}', type, description='type of building')
        self.normal_load = Node(f'normal_load_{name}', kwargs.get('normal_load', None), 
            description='normal_load of building')
        self.critical_load = Node(f'critical_load_{name}', kwargs.get('critical_load', None), 
            description='critical_load of building')
        self.lights_load = Node(f'lights_load_{name}', kwargs.get('light_load', None), 
            description='lights_load of building')
        self.equipment_load = Node(f'equipment_load_{name}', kwargs.get('equipment_load', None),
            description='equipment_load of building')
        self.building_filename = Node(f'building_filename_{name}', kwargs.get('building_filename', None),
            description='filename for load data for the building')
        self.load_data = Node(f'load_data_{name}', kwargs.get('load_data', None),
            description='list of dictionaries for building load data')
        self.normal_col_name = Node(f'normal_col_name_{name}', kwargs.get('normal_col_name', 'Electricity:Facility [kW](Hourly)'),
            description='name of column with normal loads in building data')
        self.lights_col_name = Node(f'lights_col_name_{name}', kwargs.get('lights_col_name', 'InteriorLights:Electricity [kW](Hourly)'),
            description='name of column with lights loads in building data')
        self.equipment_col_name = Node(f'equipment_col_name_{name}', kwargs.get('equipment_col_name', 'InteriorEquipment:Electricity [kW](Hourly)'),
            description='name of column with equipment loads in building data')
        self.priority = Node(f'priority_{name}', kwargs.get('priority', 0.),
            description='priority rating of building, with higher being more critical')
        super().__init__(name, output=0., **kwargs)

## Modes
class MICROGRID_MODE(Enum):
    GRID_CONNECTED = auto()
    ISLANDED = auto()
    IMPORT_STATE = auto()