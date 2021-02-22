import json, random, os, math, jsonpickle, games
from enum import Enum, IntEnum
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
                        "speed_stars" : 1.0,
                        "striking_stars" : 1.0,
                        "goalkeeping_stars" : 1.0,
                        "ballhandling_stars" : 1.0
                    },
                "rng_breakpoints" : {
                        "shot_on_target" : 0,
                        "shot_success" : 0,
                        "save_deflect_chance" : 0.50,
                        "pass_success" : 0,
                        "steal_roll_mult" : 1
                    }
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
    pass_success = "passes to"
    pass_intercepted = "attempts a pass to {}, but the ball is intercepted by" #requires .format(reciever)
    pass_miss = "sends a pass to {}, but it goes wide!" #requires .format(reciever)
    tackles_in = "tackles"
    tackles_out = "tackles {}, sending the ball out of bounds! {} takes the throw-in." #requires .format(possesser, thrower)
    tackle_dodge = "attempts to tackle {}, but they dribble around!" #requires .format(possesser)
    collect_ball = "takes possession of the ball."
    cross = "crosses it in!"
    dribble = "dribbles" #direction would be nice to have
    header = "heads it" #direction here too
    juke = "jukes around {} and dribbles" #direction??? requires .format(defender)
    breakaway = "breaks away!"
    shot_miss = "shoots and misses! {} sets up for a goal kick." #requires .format(goalie)
    shot_goal = "shoots and scores!"
    shot_save_capture = "shoots, but {} makes the save!" #requires .format(goalie)
    shot_save_deflect = "shoots, but {} deflects the shot out of bounds!" #requires .format(goalie)   
    head_miss = "heads the ball towards the net, but misses. {} sets up for a goal kick." #requires .format(goalie)
    head_goal = "heads the ball into the net and scores!"
    head_save_capture = "heads the ball, but {} makes the save!" #requires .format(goalie)
    head_save_deflect = "heads the ball, but {} deflects the shot out of bounds!" #requires .format(goalie)     
    clear_ball = "clears the ball away!"
    foul_free = "is fouled by {}, and is awarded a free kick!" #requires .format(defender)
    foul_penalty = "is fouled by {}, and is awarded a penalty kick!" #requires .format(defender)
    red_card = "gets a red card!"
    yellow_card = "gets a yellow card."
    offsides = "passes to {}, but is called offsides. {} sets up for a free kick." #requires .format(reciever, defender)
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
        self.stlats["speed_stars"] = self.stlats["baserunning_stars"]
        self.stlats["striking_stars"] = self.stlats["pitching_stars"]
        self.stlats["goalkeeping_stars"] = self.stlats["batting_stars"]
        self.stlats["ballhandling_stars"] = self.stlats["defense_stars"]
     
    def star_string(self, key):
        str_out = ""
        starstring = str(self.stlats[key])
        if ".5" in starstring:
            starnum = int(starstring[0])
            addhalf = True
        else:
            starnum = int(starstring[0])
            addhalf = False
        str_out += "⚽ " * starnum
        if addhalf:
            str_out += "🏈"
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

    def swap_player(self, name):
        this_player, index, roster = self.find_player(name)
        if this_player is not None and len(roster) > 1:
            if roster == self.starters:
                if self.add_sub(this_player):
                    roster.pop(index)
                    return True
            elif roster == self.bench:
                if self.add_goalie(this_player):
                    roster.pop(index)
                    return True
            elif roster == self.goalies:
                if self.add_starter(this_player)[0]:
                    roster.pop(index)
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
        if this_player is not None and new_spot <= len(roster) and roster == self.goalies:
            roster.pop(index)
            try:
                roster.insert(new_spot-1, this_player)
            except:
                roster.append(this_player)
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
        for this_player in self.starters + self.goalies + self.bench:
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

class soccer_ball(object):
    def __init__(self):
        self.x = 0.5
        self.y = 0.5

    def position(self):
        if self.y > 0.86:
            pos_int = 2
        elif self.y > 0.13:
            pos_int = 1
        else:
            pos_int = 3

        if self.x < 0.09:
            pos_int += 0 #here to prevent future oopses
        elif self.x < 0.33:
            pos_int += 3
        elif self.x < 0.67:
            pos_int += 6
        elif self.x < 0.91:
            pos_int += 9
        else:
            pos_int += 12
        
        return ball_locations(pos_int)

    def corner_kick_pos(self, top, left):
        if top:
            self.y = 1.0
        else:
            self.y = 0.0
        if left:
            self.x = 0.0
        else:
            self.x = 1.0

    def goal_kick_pos(self, left):
        if left:
            self.x = 0.06
        else:
            self.x = 0.94
        self.y = (random.random()*0.33)+0.33

class ball_locations(IntEnum):
    left_penalty = 1
    left_penalty_top = 2
    left_penalty_bot = 3
    left_field = 4
    left_field_top = 5
    left_field_bot = 6
    center = 7
    center_top = 8
    center_bot = 9
    right_field = 10
    right_field_top = 11
    right_field_bot = 12
    right_penalty = 13
    right_penalty_top = 14
    right_penalty_bot = 15


class game(object):

    def __init__(self, team1, team2, length=None):
        self.over = False
        self.teams = {"away" : team1, "home" : team2} #away on the left, home on right
        self.current_time = timedelta(hour=0,minute=0,second=0)
        self.cards = {} #player: card number
        self.injuries = []
        self.goals = {} #player: timestamp
        self.last_update = ({}, [], "") #this is a ({outcome}, [extra players], "additional_string") tuple
        self.owner = None
        self.ready = False
        self.injury_time = timedelta(hour=0,minute=1,second=0)
        self.posession = {"team" : None, "player" : None}
        self.ball = soccer_ball()
        self.pitch_size = {"x" : 125, "y" : 85}
        if length is not None:
            self.duration = length
        else:
            self.duration = config()["default_length"]
        self.weather = weather("Sunny","🌞")

        def get_goalie(self):
            if self.posession["team"] == self.teams["home"]:
                return self.teams["away"].goalie
            else:
                return self.teams["home"].goalie

        def shot(self, shooter, goalie): #returns a (game_event, string) where game_event is the actual game event and string = output text already formatted
            shot_stat = random_star_gen("striking_stars", shooter)
            save_stat = random_star_gen("goalkeeping_stars", goalie)

            shot_roll = random.gauss(0.5*math.erf((shot_stat-2)/4)-0.2,3)

            if shot_roll < config()["rng_breakpoints"]["shot_on_target"]:
                return (game_events.shot_miss, game_events.shot_miss.value.format(goalie.name))
            else:
                save_roll = random.gauss(math.erf((save_stat-shot_stat+2)/4), 1.5)
                if save_roll > config()["rng_breakpoints"]["shot_success"]:
                    if random.random() < (config()["rng_breakpoints"]["save_deflect_chance"]-(5*save_stat/100)):
                        return (game_events.shot_save_deflect, game_events.shot_save_deflect.value.format(goalie.name))
                    else:
                        return (game_events.shot_save_capture, game_events.shot_save_capture.value.format(goalie.name))
                else:
                    return (game_events.shot_goal, game_events.shot_goal.value)

        def head_shot(self, shooter, goalie, difficulty=1): #returns a (game_event, string) where game_event is the actual game event and string = output text already formatted
                                                            #shot roll is divided by difficulty
            shot_stat = random_star_gen("ballhandling_stars", shooter)
            save_stat = random_star_gen("goalkeeping_stars", goalie)

            shot_roll = random.gauss(0.5*math.erf((shot_stat-2)/4)-0.2,3) / difficulty

            if shot_roll < config()["rng_breakpoints"]["shot_on_target"]:
                return (game_events.head_miss, game_events.head_miss.value.format(goalie.name))
            else:
                save_roll = random.gauss(math.erf((save_stat-shot_stat+2)/4), 1.5)
                if save_roll > config()["rng_breakpoints"]["shot_success"]:
                    if random.random() < (config()["rng_breakpoints"]["save_deflect_chance"]-(5*save_stat/100)):
                        return (game_events.head_save_deflect, game_events.head_save_deflect.value.format(goalie.name))
                    else:
                        return (game_events.head_save_capture, game_events.head_save_capture.value.format(goalie.name))
                else:
                    return (game_events.head_goal, game_events.head_goal.value)

        def pass_attempt(self, passer, defender, reciever, difficulty = 1): #returns a (game_event, string) where game_event is the actual game event and string = output text already formatted
                                                                            #interception roll is multiplied by difficulty
            pass_stat = max(random_star_gen("striking_stars", passer), random_star_gen("ballhandling_stars", passer))
            steal_stat = max(random_star_gen("speed_stars", defender), random_star_gen("ballhandling_stars", defender))

            pass_roll = random.gauss(0.5*math.erf((pass_stat)/15)+0.8,0.8)

            if pass_roll < config()["rng_breakpoints"]["pass_success"]:
                return (game_events.pass_miss, game_events.pass_miss.value.format(reciever.name))
            else:
                steal_roll = random.gauss(0.25*math.erf(steal_stat/4)-0.25,0.5) * config()["rng_breakpoints"]["steal_roll_mult"] * difficulty
                if steal_roll > pass_roll:
                    return (game_events.pass_intercepted, f"{game_events.pass_intercepted.value.format(reciever.name)} {defender.name}!" )
                else:
                    return (game_events.pass_success, f"{game_events.pass_success.value} {reciever.name}.")



def get_team(name, owner=False):
    try:
        team_tuple, is_soccer = db.get_team(name, owner=True)
        team_json = jsonpickle.decode(team_tuple[2], keys=True, classes=(team, games.team))
        if team_json is not None:
            if not is_soccer: #detects baseball teams, converts
                convert_team = team()
                convert_team.name = team_json.name
                convert_team.slogan = team_json.slogan
                for pitcher in team_json.rotation:
                    convert_team.add_goalie(player(json.dumps(pitcher.stlats)))
                for index in range(0,len(team_json.lineup)-1):
                    convert_team.add_starter(player(json.dumps(team_json.lineup[index].stlats)))
                convert_team.add_sub(player(json.dumps(team_json.lineup[len(team_json.lineup)-1].stlats)))
                save_team(convert_team, team_tuple[4])
                team_json = convert_team
            if not owner:            
                return team_json
            else:
                return (team_json, team_tuple[4])
        return None
    except:
        return None


def save_team(this_team, user_id):
    try:
        this_team.prepare_for_save()
        team_json_string = jsonpickle.encode(this_team, keys=True)
        db.save_team(this_team.name, team_json_string, user_id)
        return True
    except:
        return None

def update_team(this_team):
    try:
        this_team.prepare_for_save()
        team_json_string = jsonpickle.encode(this_team, keys=True)
        db.update_team(this_team.name, team_json_string)
        return True
    except:
        return None

def get_all_teams():
    teams = []
    for team_pickle in db.get_all_teams():
        this_team = jsonpickle.decode(team_pickle[0], keys=True, classes=team)
        teams.append(this_team)
    return teams

def search_team(search_term):
    teams = []
    for team_pickle in db.search_teams(search_term):
        team_object = jsonpickle.decode(team_pickle[0], keys=True, classes=(team, games.team))
        try:
            team_json = get_team(team_object.name)
        except:
            return None

        teams.append(team_json)
    return teams

def random_star_gen(key, player):
    return random.gauss(config()["stlat_weights"][key] * player.stlats[key],0.75)

config()