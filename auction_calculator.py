import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import numpy as np
from urllib.parse import urlparse, parse_qs

#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)

## These are dummy urls, but the final product should fit these parameters
## Would need to add a function that grabs the url after the user inputs form variables

## Parameters are as follows:
## type: bat or pitch
## pos: corresponds to roster positions in this order -- C, 1B, 2B, 3B, SS, OF, DH, UTIL, MI, CI, SP, RP, P, BN
## dollars: total auction dollars per team in the draft
## teams: total teams in the league
## mp: starts to qualify at a position for position players
## msp: starts to qualify as an SP for pitchers
## mrp: relief appearances to qualify as an RP for pitchers
## mb: minimum bid in the auction
## split: percent of dollars allocated to hitters
## lg: player universe, either MLB, AL, or NL
## points: starts with p for points league or c for roto 
## -- if p then the list of numbers after the first '|' corresponds to the number of points for the following categories in this order
## -- ['PA', 'H', 'S', 'D', 'T', 'HR', 'SO', 'BB', 'HBP', 'SB', 'CS', 'R', 'RBI'] and pitcher categories follow the second '|' in this order
## -- ['Out', 'QS', 'W', 'L', 'SV', 'HLD', 'K', 'BB', 'HBP', 'ER', 'R', 'H', 'HR']
## -- if c then the list of numbers after the first '|' corresponds to the index of the selected category in the batting_categories array
## -- likewise for pitching categories after the second '|'


points_URL='https://pitcherlist-api-staging.herokuapp.com/v4/leaderboard/?type=bat&pos=1,1,1,1,1,3,0,2,1,1,2,2,5,10&dollars=260&teams=12&mp=20&msp=5&mrp=5&mb=1&split=0.7&points=p|0,1,1,2,3,4,-1,1,1,1,-1,1,1|1,2,5,-5,5,2,1,-1,-1,-2,0,-1,0&lg=AL'
cats_URL='https://pitcherlist-api-staging.herokuapp.com/v4/leaderboard/?type=bat&pos=1,1,1,1,1,3,0,2,1,1,2,2,5,10&dollars=260&teams=12&mp=20&msp=5&mrp=5&mb=1&split=0.7&points=c|0,1,2,3,4|0,1,2,3,4&lg=NL'
parsed_url = urlparse(points_URL)
parameters = parse_qs(parsed_url.query)
#parameters

view = parameters['type'][0]
league_format = parameters['points'][0][0]

batting_categories = ['AVG', 'RBI', 'R', 'SB', 'HR', 'OBP', 'SLG', 'OPS', 'H', 'SO', 'S', 'D', 'T', 'TB', 'BB', 'RBI+R', 'xBH', 'SB-CS', 'wOBA']
pitching_categories = ['W', 'SV', 'ERA', 'WHIP', 'SO', 'AVG', 'K/9', 'BB/9', 'K/BB', 'IP', 'QS', 'HR', 'HLD', 'SV+HLD']

selected_batting_stats = []
selected_pitching_stats = []

url_bat_cats = parameters['points'][0].split('|')[1].split(',')
url_pitch_cats = parameters['points'][0].split('|')[2].split(',')

points_cats_batters = ['PA', 'H', 'S', 'D', 'T', 'HR', 'SO', 'BB', 'HBP', 'SB', 'CS', 'R', 'RBI']
points_cats_pitchers = ['Out', 'QS', 'W', 'L', 'SV', 'HLD', 'K', 'BB', 'HBP', 'ER', 'R', 'H', 'HR']

custom_points_batters = []
custom_points_pitchers = []

default_points_batters = [0, 0, 1, 2, 3, 4, -1, 1, 0, 1, 0, 1, 1]
default_points_pitchers = [1, 0, 5, -5, 5, 0, 1, -1, 0, -2, 0, -1, 0]

url_bat_points = parameters['points'][0].split('|')[1].split(',')
url_pitch_points = parameters['points'][0].split('|')[2].split(',')

if league_format == 'c':
    for cat in url_bat_cats:
        bat_placeholder = batting_categories[int(cat)]
        selected_batting_stats.append(bat_placeholder)
    for cat in url_pitch_cats:
        pitch_placeholder = pitching_categories[int(cat)]
        selected_pitching_stats.append(pitch_placeholder)
elif league_format == 'p':
    for cat in url_bat_points:
        custom_points_batters.append(int(cat))
    for cat in url_pitch_points:
        custom_points_pitchers.append(int(cat))

budget = int(parameters['dollars'][0])
min_bid = int(parameters['mb'][0])
teams = int(parameters['teams'][0])
bat_split = float(parameters['split'][0])
p_split = 1 - bat_split
player_universe = parameters['lg'][0]

pos_list = parameters['pos'][0].split(',')

roster_C = int(pos_list[0])
roster_1B = int(pos_list[1])
roster_2B = int(pos_list[2])
roster_3B = int(pos_list[3])
roster_SS = int(pos_list[4])
roster_OF = int(pos_list[5])
roster_DH = int(pos_list[6])
roster_UTIL = int(pos_list[7])
roster_MI = int(pos_list[8])
roster_CI = int(pos_list[9])
roster_SP = int(pos_list[10])
roster_RP = int(pos_list[11])
roster_P = int(pos_list[12])
roster_B = int(pos_list[13])

## read in the projection files
## these could be updated throughout the offseason as players move teams or change situations

df_hitters = pd.read_csv("2022_batters_jan4.csv")
df_starters = pd.read_csv("2022_starters_updated_feb21.csv")
df_relievers = pd.read_csv("2022_relievers_feb4.csv")

## read in position data for players
## this is another static csv file

df_positions = pd.read_csv("player_pos_data.csv")
merge_positions = df_positions[['idfangraphs', 'allpos']]
df_hitters_merged = df_hitters.merge(merge_positions, how='left', on='idfangraphs')
df_hitters_merged['allpos'] = df_hitters_merged['allpos'].fillna('DH')
df_hitters_merged['Position'] = df_hitters_merged['allpos'].str.split('/')
df_hitters_merged['MI'] = df_hitters_merged.apply(lambda x: ['MI'] if any(elem in x.Position  for elem in ['2B', 'SS']) else [], axis=1)
df_hitters_merged['CI'] = df_hitters_merged.apply(lambda x: ['CI'] if any(elem in x.Position  for elem in ['1B', '3B']) else [], axis=1)
df_hitters_merged['Pos'] = df_hitters_merged.apply(lambda x: x.Position + x.MI + x.CI + ['UTIL'], axis=1)

df_starters['Pos'] = df_starters.apply(lambda x: ['SP', 'P'], axis=1)
df_relievers['Pos'] = df_relievers.apply(lambda x: ['RP', 'P'], axis=1)
df_pitchers = pd.concat([df_starters, df_relievers]).fillna(0)

## Another csv file so we can determine player league
## Based on a players current team

df_leagues = pd.read_csv("team_leagues.csv")
df_hitters_merged = df_hitters_merged.merge(df_leagues, how='left', on='Team')
df_pitchers = df_pitchers.merge(df_leagues, how='left', on='Team')

# Derive certain stats not included in initial projection files

df_hitters_merged['OPS'] = df_hitters_merged.apply(lambda x: x['OBP'] + x['SLG'], axis=1)
df_hitters_merged['TB'] = df_hitters_merged.apply(lambda x: x['S'] + (2 * x['D']) + (3 * x['T']) + (4 * x['HR']), axis=1)
df_hitters_merged['RBI+R'] = df_hitters_merged.apply(lambda x: x['RBI'] + x['R'], axis=1)
df_hitters_merged['xBH'] = df_hitters_merged.apply(lambda x: x['D'] + x['T'] + x['HR'], axis=1)
df_hitters_merged['SB-CS'] = df_hitters_merged.apply(lambda x: x['SB'] - x['CS'], axis=1)
df_hitters_merged['HBP'] = 0

df_pitchers['Outs'] = df_pitchers.apply(lambda x: x.IP * 3, axis=1)
df_pitchers['AB'] = df_pitchers.apply(lambda x: x.Outs + x.H, axis=1)
df_pitchers['AVG'] = df_pitchers.apply(lambda x: round(x.H / x.AB, 3), axis=1)
df_pitchers['K/9'] = df_pitchers.apply(lambda x: round((x.SO / x.IP ) * 9, 1), axis=1)
df_pitchers['BB/9'] = df_pitchers.apply(lambda x: round((x.BB / x.IP) * 9, 1) , axis=1)
df_pitchers['K/BB'] = df_pitchers.apply(lambda x: round(x.SO / (x.BB + 0.01), 1) , axis=1)
df_pitchers['QS'] = df_pitchers.apply(lambda x: round(x.GS * .015 * x.GS, 0), axis=1)
df_pitchers['SV+HLD'] = df_pitchers.apply(lambda x: x.SV + x.HLD, axis=1)
df_pitchers['HBP'] = 0

## Functions to calculate total projected fantasy points for hitters and pitchers

def calculate_hitting(pa, h, b1, b2, b3, hr, so, bb, hbp, sb, cs, r, rbi, pa_points, h_points, b1_points, b2_points, b3_points, hr_points, so_points, bb_points, hbp_points, sb_points, cs_points, r_points, rbi_points):
    return ((int(pa) * pa_points) +
            (int(h) * h_points) +
            (int(b1) * b1_points) + 
            (int(b2) * b2_points) + 
            (int(b3) * b3_points) + 
            (int(hr) * hr_points) +
            (int(hbp) * hbp_points) +
            (int(sb) * sb_points) +
            (int(cs) * cs_points) +
            (int(r) * r_points) +
            (int(rbi) * rbi_points) +
            (int(bb) * bb_points) +
            (int(so) * so_points))

def calculate_pitching(out, qs, w, l, sv, hld, k, bb, hbp, er, r, h, hr, out_points, qs_points, w_points, l_points, sv_points, hld_points, k_points, bb_points, hbp_points, er_points, r_points, h_points, hr_points):
    return ((int(out) * out_points) +
           (int(qs) * qs_points) +
            (int(w) * w_points) +
            (int(l) * l_points) +
            (int(sv) * sv_points) +
            (int(hld) * hld_points) +
            (int(k) * k_points) +
            (int(bb) * bb_points) +
            (int(hbp) * hbp_points) +
            (int(er) * er_points) +
            (int(r) * r_points) +
            (int(h) * h_points) +
            (int(hr) * hr_points))

points_list_hitters = []
points_list_pitchers = []

if league_format == 'c':
    points_list_hitters = default_points_batters
    points_list_pitchers = default_points_pitchers
else:
    points_list_hitters = custom_points_batters
    points_list_pitchers = custom_points_pitchers
    

df_hitters_merged['FantasyPoints_Hitting'] = df_hitters_merged.apply(lambda x: calculate_hitting(x.PA,
                                                                       x.H,
                                                                       x.S, 
                                                                       x.D,                       
                                                                       x['T'],
                                                                       x.HR,                                                               
                                                                       x.SO,
                                                                       x.BB,
                                                                       x.HBP,
                                                                       x.SB,
                                                                       x.CS,                          
                                                                       x.R,
                                                                       x.RBI,
                                                                       points_list_hitters[0],
                                                                       points_list_hitters[1],
                                                                       points_list_hitters[2],
                                                                       points_list_hitters[3],
                                                                       points_list_hitters[4], 
                                                                       points_list_hitters[5],
                                                                       points_list_hitters[6],
                                                                       points_list_hitters[7],
                                                                       points_list_hitters[8],
                                                                       points_list_hitters[9],
                                                                       points_list_hitters[10],
                                                                       points_list_hitters[11], 
                                                                       points_list_hitters[12]),axis=1)

df_pitchers['FantasyPoints_Pitching'] = df_pitchers.apply(lambda x: calculate_pitching(x.Outs,
                                                                       x.QS,
                                                                       x.W, 
                                                                       x.L,                       
                                                                       x.SV,
                                                                       x.HLD,                                                               
                                                                       x.SO,
                                                                       x.BB,
                                                                       x.HBP,
                                                                       x.ER,
                                                                       x.R,                          
                                                                       x.H,
                                                                       x.HR,
                                                                       points_list_pitchers[0],
                                                                       points_list_pitchers[1],
                                                                       points_list_pitchers[2],
                                                                       points_list_pitchers[3],
                                                                       points_list_pitchers[4], 
                                                                       points_list_pitchers[5],
                                                                       points_list_pitchers[6],
                                                                       points_list_pitchers[7],
                                                                       points_list_pitchers[8],
                                                                       points_list_pitchers[9],
                                                                       points_list_pitchers[10],
                                                                       points_list_pitchers[11], 
                                                                       points_list_pitchers[12]),axis=1)

## Pare down the list of players to fit with the teams/roster/universe req's

if player_universe == 'AL':
    df_hitters_merged = df_hitters_merged.loc[(df_hitters_merged['Lg'] == 'AL') | (df_hitters_merged['Lg'] == 'FA')]
    df_pitchers = df_pitchers.loc[(df_pitchers['Lg'] == 'AL') | (df_pitchers['Lg'] == 'FA')]
elif player_universe == 'NL':
    df_hitters_merged = df_hitters_merged.loc[(df_hitters_merged['Lg'] == 'NL') | (df_hitters_merged['Lg'] == 'FA')]
    df_pitchers = df_pitchers.loc[(df_pitchers['Lg'] == 'NL') | (df_pitchers['Lg'] == 'FA')]
else:
    pass
    
df_list_hitters = []
df_list_pitchers = []

rosters_hit = [roster_C, roster_2B, roster_SS, roster_OF, roster_3B, roster_1B, roster_DH, roster_MI, roster_CI, roster_UTIL]
rosters_pit = [roster_SP, roster_RP, roster_P]

positions_hit = ['C', '2B', 'SS', 'OF', '3B', '1B', 'DH', 'MI', 'CI', 'UTIL']
positions_pitch = ['SP', 'RP', 'P']

df_hit_pared = df_hitters_merged
df_pitch_pared = df_pitchers

i = 0
for pos in positions_hit:
    sort_by = 'FantasyPoints_Hitting'
    if i == 0:
        df_pos = df_hitters_merged[df_hitters_merged['Pos'].apply(lambda x: pos in x)].sort_values(by=[sort_by], ascending=False).reset_index(drop=True)
    else:
        df_pos = df_hit_pared[df_hit_pared['Pos'].apply(lambda x: pos in x)].sort_values(by=[sort_by], ascending=False).reset_index(drop=True)
    num_pos = teams * rosters_hit[i]
    df_roster = df_pos.head(num_pos)
    df_roster.insert(0, 'selected_pos', pos)
    df_list_hitters.append(df_roster)
    chosen_players = df_roster['idfangraphs'].to_list()
    df_hit_pared.loc[:, 'selected'] = df_hit_pared.apply(lambda x: 1 if x.idfangraphs in chosen_players else 0, axis=1)
    df_hit_pared = df_hit_pared[df_hit_pared['selected'] < 1]
    i+=1
    
j = 0
for pos in positions_pitch:
    sort_by = 'FantasyPoints_Pitching'
    if j == 0:
        df_pos = df_pitchers[df_pitchers['Pos'].apply(lambda x: pos in x)].sort_values(by=[sort_by], ascending=False).reset_index(drop=True)
    else:
        df_pos = df_pitch_pared[df_pitch_pared['Pos'].apply(lambda x: pos in x)].sort_values(by=[sort_by], ascending=False).reset_index(drop=True)
    num_pos = teams * rosters_pit[j]
    df_roster = df_pos.head(num_pos)
    df_roster.insert(0, 'selected_pos', pos)
    df_list_pitchers.append(df_roster)
    chosen_players = df_roster['idfangraphs'].to_list()
    df_pitch_pared.loc[:, 'selected'] = df_pitch_pared.apply(lambda x: 1 if x.idfangraphs in chosen_players else 0, axis=1)
    df_pitch_pared = df_pitch_pared[df_pitch_pared['selected'] < 1]
    j+=1
    
draft_pool_hitters = pd.concat(df_list_hitters)
bench_pool_hitters = df_hit_pared
draft_pool_pitchers = pd.concat(df_list_pitchers)
bench_pool_pitchers = df_pitch_pared

batting_stats_dict = {
    'AVG': 'mHaAVG',
    'RBI': 'mRBI',
    'R': 'mR',
    'SB': 'mSB',
    'HR': 'mHR',
    'OBP': 'mOBaAVG',
    'SLG': 'mTBaAVG',
    'OPS': 'mOPSaAVG',
    'H': 'mH',
    'SO': 'mSO',
    'S': 'mS',
    'D': 'mD',
    'T': 'mT',
    'TB': 'mTB',
    'BB': 'mBB',
    'RBI+R': 'mRBI+R',
    'xBH': 'mxBH',
    'SB-CS': 'mSB-CS',
    'wOBA': 'mwOBA'
}

pitching_stats_dict = {
    'W': 'mW',
    'SV': 'mSV',
    'ERA': 'mERaAVG',
    'WHIP': 'mWHaAVG',
    'SO': 'mSO',
    'AVG': 'mHaAVG',
    'K/9': 'mK/9',
    'BB/9': 'mBB/9',
    'K/BB': 'mK/BB',
    'IP': 'mIP',
    'QS': 'mQS',
    'HR': 'mHR',
    'HLD': 'mHLD',
    'SV+HLD': 'mSV+HLD',
}

## Derive marginal player value in roto leagues

if league_format == 'c':
    league_avg = sum(draft_pool_hitters.H.to_list()) / sum(draft_pool_hitters.AB.to_list())
    league_obp = (sum(draft_pool_hitters.H.to_list()) + sum(draft_pool_hitters.BB.to_list())) / sum(draft_pool_hitters.PA.to_list())
    league_slg = sum(draft_pool_hitters.TB.to_list()) / sum(draft_pool_hitters.AB.to_list())
    league_woba = ((sum(draft_pool_hitters.BB.to_list()) * .692) + (sum(draft_pool_hitters.S.to_list()) * .879) + (sum(draft_pool_hitters.D.to_list()) * 1.242) + (sum(draft_pool_hitters['T'].to_list()) * 1.568) + (sum(draft_pool_hitters.HR.to_list()) * 2.007)) / (sum(draft_pool_hitters.AB.to_list()) + sum(draft_pool_hitters.BB.to_list()))

    draft_pool_hitters['HaAVG'] = draft_pool_hitters.apply(lambda x: x.H - (x.AB * league_avg), axis=1)
    draft_pool_hitters['OBaAVG'] = draft_pool_hitters.apply(lambda x: (x.H + x.BB) - (x.PA * league_obp), axis=1)
    draft_pool_hitters['TBaAVG'] = draft_pool_hitters.apply(lambda x: x.TB - (x.AB * league_slg), axis=1)
    draft_pool_hitters['OPSaAVG'] = draft_pool_hitters.apply(lambda x: x.OBaAVG + x.TBaAVG, axis=1)
    draft_pool_hitters['wOBAaAVG'] = draft_pool_hitters.apply(lambda x: ((x.BB * .692) + (x.S * .879) + (x.D * 1.242) + (x['T'] * 1.568) + (x.HR * 2.007)) - ((x.BB + x.AB) * league_woba), axis=1)

    league_era = sum(draft_pool_pitchers.ER.to_list()) / (sum(draft_pool_pitchers.IP.to_list()) / 9)
    league_whip = (sum(draft_pool_pitchers.BB.to_list()) + sum(draft_pool_pitchers.H.to_list())) / sum(draft_pool_pitchers.IP.to_list())
    league_avg_p = sum(draft_pool_pitchers.H.to_list()) / sum(draft_pool_pitchers.AB.to_list())
    
    draft_pool_pitchers['ERaAVG'] = draft_pool_pitchers.apply(lambda x: ((x.IP / 9) * league_era) - x.ER, axis=1)
    draft_pool_pitchers['WHaAVG'] = draft_pool_pitchers.apply(lambda x: (x.IP * league_whip) - (x.H + x.BB), axis=1)
    draft_pool_pitchers['HaAVG'] = draft_pool_pitchers.apply(lambda x: (x.AB * league_avg_p) - x.H, axis=1)
    
    all_cats_bat = batting_categories + ['HaAVG', 'OBaAVG', 'TBaAVG', 'OPSaAVG', 'wOBAaAVG']
    all_cats_pitch = pitching_categories + ['ERaAVG', 'WHaAVG', 'HaAVG']

    agg_stats_bat = draft_pool_hitters[all_cats_bat]
    agg_stats_pitch = draft_pool_pitchers[all_cats_pitch]

    analysis_bat = agg_stats_bat.describe()
    analysis_pitch = agg_stats_pitch.describe()
    
    for cat in all_cats_bat:
        draft_pool_hitters['m' + cat] = draft_pool_hitters.apply(lambda x: (x[cat] - analysis_bat.at['mean', cat]) / (analysis_bat.at['std', cat]), axis=1)

    for cat in all_cats_pitch:
        draft_pool_pitchers['m' + cat] = draft_pool_pitchers.apply(lambda x: (x[cat] - analysis_pitch.at['mean', cat]) / (analysis_pitch.at['std', cat]), axis=1)
    
    selected_mstats_bat = []
    for stat in selected_batting_stats:
        mstat = batting_stats_dict[stat]
        selected_mstats_bat.append(mstat)
    draft_stats_hitters = draft_pool_hitters
    draft_stats_hitters.loc[:, 'mV'] = draft_stats_hitters[selected_mstats_bat].sum(axis=1)

    selected_mstats_pitch = []
    for stat in selected_pitching_stats:
        mstat = pitching_stats_dict[stat]
        selected_mstats_pitch.append(mstat)
    draft_stats_pitchers = draft_pool_pitchers
    draft_stats_pitchers.loc[:, 'mV'] = draft_stats_pitchers[selected_mstats_pitch].sum(axis=1)
## Derive marginal value for players in points leagues

if league_format == 'p':
    agg_stats_bat = draft_pool_hitters['FantasyPoints_Hitting']
    agg_stats_pitch = draft_pool_pitchers['FantasyPoints_Pitching']

    analysis_bat = agg_stats_bat.describe()
    analysis_pitch = agg_stats_pitch.describe()

    draft_pool_hitters['mV'] = draft_pool_hitters.apply(lambda x: (x['FantasyPoints_Hitting'] - analysis_bat['mean']) / (analysis_bat['std']), axis=1)
    draft_pool_pitchers['mV'] = draft_pool_pitchers.apply(lambda x: (x['FantasyPoints_Pitching'] - analysis_pitch['mean']) / (analysis_pitch['std']), axis=1)
    
    draft_stats_hitters = draft_pool_hitters
    draft_stats_pitchers = draft_pool_pitchers

## Determine positional value

selected_positions_bat = list(set(draft_stats_hitters['selected_pos'].to_list()))
selected_positions_pitch = list(set(draft_stats_pitchers['selected_pos'].to_list()))

positional_adjustment = {}
for pos in selected_positions_bat:
    adj = min(draft_stats_hitters[draft_stats_hitters['selected_pos'] == pos]['mV'])
    positional_adjustment[pos] = -adj

for pos in selected_positions_pitch:
    adj = min(draft_stats_pitchers[draft_stats_pitchers['selected_pos'] == pos]['mV'])
    positional_adjustment[pos] = -adj

## Find total marginal value based on stats/position

draft_stats_hitters.loc[:, 'mPos'] = draft_stats_hitters.apply(lambda x: positional_adjustment[x.selected_pos], axis=1)
draft_stats_pitchers.loc[:, 'mPos'] = draft_stats_pitchers.apply(lambda x: positional_adjustment[x.selected_pos], axis=1)

draft_stats_hitters.loc[:, 'm$'] = draft_stats_hitters.apply(lambda x: x.mV + x.mPos, axis=1)
draft_stats_pitchers.loc[:, 'm$'] = draft_stats_pitchers.apply(lambda x: x.mV + x.mPos, axis=1)

total_value_hitters = sum(draft_stats_hitters['m$'])
dollars_spent_hitters = (budget * teams * bat_split) - (teams * sum(rosters_hit))
dollars_per_value_hitters = dollars_spent_hitters / total_value_hitters

total_value_pitchers = sum(draft_stats_pitchers['m$'])
dollars_spent_pitchers = (budget * teams * p_split) - (teams * sum(rosters_pit))
dollars_per_value_pitchers = dollars_spent_pitchers / total_value_pitchers

## Find final dollar totals based on league settings

draft_stats_hitters.loc[:, 'auction$'] = draft_stats_hitters.apply(lambda x: round((x['m$'] * dollars_per_value_hitters) + 1, 1), axis=1)
draft_stats_pitchers.loc[:, 'auction$'] = draft_stats_pitchers.apply(lambda x: round((x['m$'] * dollars_per_value_pitchers) + 1, 1), axis=1)

## Determine value for 'bench' pool of players

if league_format == 'p':
    bench_pool_hitters['mV'] = bench_pool_hitters.apply(lambda x: (x['FantasyPoints_Hitting'] - analysis_bat['mean']) / (analysis_bat['std']), axis=1)
    bench_pool_pitchers['mV'] = bench_pool_pitchers.apply(lambda x: (x['FantasyPoints_Pitching'] - analysis_pitch['mean']) / (analysis_pitch['std']), axis=1)
elif league_format == 'c':
    bench_pool_hitters['HaAVG'] = bench_pool_hitters.apply(lambda x: x.H - (x.AB * league_avg), axis=1)
    bench_pool_hitters['OBaAVG'] = bench_pool_hitters.apply(lambda x: (x.H + x.BB) - (x.PA * league_obp), axis=1)
    bench_pool_hitters['TBaAVG'] = bench_pool_hitters.apply(lambda x: x.TB - (x.AB * league_slg), axis=1)
    bench_pool_hitters['OPSaAVG'] = bench_pool_hitters.apply(lambda x: x.OBaAVG + x.TBaAVG, axis=1)
    bench_pool_hitters['wOBAaAVG'] = bench_pool_hitters.apply(lambda x: ((x.BB * .692) + (x.S * .879) + (x.D * 1.242) + (x['T'] * 1.568) + (x.HR * 2.007)) - ((x.BB + x.AB) * league_woba), axis=1)

    bench_pool_pitchers['ERaAVG'] = bench_pool_pitchers.apply(lambda x: ((x.IP / 9) * league_era) - x.ER, axis=1)
    bench_pool_pitchers['WHaAVG'] = bench_pool_pitchers.apply(lambda x: (x.IP * league_whip) - (x.H + x.BB), axis=1)
    bench_pool_pitchers['HaAVG'] = bench_pool_pitchers.apply(lambda x: (x.AB * league_avg_p) - x.H, axis=1)
    
    for cat in all_cats_bat:
        bench_pool_hitters['m' + cat] = bench_pool_hitters.apply(lambda x: (x[cat] - analysis_bat.at['mean', cat]) / (analysis_bat.at['std', cat]), axis=1)

    for cat in all_cats_pitch:
        bench_pool_pitchers['m' + cat] = bench_pool_pitchers.apply(lambda x: (x[cat] - analysis_pitch.at['mean', cat]) / (analysis_pitch.at['std', cat]), axis=1)
    
    bench_pool_hitters.loc[:, 'mV'] = bench_pool_hitters[selected_mstats_bat].sum(axis=1)
    bench_pool_pitchers.loc[:, 'mV'] = bench_pool_pitchers[selected_mstats_pitch].sum(axis=1)

bench_pool_hitters['selected_pos'] = bench_pool_hitters.apply(lambda x: x.Pos[0], axis=1)
bench_pool_pitchers['selected_pos'] = bench_pool_pitchers.apply(lambda x: x.Pos[0], axis=1)

bench_pool_hitters['mPos'] = bench_pool_hitters.apply(lambda x: positional_adjustment[x.selected_pos] if x.selected_pos in positional_adjustment else 0, axis=1)
bench_pool_pitchers['mPos'] = bench_pool_pitchers.apply(lambda x: positional_adjustment[x.selected_pos] if x.selected_pos in positional_adjustment else 0, axis=1)

bench_pool_hitters['mPos'].fillna(0, inplace=True)
bench_pool_pitchers['mPos'].fillna(0, inplace=True)

bench_pool_hitters['m$'] = bench_pool_hitters.apply(lambda x: x.mV + x.mPos, axis=1)
bench_pool_pitchers['m$'] = bench_pool_pitchers.apply(lambda x: x.mV + x.mPos, axis=1)

bench_pool_hitters['auction$'] = bench_pool_hitters.apply(lambda x: round((x['m$'] * dollars_per_value_hitters) + 1, 1), axis=1)
bench_pool_pitchers['auction$'] = bench_pool_pitchers.apply(lambda x: round((x['m$'] * dollars_per_value_pitchers) + 1, 1), axis=1)

## Form final tables with relevant columns/headers

draft_stats_hitters = draft_stats_hitters[['Name', 'Team', 'PA', 'H', 'S', 'D', 'T', 'HR', 'R', 'RBI', 'SB', 'CS', 'SO', 'BB', 'AVG', 'OBP', 'SLG', 'OPS', 'auction$']]
bench_pool_hitters = bench_pool_hitters[['Name', 'Team', 'PA', 'H', 'S', 'D', 'T', 'HR', 'R', 'RBI', 'SB', 'CS', 'SO', 'BB', 'AVG', 'OBP', 'SLG', 'OPS', 'auction$']]
final_hitter_df = pd.concat([draft_stats_hitters, bench_pool_hitters])
final_hitter_df = final_hitter_df.sort_values(by=['auction$'], ascending=False)
final_hitter_df = final_hitter_df.reset_index(drop=True).reset_index()
final_hitter_df['Rank'] = final_hitter_df['index'].rank()
cols = list(final_hitter_df)
cols.insert(0, cols.pop(cols.index('Rank')))
final_hitter_df = final_hitter_df.loc[:, cols]
final_hitter_df.drop(['index'], axis=1, inplace=True)
final_hitter_df.rename(columns={"H": "Hits", "S": "1B", 'D': '2B', 'T': '3B', 'auction$': 'Dollars'}, inplace=True)

draft_stats_pitchers = draft_stats_pitchers[['Name', 'Team', 'GS', 'G', 'IP', 'W', 'L', 'QS', 'SV', 'HLD', 'ERA', 'WHIP', 'H', 'HR', 'SO%', 'BB%', 'SO', 'BB', 'auction$']]
bench_pool_pitchers = bench_pool_pitchers[['Name', 'Team', 'GS', 'G', 'IP', 'W', 'L', 'QS', 'SV', 'HLD', 'ERA', 'WHIP', 'H', 'HR', 'SO%', 'BB%', 'SO', 'BB', 'auction$']]
final_pitcher_df = pd.concat([draft_stats_pitchers, bench_pool_pitchers])
final_pitcher_df = final_pitcher_df.sort_values(by=['auction$'], ascending=False)
final_pitcher_df = final_pitcher_df.reset_index(drop=True).reset_index()
final_pitcher_df['Rank'] = final_pitcher_df['index'].rank()
cols = list(final_pitcher_df)
cols.insert(0, cols.pop(cols.index('Rank')))
final_pitcher_df = final_pitcher_df.loc[:, cols]
final_pitcher_df.drop(['index'], axis=1, inplace=True)
final_pitcher_df.rename(columns={"H": "Hits", "SO%": "K%", 'SO': 'K', 'auction$': 'Dollars'}, inplace=True)

## Program generates both pitcher and hitter csv's separately
## I have it set up so the initial 'Type' parameter in the url indicates whether to return hitter or pitcher tables
## to the webpage

if view == 'pitch':
    final_pitcher_df.to_csv('pitcher_value.csv', index=False)
else:
    final_hitter_df.to_csv('hitter_value.csv', index=False)






