<template>
  <v-container>
    <play-nav-view title="Pubs" :level="3" >
      <game-list variant='cards' :games="pubs.games">

      </game-list>
    </play-nav-view>
  </v-container>
</template>

<script>
import { PubsView } from '@/api/model/models'
import GameList from '@/components/lists/GameList.vue'
import PlayNavView from "@/views/PlayNavView.vue";
export default {

    setup() {
        return {
            GameList
        }
    },

    components: {PlayNavView, GameList },
    data() { 
        return {
            pubs: null,
        }
    },

    created() {
        this.pubs = PubsView.createView([]);
    }
}
</script>

<style>

</style>