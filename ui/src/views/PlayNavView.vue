<template>

  <v-container>
    <v-row>
      <v-col style="background: linear-gradient(177deg, #cecece, #c3c3c3);">
        <v-breadcrumbs>
          <v-breadcrumbs-item class="font-weight-bold" color="blue" :to="{ name: 'home' }">Home</v-breadcrumbs-item>
          <v-breadcrumbs-divider>/</v-breadcrumbs-divider>
          <v-breadcrumbs-item class="font-weight-bold" color="blue" :disabled="level === 2" v-if="level >= 2" :to="{ name: 'play' }">Play</v-breadcrumbs-item>
          <v-breadcrumbs-divider v-if="level >= 3" >/</v-breadcrumbs-divider>
          <v-breadcrumbs-item class="font-weight-bold" color="blue" disabled="" v-if="level >= 3" >{{ title }}</v-breadcrumbs-item>
        </v-breadcrumbs>
      </v-col>

    </v-row>

    <v-row>
      <v-col>
        <slot></slot>
      </v-col>
    </v-row>

  </v-container>

</template>

<script>

export default {
  name: 'PlayNavView',
  props: ['title', 'level'],
  components: {
  },

}

</script>

<style scoped>

</style>