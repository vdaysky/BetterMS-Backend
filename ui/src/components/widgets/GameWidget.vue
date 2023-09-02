<template>
  <div class="d-flex">
    <router-link class="mr-3 pt-1" :to="{name: 'game', params: {'id': game.id} }"> #{{game.id}} {{ game?.map?.display_name }} {{ score }} </router-link>
    <game-joiner v-if="joinable" :game="game"></game-joiner>
  </div>

</template>

<script>
import {Game} from "@/api/model/models";
import GameJoiner from "@/components/atom/GameJoiner.vue";

export default {
  components: {GameJoiner},
    props: {
      'game': Game,
      'no-score': Boolean,
      'joinable': Boolean,
    },
    computed: {
        score() {
            if (!this.noScore && this.game.score_a !== undefined) {
                return "(" + this.game.score_a + ' - ' + this.game.score_b + ")"
            }
            return ""
        }
    }
}
</script>

<style>

</style>