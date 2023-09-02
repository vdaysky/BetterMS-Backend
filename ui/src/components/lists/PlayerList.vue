<template>
  <contextual-list
    v-bind="{...$attrs}"
    :source="players"
    :exclude="exclude"
    :density="density"
    :headers="[
      { label: '#', name: 'index' },
      { label: 'Player', name: 'player' },
      { label: 'Elo', name: 'elo', orderable: true },
      { label: 'Games Played', name: 'games_played', orderable: true, defaultOrdering: 1 },
      { label: 'Winrate', name: 'winrate', orderable: true },
    ]"
  >
    <template v-slot:row="{ i, row, headers }">
      <td v-if="headers.index" width="8%">{{ i + 1 }}.</td>
      <td class="position-relative">

        <player-widget :crown="row?.id && row?.id == captain?.id" :player="row"></player-widget>
      </td>
      <td v-if="headers.elo">
        {{ row.elo }}
      </td>

      <td v-if="headers.games_played">
        {{ row.games_played }}
      </td>

      <td v-if="headers.winrate">
        {{ row.winrate / 100 }}%
      </td>
<!--      <td v-if="headers.team">-->
<!--        <team-widget v-if="row.team" :team="row.team"></team-widget>-->
<!--      </td>-->
    </template>
  </contextual-list>
</template>

<script>
import ContextualList from "../contextual/ContextualList.vue";
import PlayerWidget from "../widgets/PlayerWidget.vue";
import {Player} from "@/api/model/models";
export default {
  components: { PlayerWidget, ContextualList },
  props: {
    exclude: Array,
    players: Object,
    hideTeam: Boolean,
    dense: Boolean,
    captain: Player,
    density: String,
  },
};
</script>

<style>
</style>