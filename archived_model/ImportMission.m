%% Import Mission Importance


%% Setup the Import Options
opts = spreadsheetImportOptions("NumVariables", 6);

% Specify sheet and range
opts.Sheet = "Mission";
opts.DataRange = "A2:F6";

% Specify column names and types
opts.VariableNames = ["LoadName", "FacilityType", "AvgCriticalLoad", "AvgNormalLoad", "Critical", "CriticalPercent"];
opts.SelectedVariableNames = ["LoadName", "AvgCriticalLoad", "Critical"];
opts.VariableTypes = ["string", "string", "double", "double", "double", "double"];
opts = setvaropts(opts, [1, 2], "WhitespaceRule", "preserve");
opts = setvaropts(opts, [1, 2], "EmptyFieldRule", "auto");

% Import the data
Mission = readtable(Report_Workbook, opts, "UseExcel", false);


%% Clear temporary variables
clear opts

%% Add Load Shedding Precedence
% Add Mission/Load Variable  For Possible Load Shedding Precedence
Mission.Priority = Mission.Critical./Mission.AvgCriticalLoad;

% Sort by mission lost if load is shed
Mission = sortrows(Mission, {'Critical' 'Priority'});
% Optional Sort Priority Considered Below
% Mission = sortrows(Mission, {'Priority'});