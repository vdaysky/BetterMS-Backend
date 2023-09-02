<template>
  <v-container>
    <v-row class="d-flex flex-row">
      
      <!-- Player Stats -->
      <v-col md="8" lg="8" sm="12" cols="12">
        <v-card style="height:100%;">
          <v-card-title :style="{background: $vuetify.theme.themes.light.colors.background}">
            Stats
          </v-card-title>
          <v-card-text>
            
            <div class="d-flex justify-center pt-5">
              <stat-badge class="mx-1">
                <template v-slot:metric>
                  Ranked Elo
                </template>
                <template v-slot:value>
                  {{ player.elo }}
                </template>
              </stat-badge>

              <stat-badge class="mx-1">
                <template v-slot:metric>
                  Total Games Played
                </template>
                <template v-slot:value>
                  {{ stat?.games_played }}
                </template>
              </stat-badge>

              <stat-badge class="mx-1">
                <template v-slot:metric>
                  Total Wins
                </template>
                <template v-slot:value>
                  {{ stat?.games_won }}
                </template>
              </stat-badge>

              <stat-badge class="mx-1">
                <template v-slot:metric>
                  Ranked Games
                </template>
                <template v-slot:value>
                  {{ stat?.ranked_games_played }}
                </template>
              </stat-badge>

              <stat-badge class="mx-1">
                <template v-slot:metric>
                  Ranked Wins
                </template>
                <template v-slot:value>
                  {{ stat?.ranked_games_won }}
                </template>
              </stat-badge>
            </div>
            
            <v-table>
              <thead>
                <tr>
                  <th class="text-center">Kills</th>
                  <th class="text-center">Deaths</th>
                  <th class="text-center">Assists</th>
                  <th class="text-center">K/D</th>
                  <th class="text-center">HS%</th>
                </tr>
              </thead>
              <tbody>
                <tr class="text-center">
                  <td>{{ stat?.kills }}</td>
                  <td>{{ stat?.deaths }}</td>
                  <td>{{ stat?.assists }}</td>
                  <td>{{ stat?.kd?.() }}</td>
                  <td> {{ Math.round(stat?.hs * 10000 / (stat?.kills || 1)) / 100 }}%</td>
                </tr>
              </tbody>
            </v-table>

            <p>Recent games ({{stat?.recent_games?.count || 0}})</p>

            <v-container>
              <game-list v-if="stat?.recent_games" :games="stat?.recent_games" ></game-list>
          </v-container>

          </v-card-text>
        </v-card>
      </v-col>

      <!-- Player Card -->
      <v-col md="4" lg="4" sm="12" cols="12">
        <v-card style="height:100%;">
          <v-card-title class="justify-center" :style="{background: $vuetify.theme.themes.light.colors.background}" >
            <span>{{ player.username }}</span>
          </v-card-title>
          <div class="d-flex justify-center mb-4 py-3" style="background: #e7e7e7; box-shadow: #e7e7e7 0px 0px 7px 2px;">
            <img v-if="player.uuid" :src="`https://crafatar.com/renders/body/${player.uuid}`">
          </div>

          <v-card-text v-if="player.owned_team">
            <span> Team Owner </span>
            <team-widget :team="player.owned_team"></team-widget>

            <div v-if="player.owned_team" class="text-center">
              <invite-player-modal
                  v-if="own"
                  class="my-4"
                  :style="{
                  color: $vuetify.theme.themes.light.colors['on-primary'],
                  background: $vuetify.theme.themes.light.colors.primary
                }"
                  block
                  @selected="e => sendInvite(e.player)"
              >
                Invite Players
              </invite-player-modal>

              <v-divider class="my-4"></v-divider>

            </div>

            <div class="d-flex" v-if="player.isInTeam()">
              <h3 class="me-3">Member of</h3>
              <team-widget :team="player.team"></team-widget>
            </div>
          </v-card-text>

          <v-card-text v-if="own">
            <v-btn @click="logOut" block color="error">Log Out</v-btn>
          </v-card-text>

          <v-card-text>
            <p  :key="lastSeenKey">Last seen on server:
            <b>{{ player.in_server ? "Online" : formatDateAsDelta(player.last_seen) }}</b>
            </p>
          </v-card-text>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import InvitePlayerModal from '@/components/modal/InvitePlayerModal.vue'
import TeamWidget from '@/components/widgets/TeamWidget.vue'
import {PlayerPerformanceAggregatedView} from '@/api/model/models'
import StatBadge from '../atom/StatBadge.vue'
import GameWidget from "@/components/widgets/GameWidget.vue";
import API from "@/api/api";
import {formatDate, formatDateAsDelta} from "@/api/utils";
import GameList from "@/components/lists/GameList.vue";
export default {
   components: {GameList, InvitePlayerModal, TeamWidget, StatBadge },

    props: ['player', 'own'],

    data () {
        return {
          stat: null,
          lastSeenKey: 0,
          lastSeenInterval: null
        }
    },

    watch: {
      player_id: {
        immediate: true,
        handler(newVal) {
        
          if (newVal) {
            this.stat = PlayerPerformanceAggregatedView.createView(
                [{
                  entity: 'Player',
                  obj_id: newVal,
                  modifiers: '[]',
                  dependencies: [],
                }]
            );
          }
        },
      }
    },

    computed: {
      GameWidget() {
        return GameWidget
      },
      ownedTeam() {
        return this.player?.owned_team
      },
      player_id() {
        return this.player?.id
      }
    },
    mounted() {
     this.lastSeenInterval = setInterval(() => {
       this.lastSeenKey++
     }, 1000);
    },
  unmounted() {
    clearInterval(this.lastSeenInterval)
  },
  methods: {
    formatDate,
      formatDateAsDelta,
      async logOut() {
        await API.logout();
        this.$store.commit('setPlayer', null)
        this.$router.push({name: 'home'})
      }
    }
}
</script>

<style>

</style>