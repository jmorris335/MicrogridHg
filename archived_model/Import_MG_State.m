%% Import MG_State

MG_State = readtable(Report_Workbook, 'Sheet', 'MG_State', 'ReadVariableNames', true);

MG_State{:,:} = logical(MG_State{:,:} );
