<template>
  <div>
    <v-layout>
      <v-flex xs12 v-if="loggedIn" class="text-center">
        <div v-if="label != undefined">
          <v-tooltip right>
            <template v-slot:activator="{ on }">
              <v-checkbox
                v-on="on"
                class="justify-center ma-0 pa-1"
                :input-value="label"
                color="green"
                :readonly="!loggedIn"
                @change="annotate"
                hide-details
                prepend-icon="person"
              ></v-checkbox>
            </template>
            <span
              v-if="majority !== undefined"
            >Klassifizierung der Mehrheit ({{majority[0]}} von {{majority[0]+majority[1]}})</span>
          </v-tooltip>
        </div>
        <div v-else>
          <v-icon outline color="success" class="action-left" @click="annotate(true)">check</v-icon>

          <v-icon outline color="error" class="action-right" @click="annotate(false)">clear</v-icon>
        </div>
      </v-flex>
    </v-layout>
    <v-layout>
      <v-flex v-if="!loggedIn" xs12 class="text-center">
        <div v-if="majority != undefined">
          <v-tooltip right>
            <template v-slot:activator="{ on }">
              <v-checkbox
                v-on="on"
                class="justify-center ma-0 pa-1"
                :input-value="majority[0]>=majority[1]"
                color="grey darken-1"
                readonly
                hide-details
                prepend-icon="people"
              ></v-checkbox>
            </template>
            <span>Klassifizierung der Mehrheit ({{majority[0]}} zu {{majority[1]}})</span>
          </v-tooltip>
        </div>
        <div v-else>
          <v-icon>people</v-icon>
          <v-tooltip right>
            <template #activator="{ on }">
              <v-icon v-on="on" class="mr-1 ml-1">not_interested</v-icon>
            </template>
            <span>Keine weiteren Labels vorhanden</span>
          </v-tooltip>
        </div>
      </v-flex>
    </v-layout>
    <v-layout>
      <v-flex xs12 class="text-center">
        <div v-if="confidence != undefined">
          <v-tooltip right>
            <template v-slot:activator="{ on }">
              <v-checkbox
                v-on="on"
                class="justify-center ma-0 pa-0"
                :input-value="confidence>=0.5"
                color="grey darken-1"
                :prepend-icon="svgPath"
                readonly
                hide-details
              ></v-checkbox>
            </template>
            <span>Automatische Klassifizierung ({{1-confidence | toPercentage}} Konfidenz)</span>
          </v-tooltip>
        </div>
        <div v-else>
          <v-icon>{{svgPath}}</v-icon>
          <v-tooltip right>
            <template #activator="{ on }">
              <v-icon v-on="on" class="ml-1">not_interested</v-icon>
            </template>
            <span>Keine Klassifizierung vorhanden</span>
          </v-tooltip>
        </div>
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { mapGetters } from "vuex";
import { Getters } from "../store/const";
import { mdiRobot } from "@mdi/js";

export default {
  name: "UserCommentAnnotation",
  props: {
    commentId: Number,
    labelId: Number,
    personalLabel: Boolean,
    majority: Array,
    confidence: Number
  },
  data() {
    return {
      manualLabel: undefined,
      svgPath: mdiRobot
    };
  },
  mounted() {
    this.personalLabel;
  },
  filters: {
    toPercentage(value) {
      if (value) return Math.round(value * 100) + "%";
      return "";
    }
  },
  methods: {
    async annotate(value) {
      try {
        await Service.put(
          Endpoint.ADD_ANNOTATION_TO_COMMENT(
            this.commentId,
            this.labelId,
            +value
          ),
          {},
          this[Getters.jwt]
        );
        this.manualLabel = value;
        return true;
      } catch (error) {
        const status = error.response.status;
        console.error(error);
        console.error(status);
        return false;
      }
    }
  },
  computed: {
    ...mapGetters([Getters.jwt, Getters.jwtLoggedIn]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    label() {
      if (this.manualLabel != undefined) {
        return this.manualLabel;
      }
      return this.personalLabel;
    }
  }
};
</script>

<style>
</style>