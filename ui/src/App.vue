<template>
  <v-app
    ref="app"
    style="min-height: 100vh;"
  >
    <v-app-bar color="grey-lighten-2">
      <template v-slot:prepend>
        <v-app-bar-nav-icon
          v-show="!smAndUp"
          @click.stop="wide = !wide"
        ></v-app-bar-nav-icon>
      </template>

      <v-app-bar-title @click="$router.push({ name: 'home' })">
        BetterMS
      </v-app-bar-title>

      <div v-show="smAndUp">
          <v-btn :disabled="!$store.state.player.isAuthenticated()" color="success" variant="outlined" :to="{ name: 'play' }" flat>Play<v-icon>mdi-play-circle-outline</v-icon></v-btn>
        </div>
      <v-spacer></v-spacer>
        <div v-show="smAndUp">
          <v-btn :to="{ name: 'players' }" flat>Players<v-icon>mdi-account-outline</v-icon></v-btn>
          <v-btn :to="{ name: 'games' }" flat>Recent Games<v-icon>mdi-play</v-icon></v-btn>
          <v-btn v-bind="props" disabled="" :to="{ name: 'teams' }" flat>Teams<v-icon>mdi-account-group</v-icon></v-btn>
          <v-btn disabled="" :to="{ name: 'events' }" flat>Events<v-icon>mdi-calendar-check-outline</v-icon></v-btn>
        </div>


      <v-spacer></v-spacer>

      <div v-if="!$store.state.player.isAuthenticated()">
        <AuthForm> </AuthForm>
      </div>
      <div v-else>
        <ProfileLink></ProfileLink>
      </div>
    </v-app-bar>
    <v-navigation-drawer v-model="wide" color="grey-darken-2" temporary>
      <v-list>
        <v-list-item><v-btn flat>Players</v-btn></v-list-item>
        <v-list-item><v-btn flat>Teams</v-btn></v-list-item>
        <v-list-item><v-btn flat>Events</v-btn></v-list-item>
        <v-list-item><v-btn flat>Results</v-btn></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-row style="height: 100%">
<!--      <v-col style="background: #cdcdcd; padding-top: 110px" cols="0" lg="2" v-show="!mdAndDown">-->
<!--        <div>-->
<!--          <h3 class="text-center">Top Team</h3>-->
<!--          <team-sub-view class="pa-0" :team="topTeam"></team-sub-view>-->
<!--        </div>-->

<!--      </v-col>-->
      <v-col v-if="!mdAndDown" lg="2">

      </v-col>
      <v-col style="background: #dbdbdb; padding-top: 50px; padding-bottom: 50px" cols="12" lg="8" >
        <v-main>
          <router-view style="background: #efefef">
          </router-view>
        </v-main>
      </v-col>

      <v-col v-if="!mdAndDown" style="background: #cdcdcd; padding-top: 110px" cols="0" lg="2" v-show="!lgAndDown">
        <h3 class="text-center">Top Players</h3>
        <player-list :exclude="['team', 'winrate', 'games_played']" :players="topPlayersView.players"></player-list>
      </v-col>
    </v-row>

    <v-footer
      style="background: #efefef; width: 100%"
    >
      <div class="d-flex flex-row align-end" style="width: 100%; height: 100%">
        <v-card
          elevation="0"
          rounded="0"
          width="100%"
          class="text-center"
          :style="{ background: $vuetify.theme.themes.light.colors.background }"
        >
          <v-card-text>
            <v-btn class="mx-4" icon="mdi-home" variant="plain"></v-btn>
            <v-btn class="mx-4" icon="mdi-email" variant="plain"></v-btn>
            <v-btn class="mx-4" icon="mdi-calendar" variant="plain"></v-btn>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-text>
            {{ new Date().getFullYear() }} — <strong>Vuetify</strong>
            <p>
              Thank you to <a href="https://crafatar.com">Crafatar</a> for
              providing avatars.
            </p>
          </v-card-text>
        </v-card>
      </div>
    </v-footer>
  </v-app>
</template>

<script>
import { useDisplay } from "vuetify";
import AuthForm from "./components/AuthForm.vue";
import API from "./api/api";
import ProfileLink from "./components/ProfileLink.vue";
import { TopPlayersView, TopTeamView } from './api/model/models';
import PlayerList from './components/lists/PlayerList.vue';

export default {
  name: "App",

  components: { AuthForm, ProfileLink, PlayerList },

  data: () => ({
    wide: false,
    left_active: true,
    topTeam: TopTeamView.createView([{obj_id: null, entity: 'Team'}]),
    topPlayersView: TopPlayersView.createView(
        [{obj_id: null, entity: 'Player'}]
    ),
    icon: null,
  }),

  async created() {
    this.$vuetify.theme.themes.light.colors.background = "#e0e0e0";
    this.$vuetify.theme.themes.light.colors.primary = "#3b9b3b";

    try {
      let player = await API.getMe();
      this.$store.commit("setPlayer", player);
      // const modelsDependOnAuth = eventDependencyMap['auth'] || [];
      //
      // for (let model of modelsDependOnAuth) {
      //   model.initiateRefresh();
      // }

    } catch (e) {
      console.warn(e);
    }
  },

  setup() {
    const { xs, smAndUp, smAndDown, mdAndDown, lgAndDown } = useDisplay();
    return { xs, smAndUp, smAndDown, mdAndDown, lgAndDown };
  },
};
</script>


<style scoped>
.v-footer {
  padding: 0% !important;
}
body {
  overflow-y: hidden;
}
</style>
