<template>
  <v-container>
    <play-nav-view title="Deathmatch" :level="3">
      <game-list v-if="deathmatch.games" :games="deathmatch.games" variant="cards">
      </game-list>
    </play-nav-view>
  </v-container>
</template>

<script>
import { DeathMatchView } from '@/api/model/models'
import GameList from '@/components/lists/GameList.vue'
import PlayNavView from "@/views/PlayNavView.vue";
export default {
  components: {PlayNavView, GameList },
  data() {
    return {
      deathmatch: DeathMatchView.createView([{
        entity: 'Game',
        obj_id: null,
        dependencies: []
      }])
    }
  },
}
</script>

<style>

</style>