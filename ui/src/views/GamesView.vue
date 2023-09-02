<template>
<v-container>
  <v-container>
    <v-row>
      <v-col class="px-0">
        <h1>Recent Games</h1>
        <code>
          {{ gamesView?.games?.count }} games found
        </code>
      </v-col>
    </v-row>
  </v-container>
  <game-list :games="gamesView.games"></game-list>
</v-container>
</template>

<script>

import {GamesView} from "@/api/model/models";
import GameList from "@/components/lists/GameList.vue";

export default {
  components: {GameList},

  data: function() {
    return {
      gamesView: GamesView.createView([{
        entity: 'Game',
        obj_id: null,
      }]),
    }
  },
}
</script>


<style scoped>

</style>