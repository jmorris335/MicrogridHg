% MG_LP_Test_v6
% Added Loss of PV power
% Added Loss of Lines to Loads
% Changed Battery Variable to Structure Array to Capture all Battery Data
% Added check for battery output capacity being exceeded
%
% Updated Critical load assumptions from all Equipment Loads to 1/2 of
% lighting loads plus 2/3 of equipment loads
% Added Fuel Storage, Use, and Refueling to Generators
% Renamed Variables for generators from G1/G2 to GEN1/GEN2 for clarity

% Added Importation of Mission Importance Data
% Added Load Shedding. Loads are shed in precedence of Load Importance to
% minimize Mission Impact

% MG_LP_Test_v7
% Added Loss of Generators when fuel is exhuasted
% Added Loss of ESS when battery is exhausted
% Modified and cleaned up looping to create A2 matrix in one block for
% easier debugging
% A shitload of debugging to properly allow for multiple failures
% Added Results Calculations

% MG_LP_Test_v8
% Iterative Looping for Monte Carlo Simulations
% v8_1
% Charging/Discharging Efficiency included
% Write Table with Model Inputs for Each Run
% Changes some variable names/types for ease of readability and code change
% Random year now random for each MC Run

% MG_LP_Test_v9
% Added Random Failure for Monte Carlo Simulations via MG_Failure_State.m
% v9.1
% Generator fueling delay added
% v9.2
% Fixed mistake in way the summary MI is calculated
% EP3/4 are Critical Loads if BUS1/2 Connection is lost even with utility
% power
% v9.3 - DVB
% Fixed an issue with the battery being able to discharge below 0
% Added a graph
% Increased graph line thickness
% Added variable to globally change what Excel workbook is referenced
% Currently set the timestep to 1 rather than random.
% Added calculation of total load per step of time and associated graph.

% MG_LP_Test_V10
% Updates to fix concerns raised in journal manuscript review round #1
% Added import of energy parameters from Excel workbook
% Put in switches for auto mode vs manual mode to select how the software
% runs
% Can turn plots on or off
% Found some issues with how data was being imported and fixed it
%% Clear Workspace
clear
tic

%% Set Model Options

%Set if you want the prompts or to do a specific pre-coded scenario
Auto_Mode = true;
%%This is the auto settings:
    year.run = 2000; %2000-2009 available
    MG_Mode = "Islanded"; %"Import State"; %Can be: Grid Connected, Islanded, Import State -- Import State will then read from an Excel workbook.
    failure.mode = false; %Sets if a random failure mode is allowed or if only failures from the initial condition and import state, if used, are applied.
    Islanded = true; %make this true if at any time during the simulation we'll be in island mode -- basically manually check the Excel workbook if using Import State.

%choose random time of year to start time step, unless ts is specified
Random_Date = true; %set this to true if you want it to randomize where the start date/time is in a year
Start_Date = 2; %only matters if you are NOT using a random date.  This is referencing the timestep and in incriments of the imported load and solar data.  Start on timestep 2 at minimum.

%Do you want plots to be output?
Plots_or_Not = false;

%Set report workbook location - DVB

Report_Workbook = "MG1v2 Report_DVB_second_graph.xlsx"; %This is where you can change the scenario

%Set Number of Iterations for Monte Carlo Simulation
MC = 1000;

% Set Scenario Name for Settings Summary Output File
MGSettings = {'Scenario', 'Two week Islanded Operation. Failure Allowed.'};

% Set what is failing if the failure scenario is on
failure.line = {'B1_GEN1' 'B1_GEN2'};%'B1_B2' 'B2_B1'}; %Potential options: {'B2_BT1','B2_B1','B1_B2','B1_EP1','B2_EP3','B2_EP4','B1_EP5','B1_EP6','B1_GEN1','B1_GEN2','B2_PV','B1_UG'}
%NOTE: for the two buses (B1 and B2), need to fail both B1_B2 and B2_B1


%Set year of solar data to import, set as either year or "TY" for a typical
%meteorological year
if Auto_Mode == false

    list = "TY";
    for i=0:9
        list(i+2)=2000 + i;
    end
    list(12) = "Random";
    [index,sel] = listdlg('ListString',list,'SelectionMode','single',...
        'ListSize',[150,170]);
    if sel == 0
        year.sel = "TY";
        year.run = "TY";
        disp("No Selection Made, Typical Year Assumed");
    elseif sel == 1 && index <= 11
        year.run = (list(index));
        year.sel = list(index);
    elseif sel == 1 && index == 12
        year.run = randi([2000,2009]);
        year.sel = "Random";
    end

    if ~isnan(str2double(year.run))
       year.run = str2double(year.run);
    end

    clear list sel index

else 
    year.sel = year.run;
    
    
end


%Set Grid Mode
if Auto_Mode == false
    
    list = ["Grid Connected","Islanded","Import State"];
    [index,sel] = listdlg('ListString',list,'SelectionMode','single',...
        'ListSize',[150,100],'InitialValue', 2);
    if sel == 0
        MG_Mode = list(1);
        disp("No Selection Made, "+MG_Mode+" Mode Assumed");
    elseif sel == 1
        MG_Mode = list(index);
    end
    clear list sel index
else
    
end



%Set if random failure mode is used for Monte Carlo simulation

if Auto_Mode == false
    list = ["Yes","No"];
    [index,sel] = listdlg('ListString',list,'SelectionMode','single',...
        'ListSize',[150,100],'PromptString','Random Failure Mode?');
    if sel == 0
        failure.mode = false;
        disp("Assumed no random failure");
    elseif sel == 1
        if index == 1
            failure.mode = true;
        elseif index == 2
            failure.mode = false;
        end
    end
    clear list sel index
    
else
    
end




%set Islanded Mode Simulation to false. Set true if islanded occurs during
%any part of the simulation
if Auto_Mode == false
    IM_sim = false;
else
    
end

%%%%%% 
%% Import Energy
run ImportEnergy % Go to the spreadsheet to import energy info

%Record Summary of Settings for Output File
MGSettings = [MGSettings;...
    {'PV Area',  PV.Area;...
    'PV Eff', PV.eff; 'Gen Capacity', Gens(1).Capacity;...
    'Gen Storage' , Gens(1).Storage; 'Gen Refueling', Gens(1).Refuel;...
    'Refueling Pr' , Gens(1).PrRefuel;...
    'Same Fuel Supply' , Gens(1).RefuelTogether
    'BT1 Capacity' , BT1.Capacity; 'BT1 Output' , BT1.Output}];

%% Import A and b Matrix Values -- this is the control logic schema from the Matrix tab from the Excel workbook
run Import_A_b 

%% Import Solar Data

if strcmp(year.run, "TY")
    disp("Run Simulation for Typical Year")
    run ImportTY_NPS
elseif isnumeric(year.run)
    disp("Run Simulation for year "+year.run);
    run Import2000_NPS
end
%% Import Load Data and Mission Importance
run ImportLoads
run ImportMission

%% Setup Results Variables
Results = table();

%Mission Impacted (lost)
Results.MI(1:MC) = 0;
%Time that Battery was Exhausted
Results.BatteryExhausted(1:MC) = 0;
%Time that GEN1 was out of fuel
Results.GEN1_Fuel_Empty(1:MC) = 0;
%Time that GEN2 was out of fuel
Results.GEN2_Fuel_Empty(1:MC) = 0;
%Load Shedding
Results.LoadShed(1:MC,:) = zeros(MC,5);
%Time Load Not Met
Results.ShedHours(1:MC,:) = zeros(MC,5);

%% Setup the microgrid state table.
% This is a logical table for the functional state of each element

%Create table with state of the microgrid through the simulation period and
%set time steps to run as number of time steps in imported data. If the
%general grid connected or island mode operation is run, assume two weeks
if strcmp(MG_Mode , "Import State")
    run Import_MG_State
    steps = height(MG_State);
else
    % number of steps, hourly step size
    steps = 24*14;
    tblsize = length(A_UG);
    vartype(1,1:tblsize) = {'logical'};
    MG_State = table('Size',[1, tblsize], 'VariableTypes', vartype, 'VariableNames', LoadVars);
    clear vartype tblsize;
    MG_State(1:steps,:) = {true};
    if strcmp(MG_Mode , "Islanded")
        MG_State.B1_UG(1:steps) = false;
    end
end
MG_State_Initial = MG_State;

%Sets the total microgrid load variable at the start - DVB

power_sum(steps) = 0;


for iteration = 1:MC
%% Setup the microgrid initial conditions
%Reset MG_State
MG_State = MG_State_Initial;
% If a failure simulation, set MG_State for each run stochastically
if failure.mode
    run MG_Failure_State
end
%number of hours in a year. Used to loop to start of year if end reached
loop = 365*24;


if Random_Date == false
    ts = Start_Date; %This is to set the start at 1 January. - DVB -- NOTE: set it forward to ts=2 because ts=1 may be the header!
else
    ts = randi([1,loop]); % - This makes it pick a random start day/time in the year.
end
    


%Assume Battery at full capacity at the start of the simulation
BT1_Charge = zeros([1,steps]);
BT1_Charge(1) = BT1.Capacity;
%Capture charge lost when battery capacity limit is reached
BT1_lost = zeros([1,steps]);
%Setup Fuel Calc
Gens(1).Fuel = zeros([1,steps]);
Gens(1).Fuel(1) = Gens(1).Storage;
Gens(2).Fuel = zeros([1,steps]);
Gens(2).Fuel(1) = Gens(2).Storage;
Gens(1).NextFuel = Gens(1).Refuel;
Gens(2).NextFuel = Gens(2).Refuel;
% Table to Capture Load Shedding
LoadShed = table;
LoadShed.Overload([1,steps]) = false;
LoadShed.EP1(:) = 0;
LoadShed.EP3(:) = 0;
LoadShed.EP4(:) = 0;
LoadShed.EP5(:) = 0;
LoadShed.EP6(:) = 0;
% If the year is random, then import solar data for the year

if Auto_Mode == false
    if year.sel == "Random"
        year.run = randi([2000,2009]);
        run Import2000_NPS;
    end
else
    
end

disp("Iteration " + iteration + " for year " + year.run);
%% Run Linear Solver to find flows
%Initialize x with size of array
x = zeros(numel(b),steps);

%Bus balances
b(1:3) = 0;

%Find Variable Positions of Loads in Data
pos.EP = contains(LoadVars,'EP');
pos.Gens = contains(LoadVars, 'GEN');
pos.GEN1 = nodes == 'GEN1';
pos.GEN2 = nodes == 'GEN2';
pos.B2B1 = contains(LoadVars,'B2_B1');
pos.B1B2 = contains(LoadVars,'B1_B2');
pos.BT1 = contains(nodes,'BT1');
%Run Loop
for n=1:steps
    Overload.BT1 = false;
    Overload.Gens = false;
    
    % If fuel exhausted, then generators are nonoperational
    MG_State.B1_GEN1(n) =  MG_State.B1_GEN1(n) * (Gens(1).Fuel(n) > 0);
    MG_State.B1_GEN2(n) =  MG_State.B1_GEN2(n) * (Gens(2).Fuel(n) > 0);
    
    if MG_State.B1_UG(n) == true
        %Set A Matrix to default UG connected state
        A2 = A_UG;
        %Generators are off in grid connected mode
        b(4:5) = 0;
        %Battery flow is zero if fully charged or charging if not. Charge
        %rate slows after 80% charge
        if BT1_Charge(n) >= BT1.Capacity
            b(6) = 0;
        elseif BT1_Charge(n) >= .8*BT1.Capacity
            b(6) = .05*BT1.Capacity;
        else
            b(6) = .2*BT1.Capacity;
        end
        
        %Calculated building load demands
        b(7) = RefSmallOfficeLoads.Normal(ts); %EP1 Load is Small Office
        b(8) = RefSmallOfficeLoads.Normal(ts); %EP3 Load is Small Office
        b(9) = RefMedOfficeLoads.Normal(ts); %EP4 Load is Medium Office
        b(10) = RefLargeOfficeLoads.Normal(ts); %EP5 Load is Large Office
        b(11) = RefWarehouseLoads.Normal(ts); %EP6 Load is Warehouse 
        
        if MG_State.B2_B1(n) == false
            % These loads are severed from utility power if this occurs,
            % change to critical loads only
            b(8) = RefSmallOfficeLoads.Critical(ts); %EP3 Load is Small Office
            b(9) = RefMedOfficeLoads.Critical(ts); %EP4 Load is Medium Office
        end

    end
    
    if MG_State.B1_UG(n) == false
        %Islanded mode occured during some point of simulation
        IM_sim = true;
        %Reset A to IM Defaults
        A2 = A_IM;

        %No grid connection
        b(4) = 0;
        %Generators are equally sized
        b(5) = 0;
        %Islanded, battery used as little as possible to maximize charge to
        %maximize resiliency
        b(6) = 0;
        
        %Calculated building loads
        b(7) = RefSmallOfficeLoads.Critical(ts); %EP1 Load is Small Office
        b(8) = RefSmallOfficeLoads.Critical(ts); %EP3 Load is Small Office
        b(9) = RefMedOfficeLoads.Critical(ts); %EP4 Load is Medium Office
        b(10) = RefLargeOfficeLoads.Critical(ts); %EP5 Load is Large Office
        b(11) = RefWarehouseLoads.Critical(ts); %EP6 Load is Warehouse
    end
    
    %Calculated PV output. Output is zero if line failure occured
    b(12)= (-1/1000) * PV.Area * PV.eff * solar(ts) * MG_State.B2_PV(n);
    
    %Determine if any load paths have failed
    if ~all(MG_State{n,pos.EP})
        % Capture Load Shed as Result of Failure
        LoadShed{n,2:6} = ~MG_State{n,pos.EP}.*b(7:11)';
        %If load paths has failed, then set load to zero on that path
        b(7) = b(7)*MG_State{n,'B1_EP1'};
        b(8) = b(8)*MG_State{n,'B2_EP3'};
        b(9) = b(9)*MG_State{n,'B2_EP4'};
        b(10) = b(10)*MG_State{n,'B1_EP5'};
        b(11) = b(11)*MG_State{n,'B1_EP6'};

    end
        
    %Modify A if there is a loss of B2_B1/B1_B2 Line
    if MG_State.B2_B1(n) == false
        A2(1,pos.B1B2) = 0;
        A2(2,pos.B2B1) = 0;
        A2(6,:) = pos.B2B1;
    end

    %Modify A for loss of generator
    %Only applies if UG is not connected
    if MG_State.B1_UG(n) == false
        if MG_State.B1_GEN1(n) == false
            A2(5,:) = pos.GEN1;
        b(5) = 0;
        end
        if MG_State.B1_GEN2(n) == false
            A2(5,:) = pos.GEN2;
            b(5) = 0; %JM: Should this be A2(6,:) and b(6)?
        end
        if (MG_State.B1_GEN1(n) == false && MG_State.B1_GEN2(n) == false)
            A2(5,:) = pos.GEN1;
            b(5) = 0;
            A2(6,:) = pos.GEN2;
            b(6) = 0;
        end
    end
        
    %Initial Solve
    x(:,n) = linsolve(A2,b);
        
    %Determine if generator demand exceeds generator capacity
    Gen_Demand = -x(pos.Gens,n);

    if any(Gen_Demand > [Gens.Capacity]')
        %If the B2 to B1 Buss line or BT1 line is failed, or battery is
        %exhausted cannot utilize ESS to make up generator capacity
        if MG_State.B2_B1(n) == false || MG_State.B2_BT1(n) == false ...
                || BT1_Charge(n) < 0
            % Below line was useful for debugging in single runs. Commented out
            % disp("Gens Overloaded at time step "+n)
            Overload.Gens = true;
        else
            %Otherwise set Generators at full output, use battery to
            %make up unmet demand
            A2(6,:) = pos.Gens & MG_State{n,:};
            b(6) = -MG_State{n,{'B1_GEN1' 'B1_GEN2'}}*[Gens.Capacity]';
            x(:,n) = linsolve(A2,b);
        end
    %If Generator demand is negative, then generator output is zero,
    %charge batteries with excess PV generation
    elseif any(Gen_Demand < 0)
        A2(6,:) = pos.Gens;
        b(6) = 0;
        x(:,n) = linsolve(A2,b);
    end
    
    % Check for Battery Output Exceeded
    % Add 0.1 Due to Rounding Errors in Linear Solver
    if -x(contains(LoadVars,'BT1'),n) - 0.01 > BT1.Output * (BT1_Charge(n) > 0)
        Overload.BT1 = true;
        % Below line was useful for debugging in single runs. Commented out
        % disp("Battery Output Exceeded at time step "+n)
    end
    
    % Check if load shedding is required.
    bShed = b;
    xO = zeros(numel(b),numel(Mission.LoadName)+1);
    xO(:,1) = x(:,n);
    for i=1:numel(Mission.LoadName)
        % Enumerate through loads until no overload is present
        if ~any([Overload.BT1 Overload.Gens])
            break
        end
        % Set Load i to 0
        LoadShed.Overload(n) = true;
        bShed(7) = bShed(7)*~(Mission.LoadName(i) == 'EP1');
        bShed(8) = bShed(8)*~(Mission.LoadName(i) == 'EP3');
        bShed(9) = bShed(9)*~(Mission.LoadName(i) == 'EP4');
        bShed(10) = bShed(10)*~(Mission.LoadName(i) == 'EP5');
        bShed(11) = bShed(11)*~(Mission.LoadName(i) == 'EP6');
        
        xO(:,i+1) = linsolve(A2,bShed);
        % If load shedding resulted in no change to overload, then skip
        % to next load. Prevents shedding unnecessary loads when busses are
        % seperated or load was shed due to a failed line
        if  (Overload.Gens && all(xO(pos.Gens,i) == xO(pos.Gens,i+1)))...
                || (Overload.BT1 && (xO(pos.BT1,i) == xO(pos.BT1,i+1)))
            bShed(7:11) = bShed(7:11) + b(7:11) .* (Mission.LoadName(i) == {'EP1' 'EP3' 'EP4' 'EP5' 'EP6'})';
            continue
        end
        
        % If load sheds to the point that the generators are now charging
        % the battery, set battery charging to zero
        if Overload.BT1 && (xO(pos.BT1,i+1) > 0) && ...
                any(xO(pos.Gens,i+1) > 0)
            A2(6,:) = pos.BT1;
            bShed(6) = 0;
            xO(:,i+1) = linsolve(A2,bShed);
            % And if that leads to the generators now running in reverse...
            Gen_Demand = -xO(pos.Gens,i+1);
            if any(Gen_Demand < 0)
                A2(6,:) = pos.Gens;
                xO(:,i+1) = linsolve(A2,bShed);
            end
        end


        % Capture Load Shed
        LoadShed{n,Mission.LoadName(i)} = x(nodes == Mission.LoadName(i),n);
        
        % Check if overload is clear
        Gen_Demand = -xO(pos.Gens,i+1);
        if all(Gen_Demand <= [Gens.Capacity]')
            Overload.Gens = false;
        end
        if ~(-xO(pos.BT1,i+1) - .01 > BT1.Output * (BT1_Charge(n) > 0))
            Overload.BT1 = false;
        end
        
        x(:,n) = xO(:,i+1);
    % Iterate to next load if additional shedding is required
    end
    
    %Calculate battery state
    if MG_State{n,pos.BT1}
        if x(1,n)>0 % charging
            %Decrease charge by efficiency
            BT1_Charge(n+1) = BT1_Charge(n)+x(1,n)*BT1.Efficiency;
        else
            %Increase demand by efficiency
            BT1_Charge(n+1) = BT1_Charge(n)+x(1,n)/BT1.Efficiency;
        end
    elseif ~MG_State{n,pos.BT1}
         BT1_Charge(n+1) = BT1_Charge(n);
    end
    
    %Prevent Overcharging
    if BT1_Charge(n+1) > BT1.Capacity
        %Capture lost charge
        BT1_lost(n) = BT1_lost(n) + BT1_Charge(n+1) - BT1.Capacity;
        %Set the charge capacity to limit to 100%
        BT1_Charge(n+1) = BT1.Capacity;
    end
    
    %Generator Refueling
    if Gens(1).NextFuel == n
        % Pr of Refueling each day
        if rand() > Gens(1).PrRefuel
            Gens(1).NextFuel = Gens(1).NextFuel + 24;
            if Gens(2).RefuelTogether
                Gens(2).NextFuel = Gens(2).NextFuel + 24;
            end
        else
            % Reset Fuel Level for GEN1
            Gens(1).Fuel(n) = Gens(1).Storage;
            Gens(1).NextFuel = Gens(1).NextFuel + Gens(1).Refuel;
            if Gens(2).RefuelTogether
                % And also for GEN2 if supplied together
                Gens(2).Fuel(n) = Gens(2).Storage;
                Gens(2).NextFuel = Gens(2).NextFuel + Gens(2).Refuel;
            end
        end
    end
    if Gens(2).RefuelTogether == false && Gens(2).NextFuel == n
        % Pr of Refueling each day
        if rand() > Gens(2).PrRefuel
            Gens(2).NextFuel = Gens(2).NextFuel + 24; 
        else
            % Reset Fuel Level for GEN2
            Gens(2).Fuel(n) = Gens(2).Storage;
            Gens(2).NextFuel = Gens(2).NextFuel + Gens(2).Refuel;
        end
    end
    
    % Update Fuel Levels
    Gens(1).Fuel(n+1) = Gens(1).Fuel(n) + x(pos.GEN1,n).* Gens(1).Efficiency;
    Gens(2).Fuel(n+1) = Gens(2).Fuel(n) + x(pos.GEN2,n).* Gens(2).Efficiency;
    % loop iteration to next time step
    ts=ts+1;
    if ts > loop
        ts=1;
    end
    
    %fix negative battery charge states - DVB
    if BT1_Charge(n) < 0 
       BT1_Charge(n) = -0.1;
    end
    

   
end

%% Calculate Results of Each Iteration

%Calculate Mission Impacted (lost)
TN = (sortrows(Mission,'LoadName'));
% TN is temporary Table to reorder based on name so both vectors for below
% calculation are ordered by load name in ascending order
Results.MI(iteration) = sum(LoadShed{:,2:end}>0) * TN.Critical;
%Time that Battery was Exhausted
Results.BatteryExhausted(iteration) = sum(BT1_Charge < 0);
%Time that GEN1 was out of fuel
Results.GEN1_Fuel_Empty(iteration) = sum(Gens(1).Fuel < 0);
%Time that GEN2 was out of fuel
Results.GEN2_Fuel_Empty(iteration) = sum(Gens(2).Fuel < 0);
%Load Shedding
Results.LoadShed(iteration,:) = sum(LoadShed{:,2:end}) ;
Results.ShedHours(iteration,:) = sum(LoadShed{:,2:end} > 0);
end


%% Output to files
% Output summary files for Monte Carlo Simulation
if MC > 1
    %Write Results Table to File
    writetable(Results, 'MG_Sim_MC_Results.csv');
    %Write the MG_State Input Used for Reference
    writetable(MG_State_Initial, 'MG_Sim_MC_MG_State.csv');
    %Write Settings Used for BT1, Generator, PV Array Sizes/Outputs,
    %Iterations
    MGSettings(end+1,:) = {'Iterations', MC};
    MGSettings(end+1,:) = {'Year', year.sel};
    writecell(MGSettings, 'MG_Sim_MC_Settings.csv');
    
    % Calculate Summary of MC Results
    Summary = table();
    Summary.MI = mean(Results.MI);
    Summary.BatteryExhausted = mean(Results.BatteryExhausted,1);
    Summary.GEN1_Fuel_Empty = mean(Results.GEN1_Fuel_Empty,1);
    Summary.GEN2_Fuel_Empty = mean(Results.GEN2_Fuel_Empty,1);
    Summary.LoadShed = mean(Results.LoadShed,1);
    Summary.ShedHours = mean(Results.ShedHours,1);
    Summary{2,:} = max(Results.Variables);
    Summary{3,:} = min(Results.Variables);
    Summary{4,:} = std(Results.Variables,1);
    Summary{5,:} = size(Results.Variables,1);
    Summary.Properties.RowNames = {'mean' 'max' 'min' 'std' 'size'};
    %Write Summary Table to File
    writetable(Summary, 'MG_Sim_MC_Summary.csv', 'WriteRowNames', true);
    
    disp("Mean Ms "+mean(Results.MI)+" Standard Deviation "+std(Results.MI))
    
    % If only one run, then output detailed hourly data of the single run
elseif MC == 1
    %Output x (power flows of each line) to file
    writematrix(x,'MG_LP_Test_Output.csv','Delimiter',',','QuoteStrings',true);
    
    %Create table of power flows
    xT = array2table(transpose(x),  'VariableNames', LoadVars);
    xTarray = table2array(xT);
    %Create timestamps for each timestep as DateTime variable
    if isnumeric(year.run)
        xT.DateTime = datetime(year.run,1,1,(ts-steps):(ts-1),0,0)';
    else
        xT.DateTime = datetime(1900,1,1,(ts-steps):(ts-1),0,0)';
    end
    %Move DateTime variable to first variable for better data export
    xT = xT(:,[end,1:end-1]);
    %Add Battery Charge and charge lost when capacity is reached to table
    xT.BT1_Charge = BT1_Charge(1:steps)';
    xT.BT1_Lost = BT1_lost(1:steps)';
    
    %Write Table to file
    writetable(xT, 'MG_Sim_Output_Table.csv');
    
        %calculate total power load of microgrid - DVB

    for p = 1:steps
        %m=4;
        for m=4:9
            power_sum(p) = power_sum(p) + xTarray(p,m);
            m = 1 + m;
        end
        disp("Power Sum for Step "+p+" is "+power_sum(p));
        %power_sum(p) = xTarray(4,p)+ xTarray(5,p) + xTarray(6,p) + xTarray(7,p) + xTarray(8,p);
        p = p + 1;
    end
end
%% Write Summary to Console
% Added if statement to Console Output and Plots on/off

if MC == 1
    disp(['Maximum PV Output is ', num2str(-min(x(11,:)))]);
    disp(['Mean PV Output is ', num2str(-mean(x(11,:)))]);
    for i = 4:8
        disp(['Maximum Load ', LoadVars{i},' is ', num2str(max(x(i,:)))]);
        disp(['Mean Load ', LoadVars{i},' is ', num2str(mean(x(i,:)))]);
    end
    clear i
    disp("Unable to meet loads for "+sum(BT1_Charge < 0)+" out of "+steps+" hours")
end
%% Plot Results

if Plots_or_Not == true

    line_thickness = 3; %change the thickness of the lines in the plots - DVB

    if MC == 1
        %Plot all flows except those between B1 and B2
        figure(1)
        plot(transpose(x([1,4:12],:)), 'LineWidth', line_thickness);
        title("Power Flow in Microgrid");
        legend(LoadVars([1,4:12]),'Interpreter','none');
        xlabel("hrs")
        ylabel("kW")
        set(gca,'FontSize', 20)
        %Only plot Battery data if Islanded Mode was encountered during simulation,
        %otherwise battery was always charged and plotting data for inspection
        %is unneccessary
        if IM_sim == true

            %Plot Battery State Data
            figure(2)
            yyaxis left
            plot(BT1_Charge, 'LineWidth', line_thickness)
            %title("Battery Charge Level");
            legend("BT1");
            xlabel("hrs")
            ylabel("Battery Charge (kW*h)")
            %refline(0,0)
            yyaxis right
            plot(x(1,:), 'LineWidth', line_thickness)
            ylabel("Battery Power Flow (kW)")
            %legend("BT1","B2_BT1",'Interpreter','none')
            legend("BT1 Charge State","BT1 Power Flow")
            set(gca,'FontSize', 20)
            %Plot Generator Fuel
            figure(3)
            plot([Gens(1).Fuel; Gens(2).Fuel]', 'LineWidth', line_thickness)
            title("Generator Fuel Level");
            xlabel("hrs")
            ylabel("Fuel Level (gal)")
            legend("GEN1","GEN2")
            set(gca,'FontSize', 20)

            %Plot Generator Fuel and Battery Charge Level - DVB
            figure(4)
            %plot([Gens(1).Fuel; BT1_Charge', 'LineWidth', line_thickness)
            %title("ESS Storage and Generator Fuel Storage");
            yyaxis left
            plot(BT1_Charge, 'LineWidth', line_thickness)
            xlabel("hrs")
            ylabel("Battery Charge (kW*h)")
            ylim([0,3000])
            %refline(0,0)
            yyaxis right
            plot([Gens(1).Fuel; Gens(2).Fuel]', 'LineWidth', line_thickness)
            ylabel("Fuel Level (gal)")
            ylim([1000,2800])
            legend("BT1","GEN1","GEN2")
            set(gca,'FontSize', 20)

            %Plot total load - DVB

            figure(5)
            plot(power_sum, 'LineWidth', line_thickness)
            %title("Power Consumption");
            xlabel("hrs")
            ylabel("Total kW*h Supplied")
            legend("kW*h Supplied")
            set(gca,'FontSize', 20)
        end
    end
    
else
    
end
    
%% Done
beep;
toc
