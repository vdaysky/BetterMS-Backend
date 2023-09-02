<template>
  <v-container>
    <play-nav-view title="Ranked" :level="3">
      <v-row>
        <v-col>
          <h1>Ranked</h1>
          <code> {{ ranked.queues.length }} ranked queues found </code>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="3" v-for="queue in ranked.queues" :key="queue.id">
          <v-card class="d-flex flex-column">
            <v-card-title>
              <h4>Ranked Queue #{{ queue.id }}</h4>
            </v-card-title>

            <v-card-text>
              <code> {{ queue.players.length }} / {{ queue?.size }} Players </code>
              <div class="mt-2">
                <v-chip class="me-1" color="green" v-if="!queue.locked">
                  Open
                </v-chip>
                <v-chip class="me-1" color="red" v-else>
                  Locked
                </v-chip>
                <v-chip color="green" v-if="queue.id == ranked?.my_queue?.id">
                  You are in
                </v-chip>
              </div>
            </v-card-text>

            <v-spacer></v-spacer>
            <v-card-actions>
              <v-col>
                <v-btn variant="outlined" block color="primary" v-if="queue.id" :to="{name: 'ranked-queue', params: {id: queue?.id} }" >View Queue</v-btn>
              </v-col>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </play-nav-view>
  </v-container>
</template>

<script>
import { RankedView } from "@/api/model/models";
import PlayNavView from "@/views/PlayNavView.vue";
export default {
  components: {PlayNavView},
  data() {
    return {
      ranked: null,
    };
  },

  created() {
    this.ranked = RankedView.createView([]);
  },
};
</script>

<style>
</style>