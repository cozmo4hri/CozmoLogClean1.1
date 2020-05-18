"""
This file defines the classes that need to be recorded
"""
from datetime import timedelta

STANDARD_SESSIONS_START = timedelta(minutes=2)

class GameDetails:
    """
    Records the details of each type of game played
    """
    def __init__(self):
        self.name = None
        self.start_count = 1
        self.cozmo_win_count = 0
        self.cozmo_lose_count = 0
        self.neutral_outcome = 0
        self.game_abort_count = 0
        self.game_animations = {}
        self.positive_animations = 0
        self.negative_animations= 0
        self.mixed_neutral_animations = 0
    
class FreeplayDetails:
    """
    Records the details of 
    """
    def __init__(self):
        self.name = None
        self.start_count = 1       
        
class SessionData:   
    
    # This is for communicating between last log file analysed
    # and this log file
    
    def __init__(self, record_time, session_id):
        self.session_time = record_time
        self.current_game_name = None
        self.current_game_id = None
        self.details = { 'play_time': STANDARD_SESSIONS_START,
                            'play_sessions': session_id + 1,
                            'games_unlocked': [],
                            'features_unlocked': [],
                            'animations_played':{},
                            'positive_animations':0,
                            'negative_animations':0,
                            'mixed_neutral_animations':0,
                            'face_enrolled': [],
                            'face_recognized': [],
                            'unknown_face_count': 0,
                            'pets_recorded': {},
                            'freeplay_record': {},
                            'goal_progress': [],
                            'daily_challenge': [],
                            'robot_requests':{},
                            'game_record':{}
                          }
    
    def add_time(self, time_gap):
        """
        Adds time to play time. If an empty time is passed then
        It is assumed to be the start of a new session with a 2min log
        @param time_gap: time_delta giving the time to add
        """
        if time_gap:
            self.details['play_time'] += time_gap
        else:
            self.details['play_time'] += STANDARD_SESSIONS_START
            self.details['play_sessions'] += 1
            
    def add_update_pet(self, pet_type):
        """
        Records the number of times it cozmo detects a particular
        type of pet
        @param pet_type: string giving the type of pet that cozmo has
                         detected        
        """
        if pet_type in self.details['pets_recorded']:
            self.details['pets_recorded'][pet_type] += 1
        else:
            self.details['pets_recorded'][pet_type]  = 1
            
    def add_update_request(self, request_type):
        """
        Records the number of times it cozmo detects a particular
        type of pet
        @param pet_type: string giving the type of pet that cozmo has
                         detected        
        """
        if request_type in self.details['robot_requests']:
            self.details['robot_requests'][request_type] += 1
        else:
            self.details['robot_requests'][request_type]  = 1
    
    def anim_analysis(self, anim_name):
        anim_id = 0    
        positive_anim_strings = ['admire',
                                 'ask',
                                'celebrat',
                                'find',
                                'found',
                                'giggle',
                                'happy',
                                'hello',
                                'highenergy',
                                'ideatoplay',
                                'like',
                                'newarea',
                                'petdetection',
                                'playeryes',
                                'request',
                                'reacttocube',
                                'reenrollment',
                                'thankyou',
                                'upgrade',
                                'wheely',
                                'wiggle',
                                'turbo'
                                ]
        negative_anim_strings = ['badword',
                                 'bored',
                                 'dizzy',
                                 'frustrated',
                                 'lowenergy',
                                 'match_no',
                                 'playerno', 
                                 'struggle',
                                 'stuck',
                                 'upset',
                                 'turtleroll',
                                 'hiccup']
        if 'cure' in anim_name:
            # To handle cure of hiccups
            anim_id = 1
        if 'win' in anim_name or 'success' in anim_name:
            if 'player' in anim_name and not 'solo' in anim_name:
                anim_id = -1
            else:
                anim_id = 1
        elif 'lose' in anim_name or 'fail' in anim_name:
            if 'player' in anim_name and not 'solo' in anim_name:
                anim_id = 1
            else:
                anim_id = -1
        elif 'reacttoface' in  anim_name and not 'unidentified' in anim_name:
            # positive reactions seems to be for known people only
            anim_id = 1
        elif 'petdetection' in anim_name and 'misc' in anim_name: 
            # the sneeze
            anim_id = -1
            
            
        if not anim_id:
            # So if we have not already decided 
            for anim_string in positive_anim_strings:
                if anim_string in anim_name:
                    anim_id = 1
                    break
                
        if not anim_id:
            # So if we have not already decided 
            for anim_string in negative_anim_strings:
                if anim_string in anim_name:
                    anim_id = -1
                    break
        return anim_id

        
    def record_animation(self, game_name, animation_name):
        """
        Records the animation by keeping count of how many times
        It was played on a day. If a game_name is provided the 
        animation is recorded against the name
        @param game_name: The string giving the game name against which
                          this animation is being played
        @param animation_name: The name of the animation to record 
        """
        anim_id = self.anim_analysis(animation_name)
        if game_name:
            # This animation is part of the game
            if game_name not in self.details['game_record']:
                self.details['game_record'][game_name] = GameDetails()
                self.details['game_record'][game_name].name = game_name
            game_record = self.details['game_record'][game_name]
            if animation_name in game_record.game_animations:
                game_record.game_animations[animation_name] += 1
                if anim_id > 0:
                    game_record.positive_animations += 1
                elif anim_id < 0:
                    game_record.negative_animations += 1
                else:
                    game_record.mixed_neutral_animations += 1
            else:
                game_record.game_animations[animation_name] = 1
        else:
            if anim_id > 0:
                self.details['positive_animations'] += 1
            elif anim_id < 0:
                self.details['negative_animations'] += 1
            else:
                self.details['mixed_neutral_animations'] += 1
                
            if animation_name in self.details['animations_played']:
                self.details['animations_played'][animation_name] += 1
            else:
                self.details['animations_played'][animation_name] = 1
    
    def create_or_update_game(self, game_name):
        """
        If there is a record of the game updates the play count on it 
        otherwise creates a record
        @param game_name: String giving the name of the game the player
                          started
        """
        if game_name not in self.details['game_record']:
            self.details['game_record'][game_name] = GameDetails()
            self.details['game_record'][game_name].name = game_name
        else:
            self.details['game_record'][game_name].start_count += 1
        self.current_game_name = game_name
        self.current_game_id = None
        return self
    
    def end_game(self, game_name, game_result):
        """
        This method records the end of a game and the available result
        @param game_name: String giving the name of the game
        @param game_result: Integer indicating the game outcome
                             0  = Nutral
                             -1 = Cozmo lost game
                             1  = Cozmo won game
        """
        if game_name:
            if game_result == 0:
                self.details['game_record'][game_name].neutral_outcome += 1
            elif game_result < 0:
                self.details['game_record'][game_name].cozmo_lose_count += 1
            else:
                self.details['game_record'][game_name].cozmo_win_count += 1
            self.current_game_name = None
            self.current_game_id = None
            
    def abort_game(self, game_name):
        """
        If a new game starts while there is an active game then 
        this method is used to record aborting the previous game
        @param game_name: String naming the game that was aborted 
        """
        if game_name in self.details['game_record']:
            self.details['game_record'][game_name].game_abort_count += 1
        return self
        
    def update_record_list(self, record, new_list):
        """
        Adds the incoming value to the existing list for the given
        record
        @param record: string identifyinng the record to update
        @param new_list: string identifying the new list to append to the record list
        """
        self.details[record] = self.details[record] + new_list
        
    def update_record_set(self, record, record_string):
        """
        Adds the incoming value to the existing set for the given
        record if it doea not exist
        @param record: string identifyinng the record to update
        @param record_string: string identifying the new list to append to the record list
        """
        if record_string not in self.details[record]:
            self.details[record].append(record_string)
        
    def add_goal_progress(self, goal_title):
        """
        Records daily goals that were completed by the player
        @param goal_title: String giving the goal that was achieved  
        """
        self.details['goal_progress'].append(goal_title.replace("dailyGoal.title.",
                                                                ""))
    def create_or_update_free_play(self, free_play_name):
        """
        Records free play activites and how many time they were started
        @param free_play_name: The String giving the free play activity that was triggered
                               by cozmo
        """
        if free_play_name not in self.details['freeplay_record']:
            self.details['freeplay_record'][free_play_name] = FreeplayDetails()
            self.details['freeplay_record'][free_play_name].name = free_play_name
        else:
            self.details['freeplay_record'][free_play_name].start_count += 1

    def formatted_print(self):
        """
        Prints information gathered in a predefined format on screen
        """
        print("Play Sessions                : %s" % self.details['play_sessions'])
        print("Time                         : %s" % self.session_time)
        print("Played for (Hours:Min:Sec)   : %s" % self.details['play_time'])
        print("Face Enrolled                : %s" % self.details['face_enrolled'])
        print("Face Recognized              : %s" % list(set(self.details['face_recognized'])))
        print("Unknown Face Count           : %s" % self.details['unknown_face_count'])
        print("Pets Recorded                : %s" % self.details['pets_recorded'])
        print("Games Unlocked               : %s" % list(set(self.details['games_unlocked'])))
        print("Features Unlocked            : %s" % list(set(self.details['features_unlocked'])))
        print("Daily Challenge              : %s" % list(set(self.details['daily_challenge'])))
        print("Daily Goal Progress          : %s" % list(set(self.details['goal_progress'])))
        
        print("Cozmo Requests               : ")
        for request, count in self.details['robot_requests'].items():
            print("                         %s      : %d"  % (request,
                                                              count)) 
        
        
        # Game Play Records
        print("Game Records                 :")
        for name, game_details in  self.details['game_record'].items():
            print("                         Type              : %s"  % name)
            print("                         Play Sessions     : %d"  % game_details.start_count)
            print("                         Cozmo Wins        : %d"  % game_details.cozmo_win_count)
            print("                         Cozmo Lose        : %d"  % game_details.cozmo_lose_count)
            print("                         Neutral           : %d"  % game_details.neutral_outcome)
            print("                         Game Aborts       : %d"  % game_details.game_abort_count)
            print("                         Game Positive Anim : %d"  % game_details.positive_animations)
            print("                         Game Negative Anim : %d"  % game_details.negative_animations)
            print("                         Game MixedNeutral Anim : %d"  % game_details.mixed_neutral_animations)
            print("                         Game Animations   :") 
            for anim_name, count in game_details.game_animations.items():
                print("                                     %s      : %d"  % (anim_name,
                                                                              count))
        
        # General free play record
        print("Free Play Records            :")
        for name, free_play in self.details['freeplay_record'].items():
            print("                         %s      : %d"  % (name,
                                                              free_play.start_count)) 
              
        
        
        # General Animation Record
        print("Postive animations            : %d" % self.details['positive_animations'])
        print("Negative animations           : %d" % self.details['negative_animations'])
        print("Mixed Neutral animations      : %d" % self.details['mixed_neutral_animations'])
        print("Animation Played             :")
        for anim_name, count in self.details['animations_played'].items():
            
            print("                         %s      : %d"  % (anim_name,
                                                              count))
              
        
class DailyData:
    def __init__(self, record_date_time):
        self.record_date = "%s" % record_date_time.date()
        self.sessions_record = []
        self.current_session_id = 0
        
        session_start_time = record_date_time - STANDARD_SESSIONS_START 
        self.sessions_record.append(SessionData("%s" % session_start_time.time(),
                                                self.current_session_id))
          
    def get_new_session(self, record_date_time):
        self.current_session_id += 1
        session_start_time = record_date_time - STANDARD_SESSIONS_START 
        self.sessions_record.append(SessionData("%s" % session_start_time.time(),
                                                self.current_session_id))
        return self.sessions_record[self.current_session_id]
        
    def get_current_session(self):
        return self.sessions_record[self.current_session_id]
    
    def formatted_print(self):
        """
        Prints information gathered in a predefined format on screen
        """
        print("Date                         : %s" % self.record_date)
        print("Sessions Played              : %d" % (self.current_session_id+1))
        for i in range(0,self.current_session_id+1):
            print("-------------------------------------------------------------------------------------")
            self.sessions_record[i].formatted_print()
            print("-------------------------------------------------------------------------------------")
        
               