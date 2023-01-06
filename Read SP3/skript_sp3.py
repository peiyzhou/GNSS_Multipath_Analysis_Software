import numpy as np
import copy
#Function that reads the GNSS satellite position data from a SP3 position
#file. The function has been tested with sp3c and sp3d. NOTE: It is
#advised that any use of this function is made through the parent function
#"read_multiple_SP3Nav.m", as it has more functionality. 
#--------------------------------------------------------------------------------------------------------------------------
#INPUTS

#filename:             path and filename of sp3 position file, string

#desiredGNSSsystems:   array. Contains string. Each string is a code for a
#                      GNSS system that should have its position data stored 
#                      in sat_positions. Must be one of: "G", "R", "E",
#                      "C". If left undefined, it is automatically set to
#                      ["G", "R", "E", "C"]
#--------------------------------------------------------------------------------------------------------------------------
#OUTPUTS

#sat_positions:    cell. Each cell elements contains position data for a
#                  specific GNSS system. Order is defined by order of 
#                  navGNSSsystems. Each cell element is another cell that 
#                  stores position data of specific satellites of that 
#                  GNSS system. Each of these cell elements is a matrix 
#                  with [X, Y, Z] position of a epoch in each row.

#                  sat_positions{GNSSsystemIndex}{PRN}(epoch, :) = [X, Y, Z]

#epoch_dates:      matrix. Each row contains date of one of the epochs. 
#                  [nEpochs x 6]

#navGNSSsystems:   array. Contains string. Each string is a code for a
#                  GNSS system with position data stored in sat_positions.
#                  Must be one of: "G", "R", "E", "C"

#nEpochs:          number of position epochs, integer

#epochInterval:    interval of position epochs, seconds

#success:          boolean, 1 if no error occurs, 0 otherwise
#--------------------------------------------------------------------------------------------------------------------------



#
max_GNSSsystems = 4;

max_GPS_PRN     = 36; #Max number of GPS PRN in constellation
max_GLONASS_PRN = 36; #Max number of GLONASS PRN in constellation
max_Galileo_PRN = 36; #Max number of Galileo PRN in constellation
max_Beidou_PRN  = 60; #Max number of BeiDou PRN in constellation
max_sat = [max_GPS_PRN, max_GLONASS_PRN, max_Galileo_PRN, max_Beidou_PRN]

#Initialize variables
success = 1

#Open nav file
# fid=fopen(filename,'r');
filename = 'testfile.SP3'
try:
    fid = open(filename,'r')
except:
    success = 0
    raise ValueError('No file selected!')

#GNSS system order
navGNSSsystems = ["G", "R", "E", "C"];
#Map mapping GNSS system code to GNSS system index
# GNSSsystem_map = containers.Map(navGNSSsystems, [1, 2, 3, 4]);
GNSSsystem_map = dict(zip(navGNSSsystems,[1, 2, 3, 4]))

results = {}
results['GNSS_systems'] = navGNSSsystems

# if nargin==1
#    desiredGNSSsystems = ["G", "R", "E", "C"];
# end





# #If invalid filename
# if fid==-1
#     disp('ERROR(readSP3Nav): SP3 Navigation filename does not exist!')
#     [sat_positions, epoch_dates, navGNSSsystems, nEpochs, epochInterval] = deal(NaN);
#     success = 0;
#     return
# end
sp3 = [] # testing


obs_GPS = []
obs_GLONASS =[]
obs_BeiDou = []
obs_Galileo = []

#Gobble up header
headerLine = 0
# line = fgetl(fid)
line = fid.readline().rstrip()

#all header lines begin with '*'
# while ~strcmp(line(1), '*')
while '*' not in line[0]:
    headerLine = headerLine + 1
    
    if headerLine == 1:
       # sp3Version = line(1:2)
       sp3Version = line[0:2]
       #control sp3 version
       
       # if ~strcmp(sp3Version, '#c') && ~strcmp(sp3Version, '#d')
       if '#c' not in sp3Version and '#d' not in sp3Version:
           print('ERROR(readSP3Nav): SP3 Navigation file is version %s, must be version c or d!' % (sp3Version))
           # [sat_positions, epoch_dates, navGNSSsystems, nEpochs, epochInterval] = deal(NaN)
           success = 0
           # return
     
       
       #control that sp3 file is a position file and not a velocity file
       # Pos_Vel_Flag = line(3);
       Pos_Vel_Flag = line[2]

       if 'P' not in Pos_Vel_Flag:
           print('ERROR(readSP3Nav): SP3 Navigation file is has velocity flag, should have position flag!')
           # [sat_positions, epoch_dates, navGNSSsystems, nEpochs, epochInterval] = deal(NaN);
           success = 0
           # return
       
       #Store coordinate system and amount of epochs
       # CoordSys = line(47:51);
       # nEpochs = str2double(line(33:39));
       CoordSys = line[46:51]
       nEpochs = int(line[32:39])
    
    
    if headerLine == 2:
        #Store GPS-week, "time-of-week" and epoch interval[seconds]
       GPS_Week = int(line[3:7])
       tow      = float(line[8:23])
       epochInterval = float(line[24:38])

    
    if headerLine == 3:
       
       #initialize array for storing indices of satellites to be excluded
       RemovedSatIndex = []
       
       #store amount of satellites in each epoch, including undesired ones
       # if strcmp(sp3Version, '#c')
       #  nSat = str2double(line(5:6)); 
       # else
       #  nSat = str2double(line(4:6)); 
       # end
       
       if '#c' in sp3Version:
        nSat = int(line[5:6])
       else:
        nSat = int(line[4:6])
       
       #remove beginning of line
       # line = line(10:60);
       line = line[9:60]
       
       #Initialize array for storing the order of satellites in the SP3
       #file(ie. what PRN and GNSS system index)
       
        # GNSSsystemIndexOrder = zeros(1, nSat);
        # PRNOrder = zeros(1, nSat);
       
       GNSSsystemIndexOrder = []
       PRNOrder = []
        
       
       #Keep reading lines until all satellite IDs have been read
        # for k = 1:nSat
       for k in range(0,nSat):          
          #control that current satellite is amoung desired systems
          # if ismember(line(1), desiredGNSSsystems):
          if np.in1d(line[0], list(GNSSsystem_map.keys())):
              #Get GNSSsystemIndex from map container
              # GNSSsystemIndex = GNSSsystem_map(line(1));
              GNSSsystemIndex = GNSSsystem_map[line[0]]
              #Get PRN number/slot number
              # PRN = str2double(line(2:3));
              PRN = int(line[1:3])
              #remove satellite that has been read from line
              # line = line(4:end);
              line = line[3::]
              #Store GNSSsystemIndex and PRN in satellite order arrays
              # GNSSsystemIndexOrder(k) = GNSSsystemIndex;
              # PRNOrder(k) = PRN;
              GNSSsystemIndexOrder.append(GNSSsystemIndex)
              PRNOrder.append(PRN)
              
              #if current satellite ID was last of a line, read next line
              #and increment number of headerlines
              # if np.mod(k,17)==0 and k != 0:
              if np.mod(k,16)==0 and k != 0:
                  # line = fgetl(fid);
                  line = fid.readline().rstrip()
                  line = line[9:60]
                  headerLine = headerLine + 1
          #If current satellite ID is not amoung desired GNSS systems,
          #append its index to array of undesired satellites
          else:
              # RemovedSatIndex = [RemovedSatIndex, k];
              RemovedSatIndex.append(k)
              # GNSSsystemIndexOrder(k) = NaN;
              GNSSsystemIndexOrder.append(np.nan)
              # PRNOrder(k) = NaN
              PRNOrder.append(np.nan)
              
              #if current satellite ID was last of a line, read next line
              #and increment number of headerlines
              # if np.mod(k,17)==0 and k != 0:
              if np.mod(k,16)==0 and k != 0:
                  # line = fgetl(fid);
                  line = fid.readline().rstrip()
                  # line = line(10:60);
                  line = line[9:60]
                  headerLine = headerLine + 1;
    #read next line
    # line = fgetl(fid);
    line = fid.readline().rstrip()

#Initialize matrix for epoch dates
epoch_dates = []
epoch_dates2 = np.array(np.empty(6).reshape(1,6))

# #initialize cell structure for storing satellite positions
# sat_positions = cell(1, max_GNSSsystems);
# for k = 1:max_GNSSsystems
#     sat_positions{k} = cell(1, max_sat(k));
#     for j = 1:max_sat(k)
#       sat_positions{k}{j} = zeros(nEpochs, 3); 
#     end
# end

# sat_positions = {}
# sat_positions['GNSS_systems'] = navGNSSsystems
sys_dict = {}
PRN_dict = {}

PRN_dict_GPS = {}
PRN_dict_Glonass = {}
PRN_dict_Galileo = {}
PRN_dict_BeiDou = {}
#read satellite positions of every epoch

    
ini_sys = list(GNSSsystem_map.keys())[0]
for k in range(0,nEpochs):
    #Store date of current epoch
    # epoch_dates(k, :) = sscanf(line(4:31),'%d%d%d%d%d%f')';
    epochs = line[3:31].split(" ")
    epochs = [x for x in epochs if x != "" ] # removing ''
    epoch_dates.append(epochs)
    epoch_dates2 = np.append(epoch_dates2,np.array(epochs).reshape(1,len(epochs)),axis = 0)
    #store positions of all satellites for current epoch
    # ini_sys = list(GNSSsystem_map.keys())[0]
    obs_dict = {}
    obs_dict_GPS = {}
    obs_dict_Glonass = {}
    
    for i in range(0,nSat):
        #read next line
        line = fid.readline().rstrip()
        #if current satellite is amoung desired systems, store positions
        if np.in1d(i, RemovedSatIndex,invert = True):
            #Get PRN and GNSSsystemIndex of current satellite for
            #previously stored order
            PRN = PRNOrder[i]
            GNSSsystemIndex = GNSSsystemIndexOrder[i]
            #store position of current satellite in correct location in
            #cell structure
            # sat_positions{GNSSsystemIndex}{PRN}(k, :) = 1e3 * sscanf(line(5:46),'%f%f%f')';
            sys_keys = list(GNSSsystem_map.keys())
            sys_values = list(GNSSsystem_map.values())
            sys_inx = sys_values.index(GNSSsystemIndex)
            sys = sys_keys[sys_inx]
            obs = line[5:46].split(" ")
            obs = [x for x in obs if x != "" ]
            sp3.append(obs)

            # if sys != ini_sys:
            #     PRN_dict = {}
            #     ini_sys = sys
                
            if sys != ini_sys:
                ini_sys = sys
                # obs_dict = {}

                
            # obs_dict[str(k)]  = obs
            # PRN_dict[int(PRN)] = obs_dict
            obs_dict[str(PRN)]  = obs[:]  # Nå blir alt med, men glonass data er GPS data
            PRN_dict[int(k)] = obs_dict
            
            if sys == 'G':
                obs_G = [x for x in obs if x != "" ]
                obs_dict_GPS[PRN]  = obs_G.copy()
                PRN_dict_GPS[k] = obs_dict.copy()
            elif sys =='R':
                obs_R = [x for x in obs if x != "" ]
                obs_dict_Glonass[PRN]  = obs_R.copy()
                PRN_dict_Glonass[k] = obs_dict_Glonass.copy()
                
                
        sys_dict['G'] = PRN_dict_GPS
        sys_dict['R'] = PRN_dict_Glonass
        results[sys] = sys_dict[sys]
                
    #Get next line
    line = fid.readline().rstrip()
    
#the next line should be eof. If not, raise warning
try:
    line = fid.readline().rstrip()
except:
    print('ERROR(readSP3Nav): End of file was not reached when expected!!')
    success = 0
     
#remove NaN values
GNSSsystemIndexOrder = [x for x in GNSSsystemIndexOrder if x != 'nan']
PRNOrder = [x for x in GNSSsystemIndexOrder if x != 'nan']

print('INFO(readSP3Nav): SP3 Navigation file %s has been read.' %(filename))
## Remove GNSS systems not present in navigation file
# sat_positions  = sat_positions(unique(GNSSsystemIndexOrder));
# navGNSSsystems = navGNSSsystems(unique(GNSSsystemIndexOrder));





# return sat_positions, epoch_dates, navGNSSsystems, nEpochs, epochInterval, success