<template>
  <div>
    <player-profile :key="player_id"  :player="player" :own="false"></player-profile>
  </div>
</template>

<script>
import PlayerProfile from "@/components/common/PlayerProfile.vue";
import {Player} from "@/api/model/models";

export default {
  components: { PlayerProfile },
  data: function() {
    return {
      player: null,
    }
  },
  created() {
    const playerId = this.$route.params.id;
    this.player = Player.Find(playerId);
  },
  watch: {
    player_id: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.player = Player.Find(newVal);
        }
      },
    }
  },
  computed: {
    player_id() {
      return this.$route.params.id
    }
  },
};
</script>

<style>
</style>