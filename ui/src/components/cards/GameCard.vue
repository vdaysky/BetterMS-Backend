<template>
  <v-card style="min-width: 220px; max-width: 350px; width: 100%">
    <v-card-title>
        {{ game?.map?.display_name }} #{{ game?.id}}
    </v-card-title>
    <v-card-text>
        {{ game.playerCount() }} {{ game.playerCount() == 1 ? "player" : "players" }}
    </v-card-text>
    <v-card-actions class="d-flex justify-space-between">
        <game-joiner :game="game"></game-joiner>
        <v-btn variant="outlined" color="primary" :to="{name: 'game', params: {id: game.id} }" >More</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import GameJoiner from '../atom/GameJoiner.vue';
import {Game} from "@/api/model/models";
export default {
  components: { GameJoiner },
    props: {
        game: Game,
        joinable: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        player() {
            return this.$store.state.player;
        }
    },
}
</script>

<style>

</style>