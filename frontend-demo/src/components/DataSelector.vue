<template>
  <v-layout align-center>
    <v-flex xs4 pr-2>
      <v-select
        :items="sources.map(e=>e['name'])"
        v-on:change="sourceChanged"
        v-model="selectedSource"
        label="Datenquelle"
        chips
      ></v-select>
    </v-flex>

    <v-flex :xs6="loggedIn" :xs8="!loggedIn" pr-2>
      <v-select
        v-model="selection"
        :items="Object.keys(labels)"
        chips
        clearable
        multiple
        label="Ausgewählte Labels"
      >
        <template v-slot:selection="data">
          <v-chip :input-value="data.selected" close @click:close="remove(data.item)">
            <strong>{{ data.item }}</strong>
          </v-chip>
        </template>
      </v-select>
    </v-flex>
    <v-flex xs2 v-if="loggedIn">
      <v-dialog v-model="dialog" width="300" @keydown.enter.prevent="addLabel">
        <template v-slot:activator="{ on }">
          <v-btn
            small
            :disabled="selectedSource===undefined"
            outlined
            color="success"
            v-on="on"
          >Label erstellen</v-btn>
        </template>

        <v-card>
          <v-card-title class="headline primary white--text" primary-title>Label erstellen</v-card-title>

          <v-form>
            <v-container fluid>
              <v-layout wrap>
                <v-flex xs12>
                  <v-text-field
                    v-if="dialog"
                    autofocus
                    v-model="newLabel"
                    label="Neue Label Beschreibung"
                    clearable
                  ></v-text-field>
                </v-flex>
              </v-layout>
            </v-container>
          </v-form>
          <v-divider></v-divider>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="addLabel">Erstellen</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-alert v-model="success" dismissible type="success" class="center">Label hinzugefügt!</v-alert>
      <v-alert v-model="error" type="error" dismissible class="center">Label bereits vorhanden!</v-alert>
    </v-flex>
  </v-layout>
</template>

<script>
import { State, Getters, Mutations } from "../store/const";
import { mapState, mapGetters, mapMutations } from "vuex";
import Service, { Endpoint } from "../api/db";

export default {
  name: "DataSelector",

  data: () => ({
    dialog: false,
    newLabel: "",
    error: false,
    success: false
  }),
  methods: {
    ...mapMutations([
      Mutations.setSelectedLabels,
      Mutations.setLabels,
      Mutations.setSource,
      Mutations.setSources
    ]),
    async fetchSources() {
      const { data } = await Service.get(Endpoint.SOURCES);
      if (data.length > 0) {
        this[Mutations.setSources](data);
        this[Mutations.setSource](data[0].name);
        this.fetchLabels();
      }
    },
    async fetchLabels() {
      const { data } = await Service.get(
        Endpoint.LABELS(this[Getters.getSelectedSource].id)
      );
      const labels = {};
      const labels_names = data.labels;
      const label_ids = data.ids;
      labels_names.forEach((key, i) => (labels[key] = label_ids[i]));
      this[Mutations.setLabels](labels);
    },
    remove(item) {
      this.selection.splice(this.selection.indexOf(item), 1);
      this.selection = [...this.selection];
    },
    async addLabel() {
      if (this.selectedSource === undefined) return;
      this.dialog = false;
      try {
        await Service.put(
          Endpoint.ADD_LABEL(this.newLabel, this[Getters.getSelectedSource].id),
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
    },
    sourceChanged(value) {
      this.selection = [];
      this.fetchLabels();
    }
  },
  mounted() {
    this.fetchSources();
  },
  computed: {
    ...mapState([State.sources, State.source, State.labels]),
    ...mapGetters([
      Getters.jwt,
      Getters.selectedLabels,
      Getters.jwtLoggedIn,
      Getters.getSelectedSource
    ]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    selection: {
      set(state) {
        const selectedLabels = {};
        state.forEach(label => {
          selectedLabels[label] = this[State.labels][label];
        });
        this[Mutations.setSelectedLabels](selectedLabels);
      },
      get() {
        return this[Getters.selectedLabels];
      }
    },
    selectedSource: {
      get() {
        return this[State.source];
      },
      set(state) {
        this[Mutations.setSource](state);
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
