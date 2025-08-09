from model.microgrid import mg as general_hg
from validation.spanagel_hg import sg as spanagel_hg
from aux.plotter import *

# Note that the simulation is not fast, please be patient.

inputs = {
    'use_random_date': False,
    'start_day': 100,
    'start_year': 2005,
    'start_hour': 6,
    'has_random_failure': False,
    'island_mode': True,
    'time_step': 3600,
}
plot_general_study(general_hg, **inputs)


inputs_validation = {
    'valid_data_path': 'src/validation/Spanagel_Test_29APR-1MAY2025.csv',
    'use_random_date': False,
    'start_day': 119,
    'start_year': 2025,
    'start_hour': 15,
    'has_random_failure': False,
    'time_step': 60,
}
plot_validation_study(spanagel_hg, inputs_validation)
