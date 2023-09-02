<template>
  <v-container>
    <v-card density="compact">
      <v-card-title class="justify-center">
        <span>{{ title }}</span>
      </v-card-title>
      <v-card-text dclass="pt-0 px-0">
        <player-list
            class="px-0"
          :players="players"
          :captain="captain"
          :exclude="['index', 'team', 'elo', 'games_played', 'winrate']"
        >
        </player-list>

      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import PlayerList from "@/components/lists/PlayerList.vue";
import { MatchTeam } from '@/api/model/models';
export default {
    components: { PlayerList },
    props: {'team': null, 'captain': null},
    computed: {
      isMatchTeam() {
        return this.team instanceof MatchTeam;
      },
      title() {
        if (this.isMatchTeam) {
          return this.team._name;
        }
        return this.team.short_name + " | " + this.team.elo + " Elo"; 
      },
      players() {
        if (this.isMatchTeam) {
          return this.team.players;
        }
        return this.team.members;
      },
    },
    created() {
      console.log("TeamSubView created");
    }

}
</script>

<style>

</style>