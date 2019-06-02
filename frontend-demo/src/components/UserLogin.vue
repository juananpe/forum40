<template>
  <div class="text-xs-center">
    <div v-if="jwtLoggedIn">
      <v-menu bottom left>
        <template v-slot:activator="{ on }">
          <v-btn flat v-on="on">{{jwtUser}}</v-btn>
        </template>

        <v-list>
          <v-list-tile @click="checkLogin">
            <v-list-tile-title>Check login</v-list-tile-title>
          </v-list-tile>

          <v-list-tile @click="logout">
            <v-list-tile-title>Logout</v-list-tile-title>
          </v-list-tile>
        </v-list>
      </v-menu>
      <v-alert v-model="testalert" dismissible type="success">Sie sind authentifiziert!</v-alert>
    </div>
    <div v-else>
      <v-dialog v-model="dialog" width="500" @keydown.enter.prevent="login">
        <template v-slot:activator="{ on }">
          <v-btn flat v-on="on">Login</v-btn>
        </template>

        <v-card>
          <v-card-title class="headline grey lighten-2" primary-title>Login</v-card-title>

          <v-form>
            <v-container fluid>
              <v-layout row wrap>
                <v-flex xs12 sm6>
                  <v-text-field
                    v-if="dialog"
                    autofocus
                    v-model="username"
                    label="Username"
                    clearable
                  ></v-text-field>
                </v-flex>

                <v-flex xs12 sm6>
                  <v-text-field
                    v-model="password"
                    :append-icon="show ? 'visibility' : 'visibility_off'"
                    :type="show ? 'text' : 'password'"
                    name="password"
                    label="Password"
                    @click:append="show = !show"
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-form>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" flat @click="login">Login</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-alert :value="error" type="error" dismissible>Login fehlgeschlagen!</v-alert>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions, mapState } from "vuex";
import Service from "../api/db";
export default {
  data() {
    return {
      dialog: false,
      error: false,
      testalert: false,
      username: "",
      password: "",
      show: false
    };
  },
  computed: {
    ...mapGetters(["jwt", "jwtUser", "jwtLoggedIn", "jwtExpiration"]),
    ...mapState(["now"])
  },
  methods: {
    ...mapActions(["fetchJWT", "logout"]),
    async login() {
      this.dialog = false;
      const success = await this.fetchJWT({
        username: this.username,
        password: this.password
      });
      if (!success) this.error = true;
    },
    async checkLogin() {
      const { data } = await Service.get("db/auth/test", this.jwt);
      if (data.ok === this.jwtUser) {
        this.testalert = true;
      }
    }
  }
};
</script>

<style>
</style>
