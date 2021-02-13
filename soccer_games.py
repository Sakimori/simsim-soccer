import json, random, os, math, jsonpickle
from enum import Enum
import database as db

data_dir = "data"
games_config_file = os.path.join(data_dir, "soccer_games_config.json")

def config():
    if not os.path.exists(os.path.dirname(games_config_file)):
        os.makedirs(os.path.dirname(games_config_file))
    if not os.path.exists(games_config_file):
        #generate default config
        config_dic = {
                "default_length" : 3,
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