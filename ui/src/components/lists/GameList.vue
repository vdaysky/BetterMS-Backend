<template>
  <contextual-list
  noSearch
  :variant="variant"
  :source="games"
  paginated
  :headers="[{label: 'Game'}, {label: 'Score', align: 'center'}, {label: 'Started At'}, {label: 'Mode'}]"
  :filters="[
    {name: 'map', label: 'Map', type: 'select', options: maps},
  ]"
  :interactive="interactive"
  >
  <template v-slot:card="{item}">
    <game-card v-if="item.id" :game="item" :joinable="joinable"></game-card>
  </template>
    <template v-slot:row="{row}">
      <td>
        <GameWidget no-score v-if="row.id" :joinable="joinable" :game="row"></GameWidget>
      </td>
      <td class="text-center">
        {{ row.score_a }} - {{ row.score_b }}
      </td>
      <td>
        {{ formatDate(row.started_at) }}
      </td>
      <td :key="row._mode">
        {{ row.mode() }}
      </td>
    </template>
  </contextual-list>
</template>

<script>
import GameCard from '../cards/GameCard.vue'
import ContextualList from '../contextual/ContextualList.vue'
import GameWidget from "@/components/widgets/GameWidget.vue";
import {formatDate} from "../../api/utils";
export default {
  methods: {formatDate},
  components: {GameWidget, ContextualList, GameCard },
  props: {
    'games': Object,
    'interactive': Boolean,
    'variant': String, 
    'joinable': Boolean,
  },

  data() {
    return {
      maps: [{
        title: 'Nuke',
        value: 'de_nuke',
      }, {
        title: 'Dust 2',
        value: 'de_dust2',
      }] // Map.all()
    }
  },
}
</script>

<style>

</style>