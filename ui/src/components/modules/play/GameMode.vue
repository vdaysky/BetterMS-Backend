<template>
  <v-card min-width="200px" max-width="400px" class="d-flex flex-column">
    <v-card-title>
      {{ name }}
    </v-card-title>
    <v-divider class="mb-2"></v-divider>
    <v-card-subtitle>
      <div class="d-flex justify-space-between flex-wrap">
        <p>
          <b>{{ online }}</b> Players Online
        </p>
        <p class="hidden-md-and-down hidden-xl">
          &bull;
        </p>
        <p>
          <b>{{ lobbies }}</b> Active Lobbies
        </p>
      </div>
    </v-card-subtitle>
    
    <v-card-text height="100px">
      {{ description }}
    </v-card-text>
    <v-spacer></v-spacer>
    <v-card-actions>
      <v-btn :disabled="disabled" block variant="outlined" color="primary" @click="$emit('selected')">Play!</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  props: ["name", "description", "online", "lobbies", "disabled"],
};
</script>

<style>
</style>