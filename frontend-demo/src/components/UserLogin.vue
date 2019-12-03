<template>
  <div class="text-xs-center">
    <div v-if="jwtLoggedIn">
      <v-menu bottom left>
        <template v-slot:activator="{ on }">
          <v-btn color="primary" v-on="on">{{jwtUser}}</v-btn>
        </template>

        <v-list>
          <v-list-item @click="checkLogin">
            <v-list-item-title>Check Authentifizierung</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logoutClicked">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      <v-alert
        v-model="testalert"
        dismissible
        type="success"
        class="center"
      >Sie sind authentifiziert!</v-alert>
    </div>
    <div v-else>
      <v-dialog v-model="dialog" width="500" @keydown.enter.prevent="loginUser">
        <template v-slot:activator="{ on }">
          <v-btn color="primary" v-on="on">Einloggen</v-btn>
        </template>

        <v-card>
          <v-card-title class="headline primary white--text" primary-title>Login</v-card-title>

          <v-form>
            <v-container>
              <v-layout>
                <v-flex xs12 sm6 pr-3>
                  <v-text-field
                    v-if="dialog"
                    autofocus
                    v-model="username"
                    label="Nutzername"
                    clearable
                  ></v-text-field>
                </v-flex>

                <v-flex xs12 sm6 pl-3>
                  <v-text-field
                    v-model="password"
                    :append-icon="show ? 'visibility' : 'visibility_off'"
                    :type="show ? 'text' : 'password'"
                    name="password"
                    label="Passwort"
                    @click:append="show = !show"
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-form>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="loginUser">Einloggen</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-alert v-model="error" type="error" dismissible class="center">Einloggen fehlgeschlagen!</v-alert>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from "vuex";
import Service, { Endpoint } from "../api/db";
import { Getters, Actions } from "../store/const";
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
    ...mapGetters([Getters.jwt, Getters.jwtUser, Getters.jwtLoggedIn])
  },
  methods: {
    ...mapActions([Actions.login, Actions.logout]),
    async loginUser() {
      this.dialog = false;
      const success = await this[Actions.login]({
        username: this.username,
        password: this.password
      });
      this.username = "";
      this.password = "";
      if (!success) this.error = true;
    },
    async checkLogin() {
      const { data } = await Service.get(
        Endpoint.TEST_LOGIN,
        this[Getters.jwt]
      );
      if (data.ok === this[Getters.jwtUser]) {
        this.testalert = true;
      }
    },
    logoutClicked() {
      this[Actions.logout]();
    }
  }
};
</script>

<style>
.center {
  position: fixed;
  right: 20px;
  top: 50%;
}
</style>
