<template>
  <v-row class="flex-nowrap">
    <v-col cols="auto" class="d-flex align-center" :class="{ 'pa-0': dense }">
      <div class="position-relative">
        <div style="top:-10px; right:-7px; z-index: 10;" class="position-absolute" v-if="player.in_server" color="green">
          <v-icon size="15px" color="green">
            mdi-circle
          </v-icon>
        </div>
        <v-icon size="large" v-if="crown" class="position-absolute" style="width: 100%; z-index: 10;left:0; right: 0; margin: 0 auto 0 auto; top: 0px; color: #da8d25; transform: translateY(-60%)">mdi-crown</v-icon>
        <player-avatar
            @click="$router.push({ name: 'player', params: { id: player.id } })"
            v-bind="{ ...$attrs, ...$props }"
            :player="player"
        ></player-avatar>
      </div>

    </v-col>
    <v-col style="width: 1px">
      <div class="d-flex align-center" style="height: 100%">
        <router-link
          class="w-100 text-truncate"
          v-if="player?.id"
          :to="{ name: 'player', params: { id: player.id } }"
        >
          {{ player.username }}
        </router-link>

      </div>
    </v-col>
  </v-row>
</template>

<script>
import playerAvatar from "../atom/player-avatar.vue";
export default {
  components: { playerAvatar },
  props: { player: null, dense: Boolean, crown:  Boolean },

  data() {
    return {};
  },
  created() {},
};
</script>

<style>
</style>