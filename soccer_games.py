import json, random, os, math, jsonpickle
from enum import Enum
from datetime import time, timedelta
import database as db

data_dir = "data"
games_config_file = os.path.join(data_dir, "soccer_games_config.json")

def config():
    if not os.path.exists(os.path.dirname(games_config_file)):
        os.makedirs(os.path.dirname(games_config_file))
    if not os.path.exists(games_config_file):
        #generate default config
        config_dic = {
                "default_length" : 90,
                "stlat_weights" : {
                        #what stats am i even going to use??????
                    },
            }
        with open(games_config_file, "w") as config_file:
            json.dump(config_dic, config_file, indent=4)
            return config_dic
    else:
        with open(games_config_file) as config_file:
            return json.load(config_file)

def all_weathers():
    weathers_dic = {
        #"Supernova" : weather("Supernova", "🌟"),
        #"Midnight": weather("Midnight", "🕶"),
        "Slight Tailwind": weather("Slight Tailwind", "🏌️‍♀️"),
        "Heavy Snow": weather("Heavy Snow", "❄"),
        #"Twilight" : weather("Twilight", "👻"),
        "Thinned Veil" : weather("Thinned Veil", "🌌"),
        #"Heat Wave" : weather("Heat Wave", "🌄"),
        #"Drizzle" : weather("Drizzle", "🌧")
        }
    return weathers_dic

class game_events(Enum):
    player_pass_success = "passes to"
    player_pass_intercepted = "attempts a pass to {}, but the ball is intercepted by" #requires .format(reciever)
    tackles_in = "tackles"
    tackles_out = "tackles {}, sending the ball out of bounds! {} takes the throw-in." #requires .format(possesser, thrower)
    tackle_dodge = "attempts to tackle {}, but they dribble around!" #requires .format(possesser)
    collect_ball = "takes possession of the ball."
    player_dribble = "dribbles" #direction would be nice to have
    player_shot_save = "shoots, but {} makes the save!" #requires .format(goalie)
    player_shot_goal = "shoots and scores!"
    player_head_goal = "heads the ball into the net and scores!"
    player_head_save = "heads the ball, but {} makes the save!" #requires .format(goalie)
    player_shot_miss = "shoots and misses! {} sets up for a goal kick." #requires .format(goalie)
    foul_free = "is fouled by {}, and is awarded a free kick!" #requires .format(defender)
    foul_penalty = "is fouled by {}, and is awarded a penalty kick!" #requires .format(defender)
    red_card = "gets a red card!"
    yellow_card = "gets a yellow card."
    offsides = "passes to {}, but is called offsides. {} sets up for a free kick." #requires .format(reciever, goalie)
    out_side = "plays out of bounds. {} takes the throw-in." #requires .format(thrower)
    out_back_self = "deflects the ball out of bounds. {} sets up for a corner kick."
    throw_in = "throws in to"
    goal_kick = "makes the goal kick, and {} recieves it." #requires .format(reciever)
    corner_kick = "sends the corner kick across!"
    free_kick_block = "makes the free kick. It's blocked by"
    free_kick_save = "makes the free kick past the wall, but {} saves it!" #requires .format(goalie)
    free_kick_deflect_goal = "makes the free kick past the wall, and {} sends it in for a goal!" #requires .format(reciever)
    free_kick_goal = "makes the free kick, and scores!"
    goalie_punt = "kicks the ball downfield."
    goalie_throw = "yeets the ball downfield."
    injury = "is injured! {} comes in to replace them." #requires .format(substitute)

class player(object):
    def __init__(self, json_string):
        self.stlats = json.loads(json_string)
        self.id = self.stlats["id"]
        self.name = self.stlats["name"]
        self.game_stats = {
                            "possession_time" : 0,
                            "shots" : 0,
                            "goals" : 0,
                            "misses" : 0,
                            "passes" : 0,
                            "tackles" : 0,
                            "penalties" : 0,
                            "cards" : 0,
                            "blocks" : 0,
                            "offsides" : 0,
                            "corner_kicks" : 0,
                            "free_kicks" : 0,
                            "saves" : 0
            }

    def star_string(self, key):
        str_out = ""
        starstring = str(self.stlats[key])
        if ".5" in starstring:
            starnum = int(starstring[0])
            addhalf = True
        else:
            starnum = int(starstring[0])
            addhalf = False
        str_out += "⭐" * starnum
        if addhalf:
            str_out += "✨"
        return str_out

    def __str__(self):
        return self.name

class team(object):
    def __init__(self):
        self.name = None
        self.starters = []
        self.bench = []
        self.goalies = []
        self.goalie = None
        self.active_players = []
        self.slogan = None
        self.score = 0

    def find_player(self, name):
        for index in range(0,len(self.starters)):
            if self.starters[index].name == name:
                return (self.starters[index], index, self.starters)
        for index in range(0,len(self.bench)):
            if self.bench[index].name == name:
                return (self.bench[index], index, self.bench)
        for index in range(0,len(self.goalies)):
            if self.goalies[index].name == name:
                return (self.goalies[index], index, self.goalies)
        else:
            return (None, None, None)

    def find_player_spec(self, name, roster):
         for s_index in range(0,len(roster)):
            if roster[s_index].name == name:
                return (roster[s_index], s_index)

    def swap_player(self, name, to_roster):
        this_player, index, roster = self.find_player(name)
        if this_player is not None and len(roster) > 1:
            if roster == self.lineup:
                if self.add_pitcher(this_player):
                    roster.pop(index)
                    return True
            else:
                if self.add_lineup(this_player)[0]:
                    self.rotation.pop(index)
                    return True
        return False

    def delete_player(self, name):
        this_player, index, roster = self.find_player(name)
        if this_player is not None and len(roster) > 1:
            roster.pop(index)
            return True
        else:
            return False

    def slide_player(self, name, new_spot):
        this_player, index, roster = self.find_player(name)
        if this_player is not None and new_spot <= len(roster):
            roster.pop(index)
            roster.insert(new_spot-1, this_player)
            return True
        else:
            return False

    def slide_player_spec(self, this_player_name, new_spot, roster):
        index = None
        for s_index in range(0,len(roster)):
            if roster[s_index].name == this_player_name:
                index = s_index
                this_player = roster[s_index]
        if index is None:
            return False
        elif new_spot <= len(roster):
            roster.pop(index)
            roster.insert(new_spot-1, this_player)
            return True
        else:
            return False
                
    def add_starter(self, new_player):
        if len(self.starters) < 18:
            self.starters.append(new_player)
            return (True,)
        else:
            return (False, "18 players on the field, maximum. We're being really generous here.")
    
    def add_goalie(self, new_player):
        if len(self.goalies) < 4:
            self.goalies.append(new_player)
            return True
        else:
            return False

    def add_sub(self, new_player):
        if len(self.bench) < 4:
            self.bench.append(new_player)
            return True
        else:
            return False

    def set_goalie(self, rotation_slot = None, use_lineup = False):
        temp_rotation = self.goalies.copy()
        if use_lineup:         
            for member in self.bench + self.starters:
                temp_rotation.append(member)
        if rotation_slot is None:
            self.goalie = random.choice(temp_rotation)
        else:
            self.goalie = temp_rotation[(rotation_slot-1) % len(temp_rotation)]

    def is_ready(self):
        try:
            return (len(self.starters) >= 1 and len(self.goalies) > 0)
        except AttributeError:
            self.goalies = [self.goalie]
            self.goalie = None
            return (len(self.starters) >= 1 and len(self.goalies) > 0)

    def prepare_for_save(self):
        self.goalie = None
        self.score = 0
        for this_player in self.starters + self.rotation + self.bench:
            for stat in this_player.game_stats.keys():
                this_player.game_stats[stat] = 0
        return self

    def finalize(self):
        if self.is_ready():
            if self.goalie == None:
                self.set_goalie()
            while len(self.starters) <= 2:
                self.starters.append(random.choice(self.starters))       
            return self
        else:
            return False

class game(object):

    def __init__(self, team1, team2, length=None):
        self.over = False
        self.teams = {"left" : team1, "right" : team2}
        self.current_time = timedelta(hour=0,minute=0,second=0)
        self.cards = {} #player: card number
        self.injuries = []
        self.goals = {} #player: timestamp
        self.last_update = ({},"") #this is a ({outcome}, "additional_string") tuple
        self.owner = None
        self.ready = False
        self.injury_time = timedelta(hour=0,minute=1,second=0)
        self.posession = {"team" : None, "player" : None}
        if length is not None:
            self.duration = length
        else:
            self.duration = config()["default_length"]
        self.weather = weather("Sunny","🌞")

        def get_goalie(self):
            if self.posession["team"] == self.teams["left"]:
                return self.teams["right"].goalie
            else:
                return self.teams["left"].goalie

config()