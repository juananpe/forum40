<template>
  <div class="text-xs-center">
    <v-dialog v-model="dialog" width="500">
      <template v-slot:activator="{ on }">
        <v-btn flat v-on="on">Login</v-btn>
      </template>

      <v-card>
        <v-card-title class="headline grey lighten-2" primary-title>Login</v-card-title>

        <v-form>
          <v-container fluid>
            <v-layout row wrap>
              <v-flex xs12 sm6>
                <v-text-field v-model="username" label="Username" clearable></v-text-field>
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
  </div>
</template>

<script>
import { mapActions } from "vuex";
export default {
  data() {
    return {
      dialog: false,
      username: "",
      password: "",
      show: false
    };
  },
  methods: {
    ...mapActions(["fetchJWT"]),
    login() {
      this.dialog = false;
      this.fetchJWT({ username: this.username, password: this.password });
    }
  }
};
</script>

<style>
</style>
