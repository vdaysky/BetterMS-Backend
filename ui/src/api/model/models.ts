import {Model, Field, Str, Bool, Int, Page, Computed, modelTypes, Struct} from './modelBase';



export class Map extends Model {

    declare id: number;
    declare _name: string;
    declare display_name: string;

    static id = Int;
    static _name = Field(Str, {alias: 'name'});
    static display_name = Str;
}

enum GameMode {
    Competitive = 0,
    Public = 1,
    DeathMatch = 2,
    Duel = 3,
    Practice = 4,
    Ranked = 5,
}

export enum GameStatus {
    NotStarted,
    Started,
    Finished,
    Terminated
}

export class Game extends Model {


    declare id: number;
    declare name: string;
    declare created_at: string;
    declare started_at: string;
    declare map: Map;
    // declare is_started: boolean;
    // declare is_finished: boolean;
    declare score_a: number;
    declare score_b: number;
    declare team_a: InGameTeam;
    declare team_b: InGameTeam;
    declare status: GameStatus;
    declare match: Match;
    declare whitelist: Player[];
    declare blacklist: Player[];
    declare _mode: GameMode;

    static id = Int;
    static map = Field(Map);
    // static is_started = Bool;
    // static is_finished = Bool;
    static created_at = Str;
    static started_at = Str;
    static score_a = Int;
    static score_b = Int;
    static team_a = Field('InGameTeam');
    static team_b = Field('InGameTeam');
    static winner = Field('InGameTeam');
    static match = Field('Match');
    static whitelist = Field('Player', {list: true});
    static blacklist = Field('Player', {list: true});
    static _mode = Field(Int, {alias: 'mode'});
    static status = Field(Int);

    isFull() {
        return (this?.team_a?.players?.length||0) + (this?.team_b?.players?.length||0) >= 10;
    }
    hasPlayer(player: Player) {
        if (!this.team_a) return false;
        return this.team_a.players.some(p => p.id == player.id) || this.team_b.players.some(p => p.id == player.id);
    }
    playerCount() {
        return (this?.team_a?.players?.length||0) + (this?.team_b?.players?.length||0)
    }

    mode(): string | undefined {
        const modeMap = {
            '0': "Competitive",
            '1': "Public",
            '2': "DeathMatch",
            '3': "Duel",
            '4': "Practice",
            '5': "Ranked",
            '6': 'Gun Game',
        };
        return modeMap[this._mode];
    }
}

export class Team extends Model {

    declare id: number;


    static id = Int;
    static short_name = Str;
    static full_name = Str;
    static elo = Int;
    static players = Field('Player', {list: true});

}

export class PlayerPermission extends Model {
    declare id: number;
    declare _name: string;

    static _name = Field(Str, {alias: 'name'});
}

export class Role extends Model {

    declare id: number;
    declare _name: string;
    declare permissions: PlayerPermission[];

    static _name = Field(Str, {alias: 'name'});
    static permissions = Field(PlayerPermission, {list: true});
}

export class Player extends Model {

    declare id: number;
    declare uuid: string;
    // declare username: string;
    declare elo: number;
    // declare in_server: boolean;
    // declare on_website: boolean;
    declare game: Game;
    declare team: Team;
    declare role: Role;
    declare username: string;
    declare games_played: number;
    declare winrate: number;
    declare last_seen: string;
    declare in_server: boolean;
    declare active_game: Game;

    static id = Int;
    static username = Str;
    static team = Field(Team);
    static uuid = Str;
    static role = Field(Role);
    // static username = Str;
    static elo = Int;
    static in_server = Bool;
    static games_played = Int;
    static winrate = Int;
    static last_seen = Str;
    static active_game = Field(Game);
    // static on_website = Bool;
    // static game = Field(Game);

    isAuthenticated() {
        return this.uuid != null;
    }

    isInTeam(team: Team) {
        if (!team) return false;
        console.log("is in team", team, this.team);
        if (this.team == null) return false;
        console.log("is in team", this.team.id == team.id);
        return this.team.id == team.id;
    }
    isOnTeam() {
        return this.team != null;
    }

    hasPermission(permission: string) {

        const testPerm = (a: string, b: string) => {

            if  (!b) return false;

            const present = b.split(".");
            const required = a.split(".");
            
            // if the present permission is more specific than the required one, it is not a match
            if (required.length < present.length) {
                return false;
            }

            // iterate over both at the same time
            for (let i = 0; i < Math.max(present.length, required.length); i++) {
                
                // present permission ended earlier, and it did not have a wildcard
                if (present.length == i + 2) {
                    return false;
                }
                

                if (present[i] != required[i]) {
                    return present[i] == "*";
                }
            }
            return true;
        }
        
        if (!this.role) return false;

        for (const perm of this.role.permissions) {
            if (testPerm(permission, perm._name)) return true;
        }

        return false;
    }
}


export class PlayersView extends Model {
    static players = Computed(Page(Player), {page: 0, size: 10});
}


export class MatchTeam extends Model {

    declare id: number;
    declare _name: string;
    declare players: Player[];
    declare team: Team;

    static id = Int;
    static _name = Field(Str, {alias: 'name'});
    static players = Field(Player, {list: true});
    static team = Field(Team);
    // static in_game_team = Field('InGameTeam');
}

export class MapPick extends Model {

    declare selected_by: MatchTeam;
    declare map: Map;
    declare picked: boolean | null;
    declare id: number;

    static id = Int;
    static selected_by = Field(MatchTeam);
    static map = Field(Map);
    static picked = Bool;


    isSelected() {
        return this.selected_by != null;
    }

    isBanned() {
       return this.picked === false;
    }

    isPicked() {
        return this.picked === true;
    }
}

export class MapPickProcess extends Model {

    declare id: number;
    declare maps: MapPick[];
    declare turn: Player;
    declare next_action: string;
    declare finished: boolean;
    declare match: Match;
    declare picker_a: Player;
    declare picker_b: Player;

    static maps = Field(MapPick, {list: true});
    static turn = Field(Player);
    // 1 = ban, 2 = pick, 3 = default, 0 = null
    static next_action = Str;
    static finished = Bool;
    static match = Field('Match');
    static picker_a = Field(Player);
    static picker_b = Field(Player);

}

export class Match extends Model {

    declare id: number;
    declare _name: string;
    declare team_one: MatchTeam;
    declare team_two: MatchTeam;
    declare map_pick_process: MapPickProcess;
    declare games: Game[];
    
    static id = Int;
    static _name = Field(String, {alias: 'name'});
    static team_one = Field(MatchTeam);
    static team_two = Field(MatchTeam);
    static map_pick_process = Field(MapPickProcess);
    static games = Field(Game, {list: true});
}

export class Event extends Model {
    static matches = Field(Match, {list: true});
    static _name = Field(Str, {alias: 'name'});
    static start_date = Str;
}


class PlayerSession extends Model {
    declare roster_id: number;
    declare game_id: number;
}

export class InGameTeam extends Model {

    declare id: number;
    declare _name: string;
    declare players: Player[];
    declare is_ct: boolean;
    declare starts_as_ct: boolean;

    static id = Int;
    static _name = Field(Str, {alias: 'name'});
    static players = Field(Player, {list: true});
    static is_ct = Bool;
    static starts_as_ct = Bool;
}

InGameTeam.declareDependency(
    PlayerSession,
    {
        events: ['Create'],
        where: {
            id: "roster_id"
        }
    }
);

InGameTeam.declareDependency(PlayerSession, {
    events: ['Delete']
});

export class Round extends Model {
    static game = Field(Game);
    static number = Int;
    static winner = Field(InGameTeam);
}

export class GamePlayerEvent extends Model {
    static event = Str;
    static game = Field(Game);
    static player = Field(Player);
    static round = Field(Round);
    static is_ct = Bool;
}

export class AnonymousPlayer {
    hasPermission() {
        return false;
    }
    isAuthenticated() {
        return false;
    }

    team = null;
    owned_team = null;

    isInTeam() {
        return false;
    }
}

export class FftPlayer extends Model {
    static uuid = Str;
    static username = Str;
    static invited = Bool;
    static id = Int;
}

export class FftPlayerView extends Model {
    static players = Computed(Page(FftPlayer), {page: 0, size: 10});
}

export class TopPlayersView extends Model {
    static players = Computed(Page(Player), {page: 0, size: 10});
}

export class PlayerPerformanceAggregatedView extends Model {

    declare kills: number;
    declare deaths: number;
    declare recent_games: Game[];
    static kills = Int;
    static deaths = Int;
    static assists = Int;
    static hs = Int;
    static player = Field(Player);

    static games_played = Int;
    static games_won = Int;

    static ranked_games_played = Int;
    static ranked_games_won = Int;

    static recent_games = Computed(Page(Game), {page:0, size: 10});

    kd() {
        return Math.round((this.kills || 0) / (this.deaths || 1) * 100) / 100;
    }
}

class PlayerStats extends Struct {

    declare kills: number;
    declare deaths: number;
    declare assists: number;
    declare hs: number;
    declare player: Player;

    static kills = Int;
    static deaths = Int;
    static assists = Int;
    static hs = Int;
    static player = Field(Player);

    kd() {
        return Math.round((this.kills || 0) / (this.deaths || 1) * 100) / 100;
    }
}

export class GameStatsView extends Model {
    static stats = Field(PlayerStats, {list: true});
}

GameStatsView.declareDependency(PlayerSession, {
    events: ['Create'],
    predicate: (newVal, changes, self) => {
        return changes.roster_id == self.findDependency('InGameTeam')?.obj_id
    }
});

GameStatsView.declareDependency(PlayerSession, {
    events: ['Update', 'Delete'], // updates are tricky, I need to access old roster_id value to see if player left on update
});


export class TopTeamView extends Team {}

export class PubsView extends Model {
    declare games: Game[];
    declare online_player_count: number;

    static games = Field(Game, {list: true});
    static online_player_count = Int;
}

PubsView.declareDependency(
    PlayerSession,
    {
        events: ['Create', 'Update'],
        predicate: (newVal, changes, self) => {

            for (const game of self.games) {
                if (game.id == changes.game_id) {
                    return true;
                }
            }
            return false;
        }
    }
)

PubsView.declareDependency(Game, {});

export class GunGameView extends Model {
    static games = Field(Game, {list: true});
    static online_player_count = Int;
}

GunGameView.declareDependency(PlayerSession, {});
GunGameView.declareDependency(Game, {});

export class DeathMatchView extends Model {
    static games = Field(Game, {list: true});
    static online_player_count = Int;
}

DeathMatchView.declareDependency(PlayerSession, {});
DeathMatchView.declareDependency(Game, {});

export class DuelsView extends Model {
    static games =  Field(Game, {list: true});
    static online_player_count = Int;
}

DuelsView.declareDependency(PlayerSession, {});
DuelsView.declareDependency(Game, {});

export class GameModeStatsView extends Model {
    static ranked_online = Int;
    static pubs_online = Int;
    static duels_online = Int;
    static deathmatch_online = Int;
    static ranked_games = Int;
    static pubs_games = Int;
    static duels_games = Int;
    static deathmatch_games = Int;
    static gungame_online = Int;
    static gungame_games = Int;
}

export class PlayerQueue extends Model {

    declare players: Player[];
    declare id: number;
    declare type: number;
    declare size: number;
    declare locked: boolean;
    declare confirmed: boolean;
    declare confirmed_count: number;
    declare confirmed_by_me: boolean;
    declare match: Match;
    declare captain_a: Player;
    declare captain_b: Player;
    declare confirmed_players: Player[];

    static id = Int;
    static players = Field(Player, {list: true});
    static type = Int;
    static size = Int;
    static locked = Bool;
    static confirmed = Bool;
    static confirmed_players = Field(Player, {list: true});
    static confirmed_by_me = Bool;

    static match = Field(Match);
    static captain_a = Field(Player);
    static captain_b = Field(Player);
}

export class RankedView extends Model {

    declare queues: PlayerQueue[];
    declare my_queue: PlayerQueue;

    static queues = Field(PlayerQueue, {list: true});
    static my_queue = Field(PlayerQueue);
}

export class Post extends Model {
    static title = Str;
    static subtitle = Str;
    static text = Str;
    static author = Field(Player);
    static date = Str;
    static header_image = Str;
}

for (const model of [
    MatchTeam, PlayerQueue, GameStatsView, Map, Game, Team, Player,
    MapPick, MapPickProcess, Match, Event, GamePlayerEvent, InGameTeam, Role, PlayerPermission
]) {
    modelTypes[model.name] = model;
}

export class GamesView extends Model {
    static games = Computed(Page(Game), {page:0, size: 10});
}
