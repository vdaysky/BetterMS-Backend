<template>
  <v-container class="">
    <play-nav-view title="Play" :level="2">
      <v-row>
        <v-col lg="3" md="6">
          <game-mode min-height="100%"
                     name="Pub"
                     description="Rekt n00bz in classic defusal MineStrike without risking your rating."
                     :online="stats.pubs_online"
                     :lobbies="stats.pubs_games"
                     @selected="$router.push({ name: 'pubs' })"
          ></game-mode>
        </v-col>
        <v-col lg="3" md="6">
          <game-mode min-height="100%"
                     name="Ranked"
                     description="Defusal Mode with a rating system."
                     :online="stats.ranked_online"
                     :lobbies="stats.ranked_games"
                     @selected="$router.push({ name: 'ranked' })"
          ></game-mode>
        </v-col>
        <v-col lg="3" md="6">
          <game-mode min-height="100%"
                     name="Deathmatch"
                     description="Deathmatch mode. Instant respwans, free weapons. Get as many kills as you can."
                     :online="stats.deathmatch_online"
                     :lobbies="stats.deathmatch_games"
                     @selected="$router.push({ name: 'deathmatch' })"
          ></game-mode>
        </v-col>
        <v-col lg="3" md="6">
          <game-mode min-height="100%"
                     name="Duels"
                     description="1v1 duels. No rating system."
                     :online="stats.duels_online"
                     :lobbies="stats.duels_games"
                     @selected="$router.push({ name: 'duels' })"
          ></game-mode>
        </v-col>
        <v-col lg="3" md="6">
          <game-mode min-height="100%"
                     name="Gun Game"
                     description="19 Levels, get a kill with each weapon to advance to the next level. First to get to the last level wins."
                     :online="stats.gungame_online"
                     :lobbies="stats.gungame_games"
                     @selected="$router.push({ name: 'gungame' })"
          ></game-mode>
        </v-col>
      </v-row>
    </play-nav-view>
  </v-container>
</template>

<script>
import GameMode from "@/components/modules/play/GameMode.vue";
import { GameModeStatsView } from "@/api/model/models";
import PlayNavView from "@/views/PlayNavView.vue";
export default {
  components: {PlayNavView, GameMode },
  data() {
    return {
      stats: null
    };
  },
  created() {
    this.stats = GameModeStatsView.createView([]);
  }
};
</script>

<style>
</style>