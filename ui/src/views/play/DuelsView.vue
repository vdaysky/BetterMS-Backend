<template>
  <v-container>
    <play-nav-view title="Duels" :level="3">
      <game-list :games="duels.games" variant="cards" />
    </play-nav-view>
  </v-container>
</template>

<script>
import { DuelsView } from "@/api/model/models";
import GameList from "@/components/lists/GameList.vue";
import PlayNavView from "@/views/PlayNavView.vue";
export default {
  components: {PlayNavView, GameList },
  data() {
    return {
      duels: DuelsView.createView([
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