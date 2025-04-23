%% Set the MG Failure state in the MG_State Variable

% Set the Failed Line
%failure.line = {'B1_B2' 'B2_B1'};
failure.pos = contains(LoadVars,failure.line);
if any(failure.pos) == false %JM: Should be `if all(failure.pos)`...
    disp("Oops, typo in line name")
end
    
% Set the number of hours of failure
failure.time = 7*24;
% Set the start/stop time, bounded to stay within simulation run time
failure.start = randi(height(MG_State)-failure.time+1);
failure.end = failure.start+failure.time-1;

MG_State{failure.start:failure.end, failure.pos} = false;

disp(nodes(failure.pos) + " failed at time " + failure.start + " for " + failure.time + " hrs");