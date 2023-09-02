<template>
    <v-dialog persistent v-model="show_" max-width="500px">
        <v-card>
        <v-card-title class="headline">Confirm</v-card-title>
        <v-card-text>
            <p>Queue is full, confirm to start the game</p>

            <p></p>
          <v-container>
            <div class="d-flex">
              <div class="mx-1" :style="isConfirmed(player) ? 'border: 4px solid green': 'border: 4px solid gray'" v-for="player in players" :key="player.id">
                <v-tooltip>
                  <template v-slot:activator="{ props }">
                    <player-avatar :player="player" v-bind="props"></player-avatar>
                  </template>
                  <span>{{ player.username }}</span>
                </v-tooltip>
              </div>
            </div>
          </v-container>
          <p class="text-center">{{ confirmedPlayers.length }} / {{ players.length }} Confirmations ({{ secondsLeft }}s)</p>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn v-if="!confirmedByMe" color="blue darken-1" text @click="confirm">Confirm</v-btn>
            <p v-else>
                Confirmed
            </p>
        </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
import PlayerAvatar from "@/components/atom/player-avatar.vue";

export default {
  components: {PlayerAvatar},
    props: ['isOpen', 'confirmedPlayers', 'players', 'confirmedByMe'],
    data() {
        return {
            show_: this.isOpen,
            timerId: null,
            secondsLeft: 60,
        }
    },
  watch: {
    isOpen(val) {
      this.show_ = val;
    },

    show_: {
      handler(val) {
        if (val) {
          this.secondsLeft = 60;
          const this_ = this;
          this.timerId = setInterval(() => {
            if (this_.secondsLeft > 0) {
              this_.secondsLeft--;
            }
          }, 1000);
        } else {
          if (this.timerId) {
            clearInterval(this.timerId);
          }
        }
      },
      immediate: true,
    }
  },
  methods: {
    isConfirmed(player) {
      return this.confirmedPlayers?.some(p => p.id === player.id);
    },
    confirm() {
        this.$emit("confirmed");
    },
  },
};
</script>

<style>

</style>