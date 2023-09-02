import {Game, Player, PlayerQueue, Map as GameMap, MapPick} from "./model/models";

const BASSE_URL = "http://" +  window.location.hostname + ":8000"

class ApiError extends Error {

    declare message: string;
    declare detail: any[] | undefined;

    constructor(message: string, detail?: any[]) {
        super(message)
        this.message = message;
        this.detail = detail;
    }
}

class ApiBase {

    apiUrl: string

    constructor() {
        this.apiUrl = "http://" + window.location.hostname + ":8000"
    }

    async get(url: string, data?:{[key: string]: any}) {
        const r = await fetch(this.apiUrl + '/api/' + url + "?" + new URLSearchParams(data), {headers: {session_id: localStorage.sessionAuthKey}});
        if (r.headers.has("session_id")) {
            localStorage.sessionAuthKey = r.headers.get("session_id");
        }
        
        const content = await r.json();

        if (r.status != 200) {
            throw new ApiError(content.message);
        }

        return content;
    }
    async post(url: string, data?:{[key: string]: any}) {
        const r = await fetch(this.apiUrl + '/api/' + url, {method: 'post', body: JSON.stringify(data), headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                session_id: localStorage.sessionAuthKey
            }
        });

        if (r.headers.has("session_id")) {
            localStorage.sessionAuthKey = r.headers.get("session_id");
        }

        const content = await r.json();

        if (r.status != 200) {
            throw new ApiError(content.message, content.detail);
        }

        return content;
    }

    async graphql(query: string) { // model, id, fields, fieldIds
        /** Make a GraphQL query to the API
         * model - string name of model to query
         * id - id of model to query, could be complex ID represented by object, or null
         * fields - array of field names to query
         * fieldIds - array of parameters to query for each field, could be undefined
         */
        
        query = `query { ${query} }`;

        console.log(query);

        const response = await fetch(BASSE_URL + '/graphql/', {
            method: 'post', 
            body: JSON.stringify({query: query}), 
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'session_id': localStorage['session_id']
            }
        });

        const {errors, data} = (await response.json());
        if (errors) {
            console.error(errors);
            for (const error of errors) {
                console.error(error.message);
            }
            throw Error("GraphQL Request failed: See above");
        }
        return data[Object.keys(data)[0]];
    }
}


export class MsApi extends ApiBase {
    async resolveUUID(uuid: string) {
        return await this.get(`player/${uuid}/name`);
    }

    async getUUID(name: string) {
        return await this.post("player/uuid", {name});
    }

    async getNameStatus(name: string) {
        const response = await this.get("auth/name/status", {name});
        return response.status;
    }

    async getMe() {
        const response = await this.get("auth/me");
        return Player.Find(response.player_id);
    }

    async logout() {
        return await this.post("auth/logout");
    }

    async login(username: string, password: string) {
        const response = await this.post("auth/login", {username, password});
        localStorage.sessionAuthKey = response.session_key;
        return Player.Find(response.player_id as number);
    }

    async register(username: string, password: string, verification_code: string) {
        const response = await this.post("auth/register", {username, password, verification_code});
        localStorage.sessionAuthKey = response.session_key;
        return Player.Find(response.player_id as number);
    }

    async createEvent({name, start_date}: {name: string, start_date: string}) {
        return await this.post("event/create", {name, start_date});
    }

    async createGame({match, map}: {match: number, map: string}) {
        return await this.post("game/create", {match, map});
    }

    async createMatch({name, start_date, event, team_a, team_b, map_count}: {name: string, start_date: string, event: number, team_a: number, team_b: number, map_count: number}) {
        return await this.post("match/create", {name, start_date, event, team_a, team_b, map_count});
    }

    async mapPickAction(map: MapPick) {
        return await this.post("match/map-pick", {map: map.objectID});
    }

    async getFFTPlayers() {
        return await this.get("player/fft");
    }

    async invitePlayer(player: Player) {
        return await this.post("player/invite", {player_id: player.id});
    }

    async acceptInvite(invite: number) {
        return await this.post("player/invite/" + invite + "/accept")
    }

    async declineInvite(invite: number) {
        return await this.post("player/invite/" + invite + "/decline")
    }

    async isTeamNameAvailable(name: string) {
        return (await this.get("roster/name/" + name + "/status")).available
    }

    async createTeam({name, short_name, location}: {name: string, short_name: string, location?: string}) {
        return await this.post("roster/create", {name, short_name, location});
    }

    async findPlayer(query: string) {
        const response = await this.get("player/find/" + query)
        const playerId = response.player_id;
        if (!playerId) {
            return null;
        }
        return new Player(playerId);
    }

    async joinQueue(queue: PlayerQueue) {
        const response = await this.post("queue/join", {queue: queue.objectID});
        return response == true;
    }

    async leaveQueue(queue: PlayerQueue) {
        const response = await this.post("queue/leave", {queue: queue.objectID});
        return response == true;
    }

    async confirmRankedMatch(queue: PlayerQueue) {
        const response = await this.post("queue/confirm", {queue: queue.objectID});
        return response == true;
    }

    async pickPlayer(queue: PlayerQueue, player: Player) {
        return await this.post("queue/pick", {player: player.objectID, queue: queue.objectID});
    }

    async joinGame(game: Game) {
        return await this.post("game/join", {game: game.objectID});
    }

}

const API = new MsApi();

window.$api = API;
export default API;