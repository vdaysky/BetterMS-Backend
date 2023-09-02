<template>
  <v-container>
    <div class="py-5" :style="`background-image: url('/${game.map?._name}.png'),  url(/fallback.png)`" style="background-size: cover; background-position: center">
      <h1 class="text-center text-white">{{ game?.map?.display_name }} - {{ game.mode() }} -
        {{ game?.status === GameStatus.Finished ? "Finished" : "" }}
        {{ game?.status === GameStatus.Terminated ? "Terminated" : "" }}
        {{ game?.status === GameStatus.NotStarted ? "Not Started" : "" }}
        {{ game?.status === GameStatus.Started ? "Started" : "" }}
      </h1>
      <h3 class="text-center text-white">
        {{ game.started_at && formatDate(game.started_at) }}
      </h3>
    </div>

    <div v-if="game.match" class="mt-2 text-center text-white">
      <match-widget :match="game.match"></match-widget>
    </div>

    <v-container class="pb-0">
      <h2 >
        <span :style="{color: sideColor(game?.team_a?.is_ct)}">
          {{ game.team_a?.name || sideName(game?.team_a?.is_ct) }}
        </span>
         - {{ game.score_a }}

        {{ game.winner == game.team_a ? " - Winner" : "" }}

      </h2>
    </v-container>
    <team-score :key="teamA?.id" :team="teamA"></team-score>

    <v-container class="pb-0">
      <h2>
        <span :style="{color: sideColor(game?.team_b?.is_ct)}">
          {{ game.team_b?.name || sideName(game?.team_b?.is_ct) }}
        </span>

         - {{ game.score_b }}
        {{ game.winner == game.team_b ? " - Winner" : "" }}
      </h2>
    </v-container>
    <team-score :key="teamB?.id" :team="teamB"></team-score>
  </v-container>
</template>

<script>
import TeamScore from '@/components/subview/TeamScore.vue'
import MatchWidget from '@/components/widgets/MatchWidget.vue'
import {Game, GameStatus} from "@/api/model/models";
import {formatDate} from "@/api/utils";
export default {
  components: { TeamScore, MatchWidget },
  data() {
    return {
      game: Game.Find(this.$route.params.id),
    }
  },
  computed: {
    GameStatus() {
      return GameStatus
    },
    teamA() {
      return this.game.team_a;
    },
    teamB() {
      return this.game.team_b;
    }
  },
  watch: {
    teamA(newVal, oldVal) {
      console.log("team A changed", newVal, oldVal)
    }
  },
  methods: {
    formatDate,
    sideName(isCT) {
      return isCT ? this.game?.team_a?._name || 'SWAT' : this.game?.team_b?._name || 'Bombers'
    },
    sideColor(isCT) {
      return isCT ? '#1e99e7' : '#ff4b4b'
    }
  }

}
</script>

<style>

</style>