<template>
  <v-container>
    <v-table>
        <thead>
            <tr>
                <th>
                    #
                </th>
                <th>
                    Player
                </th>
                <th>
                    Kills
                </th>
                <th>
                    Deaths
                </th>
                <th>
                    Assists
                </th>

                <th>
                    K/D
                </th>

                <th>
                    HS%
                </th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(stat, i) in statsView?.stats" :key="stat">
                <td width="8%">
                    {{ i + 1 }}.
                </td>
                <td>
                    <player-widget v-if="stat.player" :player="stat.player"></player-widget>
                </td>
                <td>
                    {{ stat.kills }}
                </td>
                <td>
                    {{ stat.deaths }}
                </td>
                <td>
                    {{ stat.assists }}
                </td>
                <td>
                    {{ stat.kd() }}
                </td>
                <td>
                    {{ Math.round(stat.hs * 10000 / (stat.kills || 1)) / 100 }}%
                </td>
            </tr>
            <tr v-if="!statsView?.stats?.length">
                <td colspan="7" class="text-center">
                    No stats found
                </td>
            </tr>
        </tbody>
    </v-table>
  </v-container>
</template>

<script>
import PlayerWidget from '../widgets/PlayerWidget.vue'
import {GameStatsView} from "@/api/model/models";
export default {
  components: { PlayerWidget },
    props: ['team'],
    data() {
        return {
            statsView: null,
        }
    },
  watch: {
        team: {
          handler(newVal) {
            if (!newVal?.id) return;

            this.statsView = GameStatsView.Find(null, {
              dependencies: [
                {
                  entity: 'InGameTeam',
                  obj_id: newVal.id,
                  dependencies: []
                }
              ]
            });
          },
          immediate: true,
          deep: true
        }
    }
}
</script>

<style>

</style>