<template>
  <v-layout row>
    <v-flex :xs10="loggedIn" :xs12="!loggedIn">
      <v-select v-model="selection" :items="items" label="Label-Filter" chips clearable multiple>
        <template v-slot:selection="data">
          <v-chip :selected="data.selected" close @input="remove(data.item)">
            <strong>{{ data.item }}</strong>
          </v-chip>
        </template>
      </v-select>
    </v-flex>
    <v-flex xs2 v-if="loggedIn">
      <v-dialog v-model="dialog" width="300" @keydown.enter.prevent="addLabel">
        <template v-slot:activator="{ on }">
          <v-btn small outline color="success" v-on="on">Label erstellen</v-btn>
        </template>

        <v-card>
          <v-card-title class="headline grey lighten-2" primary-title>Label erstellen</v-card-title>

          <v-form>
            <v-container fluid>
              <v-layout row wrap>
                <v-flex xs12>
                  <v-text-field
                    v-if="dialog"
                    autofocus
                    v-model="newLabel"
                    label="Neues Label"
                    clearable
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-form>
          <v-divider></v-divider>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" flat @click="addLabel">Hinzufügen</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-alert v-model="success" dismissible type="success" class="center">Label hinzugefügt!</v-alert>
      <v-alert v-model="error" type="error" dismissible class="center">Label bereits vorhanden!</v-alert>
    </v-flex>
  </v-layout>
</template>

<script>
import { Getters, Mutations } from "../store/const";
import { mapGetters, mapMutations } from "vuex";
import Service, { Endpoint } from "../api/db";

export default {
  name: "DataSelector",

  data: () => ({
    items: [],
    dialog: false,
    newLabel: "",
    error: false,
    success: false
  }),
  methods: {
    ...mapMutations([Mutations.setSelectedLabels]),
    async fetchLabels() {
      const { data } = await Service.get(Endpoint.LABELS);
      this.items = data.labels;
    },
    remove(item) {
      this.selection.splice(this.selection.indexOf(item), 1);
      this.selection = [...this.selection];
    },
    async addLabel() {
      this.dialog = false;
      try {
        await Service.put(
          Endpoint.ADD_LABEL(this.newLabel),
          {},
          this[Getters.jwt]
        );
        this.fetchLabels();
        this.success = true;
      } catch (error) {
        const status = error.response.status;
        if (status === 400) {
          this.error = true;
        }
      }
      this.newLabel = "";
    }
  },
  mounted() {
    this.fetchLabels();
  },
  computed: {
    ...mapGetters([Getters.jwt, Getters.selectedLabels, Getters.jwtLoggedIn]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    selection: {
      set(state) {
        this[Mutations.setSelectedLabels](state);
      },
      get() {
        return this[Getters.selectedLabels];
      }
    }
  }
};
</script>

<style>
.center {
  position: fixed;
  right: 20px;
  top: 5%;
}
</style>
