%% Import data from spreadsheet
% Script for importing data from the following spreadsheet:
%
%    Workbook: MG1v2 Report.xlsx
%    Worksheet: Matrix
%
% Auto-generated by MATLAB on 05-May-2019 15:40:34

%% Import A
%set options

opts = spreadsheetImportOptions("NumVariables", 12);

% Specify sheet and range
opts.Sheet = "Matrix";
opts.DataRange = "C3:N14";

% Specify column names and types
opts.VariableNames = ["B2_BT1", "B2_B1", "B1_B2", "B1_EP1", "B2_EP3", "B2_EP4", "B1_EP5", "B1_EP6", "B1_GEN1", "B1_GEN2", "B2_PV", "B1_UG"];
opts.SelectedVariableNames = ["B2_BT1", "B2_B1", "B1_B2", "B1_EP1", "B2_EP3", "B2_EP4", "B1_EP5", "B1_EP6", "B1_GEN1", "B1_GEN2", "B2_PV", "B1_UG"];
opts.VariableTypes = ["double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"];

%Save Variable Names
LoadVars = opts.VariableNames;

% Setup rules for import
opts.ImportErrorRule = "error";
opts = setvaropts(opts, [1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12], "TreatAsMissing", '');
opts = setvaropts(opts, [1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12], "FillValue", 0);

% Import the A matrix for Utility Grid Connected Mode
A_UG = readtable(Report_Workbook, opts, "UseExcel", false);

% Convert to output type
A_UG = table2array(A_UG);

% Import the A matrix for Islanded Mode
opts.DataRange = "C35:N46";

A_IM = readtable(Report_Workbook, opts, "UseExcel", false);

% Convert to output type
A_IM = table2array(A_IM);

% Import the Nodes Names
opts.DataRange = "C2:N2";
opts = setvartype(opts,'string');

nodes = readmatrix(Report_Workbook, opts, "UseExcel", false);

% Clear temporary variables
clear opts

%% Import b
opts = spreadsheetImportOptions("NumVariables", 1);

% Specify sheet and range
opts.Sheet = "Matrix";
opts.DataRange = "P3:P14";

% Specify column names and types
opts.VariableNames = "VarName16";
opts.SelectedVariableNames = "VarName16";
opts.VariableTypes = "double";

% Setup rules for import
opts.ImportErrorRule = "error";
opts = setvaropts(opts, 1, "TreatAsMissing", '');
opts = setvaropts(opts, 1, "FillValue", 0);

% Import the data
b = readtable(Report_Workbook, opts, "UseExcel", false);

% Convert to output type
b = table2array(b);

% Clear temporary variables
clear opts