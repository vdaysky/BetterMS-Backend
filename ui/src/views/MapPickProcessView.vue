<template>
  <v-container class="px-0">
    <v-card>
      <v-card-title class="flex-column text-center">
        <span class="headline"> MAP PICKS - {{ status }}</span>
      </v-card-title>

      <v-divider></v-divider>
        <v-container>
          <v-row class="map" v-for="mapPick in [...mapPickProcess.maps].sort((x, y) => x.id - y.id)" :key="mapPick">
            <v-col cols="12"
                   :style="`background-image: url('/${mapPick?.map?._name}.png'); background-position: center; background-size: cover`"
                   :class="{
                    'bg-banned': mapPick.isBanned(),
                    'bg-picked': mapPick.isPicked(),
                  }"
                   class="py-4"
            >
              <div class="d-flex justify-space-between">
                <p
                  :class="{
                    banned: mapPick.isBanned(),
                    picked: mapPick.isPicked(),
                  }"
                  class="text-no-wrap text-uppercase font-weight-bold"
                  style="font-size: larger"
                >
                  {{ mapPick.map?.display_name }}
                </p>
                <div v-if="mapPick && !mapPick.isSelected() && !isEnded">
                  <v-btn
                      @click="selectMap(mapPick)"
                      class="ms-4 text-primary"
                      v-if="!isEnded"
                      :disabled="mapPick.selected_by || !canSelect"
                  >
                    {{ isPick ? "Pick" : "Ban" }}
                  </v-btn>
                </div>
                <div v-else>
                  <p class="ms-2 font-weight-light" style="font-size: smaller; color: white;" v-if="mapPick.isSelected()">
                    ({{ mapPick.selected_by._name }})
                  </p>
                  <p class="ms-2 font-weight-light" v-else style="font-size: smaller; color: white;">
                    (DEFAULT)
                  </p>
                </div>
              </div>
            </v-col>
          </v-row>
        </v-container>
    </v-card>
  </v-container>
</template>

<script>
export default {
  props: ["mapPickProcess", "disabled"],

  computed: {
    player() {
      return this.$store.state.player;
    },
    isParticipating() {
      if (!this.mapPickProcess?.match) return false;
      return this.player.id === this.mapPickProcess.picker_a.id || this.player.id === this.mapPickProcess.picker_b.id;
    },
    canSelect() {
      return this?.player && this.player?.id == this?.mapPickProcess?.turn?.id;
    },
    isPick() {
      return this.mapPickProcess.next_action == 2;
    },
    isBan() {
      return this.mapPickProcess.next_action == 1;
    },
    isEnded() {
      return this.mapPickProcess.finished;
    },
    status() {
      if (this.disabled) {
        return "Map Pick is disabled";
      }

      if (this.isEnded) return "Ended";
      if (this.isParticipating && !this.canSelect)
        return "Opponent's Turn";
      if (this.isParticipating && this.canSelect) return "Your Turn";
      return "In Progress";
    },
  },
  methods: {
    async selectMap(map) {
      await this.$api.mapPickAction(map);
    },
  },
};
</script>

<style scoped>
.map {
  border: 1px solid #d9d9d9;
  color: white;
  text-shadow: #000000 1px 1px 2px;
}
.banned {
  color: #bbbbbb;
  text-decoration: line-through;
  text-shadow: #000000 1px 1px 2px;
}
.picked {
  color: #06de06;
  text-shadow: #000000 1px 1px 2px;
}

.bg-banned {
  position: relative;
}
.bg-banned:before {
  position: absolute;
  background-size: cover;
  content: '';
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: #5d5d5d;
  opacity: 50%;
  z-index: 10;
}

</style>