<template>
  <v-container>
    <confirm-modal
      :is-open="modalOpen"
      :confirmedPlayers="rankedQueue?.confirmed_players"
      :players="rankedQueue?.players"
      :confirmedByMe="rankedQueue?.confirmed_by_me"
      @confirmed="confirm"
    ></confirm-modal>

    <v-row>
      <v-col>
        <v-container>
          <div class="d-flex justify-space-between">
            <h1>Ranked Queue #{{ rankedQueue.id }} </h1>

            <div class="d-flex align-center">
              <div v-if="player.isAuthenticated()">
                <v-btn
                  v-if="!alreadyJoined"
                  :disabled="rankedQueue.locked"
                  @click="joinQueue"
                  color="green"
                  >Join</v-btn
                >
                <v-btn
                  v-if="alreadyJoined"
                  :disabled="rankedQueue.locked"
                  @click="leaveQueue"
                  color="red"
                  >Leave</v-btn
                >
              </div>
              <div v-else>
                <h3>Log In to Join</h3>
              </div>
            </div>
          </div>
          <p>{{ rankedQueue.players?.length }} / {{ rankedQueue?.size }} Players</p>
        </v-container>
      </v-col>
    </v-row>
    <v-row v-if="stage != 'mapPick' && stage != 'done'">
      <v-col>
        <v-container>
          <v-row>
            <v-col cols="12">
              <v-table>
                <thead>
                  <tr>
                    <th width="8%">#</th>
                    <th>Player</th>
                    <th>Elo</th>
                    <th v-if="isCaptain">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(player, i) in teamlessPlayers" :key="player.id">
                    <td>{{ i + 1 }}.</td>
                    <td>
                      <player-widget :player="player"></player-widget>
                    </td>
                    <td>
                      {{ player.elo }}
                    </td>
                    <td v-if="isCaptain">
                      <v-btn
                        :disabled="!canPickPlayer"
                        @click="pickPlayer(player)"
                        >Pick</v-btn
                      >
                    </td>
                  </tr>
                <tr v-if="teamlessPlayers.length === 0">
                  <td colspan="3" class="text-center">This queue is empty. Be first one to join!</td>
                </tr>
                </tbody>
              </v-table>
            </v-col>
          </v-row>
        </v-container>
      </v-col>
    </v-row>
    <v-row v-if="rankedQueue.match">
      <v-col class="text-center">
        <v-container>
          <match-widget :match="rankedQueue.match"></match-widget>
        </v-container>
      </v-col>
    </v-row>
    <v-row v-if="rankedQueue.confirmed === true">
      <v-col class="mr-2">
        <player-list
          v-if="rankedQueue?.match?.team_one?.players"
          :players="rankedQueue.match.team_one.players"
          :captain="rankedQueue.captain_a"
        ></player-list>
      </v-col>

      <v-col class="ml-2">
        <player-list
          v-if="rankedQueue?.match?.team_two?.players"
          :players="rankedQueue.match.team_two.players"
          :captain="rankedQueue.captain_b"
        ></player-list>
      </v-col>
    </v-row>
    <v-row v-if="rankedQueue?.match?.games?.length">
      <v-col>
        <v-row>
          <v-col>
            <h2 class="text-center">Games</h2>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <game-list joinable :games="rankedQueue?.match?.games"></game-list>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { PlayerQueue } from "@/api/model/models";
import PlayerList from "@/components/lists/PlayerList.vue";
import ConfirmModal from "./ConfirmModal.vue";
import PlayerWidget from "@/components/widgets/PlayerWidget.vue";
import MatchWidget from "@/components/widgets/MatchWidget.vue";
import GameList from "@/components/lists/GameList.vue";
import {playMatchFound} from "@/api/utils";
export default {
  components: {
    PlayerList,
    ConfirmModal,
    PlayerWidget,
    MatchWidget,
    GameList,
  },
  data() {
    return {
      rankedQueue: null,
      modalOpen: false,
    };
  },
  computed: {
    queueId() {
      return this.$route.params.id;
    },
    teamlessPlayers() {
      if (!this.rankedQueue?.players) return [];
      return this.rankedQueue?.players.filter(
        (p1) =>
          !this.rankedQueue.match ||
          (!this.teamOnePlayers.some(
            (p2) => p1.id == p2.id
          ) &&
            !this.teamTwoPlayers.some(
              (p2) => p1.id == p2.id
            ))
      );
    },
    alreadyJoined() {
      return this.isInQueue(this.$store.state.player);
    },
    player() {
      return this.$store.state.player;
    },
    isCaptainA() {
      return (
        this.player?.id && this?.rankedQueue?.captain_a?.id == this.player.id
      );
    },
    isCaptainB() {
      return (
        this.player?.id && this?.rankedQueue?.captain_b?.id == this.player.id
      );
    },

    isCaptain() {
      return this.isCaptainA || this.isCaptainB;
    },

    stage() {
      if (!this?.rankedQueue?.locked) {
        return "recruitment";
      } else if (!this.rankedQueue.confirmed) {
        return "locked";
      } else if (this.teamlessPlayers.length != 0) {
        return "teamPick";
      } else if (
        this.teamlessPlayers.length == 0 &&
        !this.rankedQueue.match.games.length
      ) {
        return "mapPick";
      } else {
        return "done";
      }
    },

    teamOnePlayers() {
      return this.rankedQueue?.match?.team_one?.players || [];
    },
    teamTwoPlayers() {
      return this.rankedQueue?.match?.team_two?.players || [];
    },

    canPickPlayer() {
      if (this.stage != "teamPick") {
        return false;
      }

      return (
        (this.isCaptainA &&
          this.teamOnePlayers.length == this.teamTwoPlayers.length) ||
        (this.isCaptainB &&
          this.teamTwoPlayers.length <
            this.teamOnePlayers.length)
      );
    },
    confirmationModalOpen() {
      return this.rankedQueue?.locked && !this.rankedQueue?.confirmed
    }
  },
  watch: {
    confirmationModalOpen(newValue) {
      if (newValue) {
        this.modalOpen = true;
        playMatchFound();
      } else {
        this.modalOpen = false;
      }
    },

    stage: {
      handler(newValue) {
        if (newValue === "mapPick") {
          this.$router.push({ name: "match", params: { id: this.rankedQueue.match.id } });
        }
      },
      immediate: true,
      deep: true,
    },
  },
  methods: {
    isInQueue(player) {
      if (!player) return false;
      if (!this.rankedQueue) return false;

      return this?.rankedQueue?.players.some((p) => p.id == player.id);
    },
    confirm() {
      this.$api.confirmRankedMatch(this.rankedQueue);
    },
    joinQueue() {
      this.$api.joinQueue(this.rankedQueue);
    },
    leaveQueue() {
      this.$api.leaveQueue(this.rankedQueue);
    },
    pickPlayer(player) {
      this.$api.pickPlayer(this.rankedQueue, player);
    },
  },
  created() {
    this.rankedQueue = PlayerQueue.Find(this.queueId, {dependencies: [
        {
          entity: 'QueuePlayers',
          obj_id: null,
        },
        {
          entity: 'ConfirmedPlayers',
          obj_id: null,
        }
      ]}).registerEventDependency('auth');
  },
};
</script>

<style>
</style>