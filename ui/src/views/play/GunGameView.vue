<template>
  <v-container>
    <play-nav-view title="GunGame" :level="3">
      <game-list :games="gungame.games" variant="cards" />
    </play-nav-view>
  </v-container>
</template>

<script>
import { GunGameView } from "@/api/model/models";
import GameList from "@/components/lists/GameList.vue";
import PlayNavView from "@/views/PlayNavView.vue";
export default {
  components: {PlayNavView, GameList },
  data() {
    return {
      gungame: GunGameView.createView([
        {
          entity: "Game",
          obj_id: null,
          dependencies: [],
        },
      ])
    }
  },
};
</script>

<style>
</style>