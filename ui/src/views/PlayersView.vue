<template>
  <v-container>
    <v-row>
      <v-col>
        <h1>Players</h1>
        <code> {{ playerView?.players?.count }} players found </code>
      </v-col>
    </v-row>

    <v-row v-if="playerView?.players">
      <v-col>
        <player-list :players="playerView?.players" interactive paginated>
        </player-list>
        
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import {PlayersView} from "@/api/model/models";
import PlayerList from '@/components/lists/PlayerList.vue';
export default {
  components: { PlayerList },
  setup() {
    return {
      PlayerList,
    };
  },
  data() {
    return {
      playerView: PlayersView.createView([
        {
          entity: 'Player',
          obj_id: null,
          dependencies: []
        }
      ]),
    };
  },
};
</script>

<style>
</style>