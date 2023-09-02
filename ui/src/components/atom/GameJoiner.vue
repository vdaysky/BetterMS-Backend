<template>
  <div v-if="game.status === GameStatus.Terminated || game.status ===  GameStatus.Finished">
    <v-chip color="red"> Game Ended</v-chip>
  </div>
  <div v-else>
    <v-btn
        v-bind="props"
        v-if="player?.in_server"
        :color="(isFull || inGame || joinAttemptFailed) ? 'red' : 'green'"
        variant="outlined"
        :disabled="isFull || inGame || joinAttemptFailed"
        @click="join()"
    >
      {{ !isFull ? (inGame ? "In Game" : (joinAttemptFailed ? "Can't Join": "Join")) : "Game Full!" }}
    </v-btn>
    <div v-else>
      <v-chip color="red" v-if="isFull">Game is Full!</v-chip>
      <v-chip color="red" v-else-if="inGame">Already In Game</v-chip>
      <copy-text v-else :value="`/join ${game.id}`"></copy-text>
    </div>
  </div>
</template>

<script>
import CopyText from "./CopyText.vue";
import {Game, GameStatus} from "@/api/model/models";
export default {
  components: { CopyText },
  data() {
    return {
      joinAttemptFailed: false,
      errorMessage: "",
    };
  },
  props: {
    game: Game,
  },
  computed: {
    GameStatus() {
      return GameStatus
    },
    player() {
      return this.$store.state.player;
    },
    isFull() {
      return this.game.isFull();
    },
    inGame() {
      return this.player?.active_game?.id === this.game?.id;
    },
  },
  methods: {
    async join() {
      const {success, message} = await this.$api.joinGame(this.game);
      if (!success) {
        this.joinAttemptFailed = true;
        console.log(message)
        this.errorMessage = message;
      }
    },
  },
};
</script>

<style>
</style>