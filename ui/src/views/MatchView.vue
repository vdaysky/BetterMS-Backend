<template>
  <v-container>
    <v-row>
      <v-col>
        <h1 class="text-center">
          {{ match.name }}
        </h1>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="px-0 pt-16" v-if="!mdAndDown" lg="4">
        <team-sub-view hideTeam v-if="match?.team_one" :captain="match?.map_pick_process?.picker_a" :team="match.team_one"></team-sub-view>
      </v-col>
      <v-col lg="4" class="px-0">
        <div class="d-flex justify-center align-center w-100">
          <div class="d-flex flex-1-1" style="max-width: 500px;">
            <map-pick-process-view v-if="match?.map_pick_process" :mapPickProcess="match.map_pick_process"></map-pick-process-view>
          </div>
        </div>
      </v-col>
      <v-col class="px-0 pt-16" v-if="!mdAndDown" lg="4">
        <team-sub-view hideTeam v-if="match?.team_two" :captain="match?.map_pick_process?.picker_b"  :team="match.team_two"></team-sub-view>
      </v-col>
    </v-row>
    
    <v-row class="justify-center">
      <v-col cols="12" xl="6">
        <h3 class="text-center">Games</h3>

        <game-list :joinable="ICanJoin" :games="match.games"></game-list>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { Match } from '@/api/model/models'
import MapPickProcessView from './MapPickProcessView.vue'
import TeamSubView from '@/components/subview/TeamSubView.vue'
import GameList from '@/components/lists/GameList.vue'
import { useDisplay } from 'vuetify/lib/framework.mjs'

export default {
  components: { MapPickProcessView, TeamSubView, GameList },
  setup() {
    const { xs, smAndUp, smAndDown, mdAndDown } = useDisplay();
    return {
      GameList, xs, smAndUp, smAndDown, mdAndDown
    }
  },
  computed: {
    ICanJoin() {
      const player = this.$store.state.player;
      if (player && this.match.team_one) {
        return this.match.team_one.players.some(p => p.id == player.id) || this.match.team_two.players.some(p => p.id == player.id);
      }
      return false;
    }
  },

  data: function(){
      return { 
        match: Match.Find(this.$route.params.id, {dependencies: [
            {
              entity: 'Game',
              obj_id: null
            }
          ]}),
      }
  },
}
</script>

<style>

</style>