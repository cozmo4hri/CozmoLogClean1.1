"""
author: Bishakha Chaudhury
Location: Social Brain in Action Lab

This program reads the Daslog from cozmo and tries to isolate data of interest for SoBa Lab
This is then output as a file that can then be input into Matlab to perform relevant analysis
"""

import json
import os
from datetime import datetime, timedelta
import sys


from record import DailyData


def read_input_log (log_file_path):
    """
    This reads the json log file entries and compiles each line into the
    log_data list
    @param log_file_path: The full path to the log file to be read
    @ return: List of log lines 
    """
    log_data = []
    file_pointer =  open(log_file_path, 'r')
    file_data = file_pointer.read()
    file_pointer.close()
    raw_data = file_data.split('},{')
    total_lines = len(raw_data)
    count = 1
    error_line = 0
    for raw_line in raw_data:
        #print("%s" % raw_line)
        #print(">>>>>>>>>>>>>>>>>>")
        if not raw_line.startswith('{'):
            raw_line = '{' + raw_line
            
        if total_lines==count:
            # remove trailing ',' from last line
            raw_line = raw_line[:-1]
        elif raw_line[-1] != '}':
            raw_line= raw_line + '}'
        
        count += 1
        try:
            log_data.append(json.loads(raw_line))
            #print("%s" % log_data[-1])
            #print("-------------------------")
        except:
            # Sacrifice the problematic logline
            # but record that this line we could not read
            log_data.append(None)
            error_line += 1
    #print("There were %d error lines" % error_line)
    return log_data
    
def analyse_log_data(log_data, session_record):
    """
    Analyses the data in each log and puts it in the session data.
    @param log_data: The lines in the log file as a list
    @param session_record: The play session against which the entries are to be recorded 
    @return : The updated session_record with updated information from this log file
    """
    current_game = session_record.current_game_name
    current_game_id = session_record.current_game_id
    current_game_result = 0
    
    for log_line in log_data:
        if 'robot.game_unlock_status' in log_line:
            #print("%s" % log_line['robot.game_unlock_status'].split(','))
            session_record.update_record_list('games_unlocked',
                            log_line['robot.game_unlock_status'].strip(',')\
                                                                .split(','))
            
        if 'world.daily_goals' in log_line and '$data' in log_line:
            # This line has a daily goal motivator
            session_record.update_record_set('daily_challenge',
                                                 log_line['$data'].strip(',')\
                                                                  .strip('_0/1')\
                                                                  .replace('<b>', '')\
                                                                  .replace('</b>', ''))
           
        if 'robot.spark_unlock_status' in log_line:
            #print("%s" % log_line['robot.spark_unlock_status'].split(','))
            session_record.update_record_list('features_unlocked',
                                log_line['robot.spark_unlock_status'].strip(',')\
                                                                     .split(','))
        if "robot.face_enrollment" in log_line:
            session_record.details['face_enrolled'].append(
                                                log_line['robot.face_enrollment'])
            
        ############################################################
        # These three together indicate the start of a game
        if 'game.launch' in log_line:
            if current_game != None:
                session_record.abort_game(current_game)
            current_game = log_line['game.launch']
            current_game_id = None
            session_record.create_or_update_game(current_game)
            
        if current_game and 'game.start' in log_line:
            if current_game_id and  current_game_id != log_line['game.start']:
                # The last game must have been aborted or not accounted for
                if current_game:
                    session_record.abort_game(current_game)
                    current_game = None
            current_game_id = log_line['game.start']
            session_record.current_game_id = current_game_id
                    
                    
        if 'game.type' in log_line:
            if current_game == log_line['game.type']:
                # expected route. This is a all well sign
                # so nothing to do
                pass
            else:
                if current_game:
                    # We don't know what happened to the last game:
                    session_record['game_record'][current_game].game_abort_count += 1
                current_game = log_line['game.type']
                session_record.create_or_update_game(current_game)                           
            current_game_id = None
        # These three together indicate the start of a game
        #################################################################
                    
        #################################################################
        # These two together indicate the end of game
        if 'game.end' in log_line:
            session_record.end_game(current_game, current_game_result)
            current_game = None
            current_game_id = None
            current_game_result = 0 
            
        if current_game and "game.end.player_rank" in log_line:
            if log_line["game.end.player_rank"] == "0":
                # I think this defines cozmo lost
                current_game_result = -1
            else:
                current_game_result = 1
        # These two together indicate the end of game
        #################################################################
        
        if 'robot.play_animation' in log_line:
            anim_name = log_line['robot.play_animation']
            session_record.record_animation(current_game, 
                                          anim_name)
            
            if 'ask' in anim_name or 'request' in anim_name:
                session_record.add_update_request(anim_name)
                
        if 'meta.goal.progressed' in log_line:
            session_record.add_goal_progress(log_line['meta.goal.progressed'])
             
        if "robot.freeplay_goal_started" in log_line:
            session_record.create_or_update_free_play(
                                        log_line["robot.freeplay_goal_started"])       
       
        if 'robot.vision.face_recognition.re_recognized' in log_line:
            session_record.update_record_list('face_recognized',
                        [log_line['robot.vision.face_recognition.re_recognized']])
            
        if 'robot.vision.detected_pet' in log_line:
            if '$data' in  log_line:
                session_record.add_update_pet(log_line['$data'])
                        
            
    return session_record

def sort_logs_by_time(log_dir):
    """
    sorts file by creation time
    @param log_dir: The directory whose files are to be sorted 
    """
    file_paths_in_dir = [os.path.join(log_dir, 
                                      filename) for filename in 
                                                    os.listdir(log_dir)]
    file_stats_details = [(os.stat(file_path).st_mtime, file_path) 
                                            for file_path in file_paths_in_dir]
    sorted_log_files = sorted(file_stats_details)
    return sorted_log_files
        
def get_usage_details(log_dir):    
    """
    This sorts the log and groups interesting occurance by days and interaction sessions 
    within the days.
    @param log_dir: The directory containing all the log files to read
     
    """
    usage_log = {}
    daily_record = None
    last_log_time = None
    session_record = None
    #sort log files by time of creation
    sorted_log_file_path = sort_logs_by_time(log_dir)
    
    #For each log file in directory
    for fdate, fpath in sorted_log_file_path:
        if not os.path.isfile(fpath):
            # Don't want to get into directories
            continue
        #print("%s" % fpath)
        cur_log_time = datetime.utcfromtimestamp(fdate)
        date_string = "%s" % cur_log_time.date()
        
        # Which date and session does this log file belong to?
        # We deicde that from the creation date/time of the log file
        if not date_string in usage_log: 
            # We have a new date so make a new entry for it and
            # get a new session setup
            usage_log[date_string]=DailyData(cur_log_time) 
            del daily_record
            del session_record
            daily_record = usage_log[date_string]
            session_record = daily_record.get_current_session()
        else:
            daily_record = usage_log[date_string]
            time_gap = cur_log_time - last_log_time
            if time_gap.seconds >= 15*60:
                # This is a new session because 15min passed without interaction  
                # so there is no time gap between logs. 
                session_record = daily_record.get_new_session(cur_log_time)
            else:
                
                session_record = daily_record.get_current_session()
                session_record.add_time(time_gap)
                
        last_log_time = cur_log_time
        try:
            # Read the log file
            log_data = read_input_log(fpath)
            
            # Analyse the data found in the log file and put it in the session records
            analyse_log_data(log_data, session_record)
        except:
            # If a file is creating problem then tell us what it is
            print("Issue in %s" % fpath)
            raise
    return usage_log
    

if __name__ == "__main__":
    usage_log=None
    
    if len(sys.argv) < 2:
        try:
           
            #CHANGE THIS DIRECTORY
            usage_log = get_usage_details("C:/Users/Laptop/Documents/CozmoLogs")
            
        except:
            print("Check that you have provided the log directory correctly in code")
    else:
        # Or provide log directory at commandline
        log_dir = sys.argv[1]
        try:
            # Clean the data from the log directory collating usage into sessions
            #CHANGE THIS DIRECTORY
            usage_log = get_usage_details(log_dir)
        except:
            print("Incorrect log directory : %s " % log_dir)
    
    if usage_log:
        for day, usage in sorted(usage_log.items()):
            print("################################################################")
            usage_log[day].formatted_print()
        

				