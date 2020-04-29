<template>
  <v-layout>
    <v-flex xs12 class="text-center" style="display:inline-flex; justify-content: center;">
      <span v-if="loggedIn" class="text-center">
        <span v-if="label != undefined">
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-icon v-if="label" @click="annotate(false)" v-on="on">{{svgCheckbox}}</v-icon>

              <v-icon v-else @click="annotate(true)" v-on="on">{{svgRectangle}}</v-icon>
            </template>
            <span
              v-if="majority !== undefined"
            >Klassifizierung der Mehrheit ({{majority[0]}} von {{majority[0]+majority[1]}})</span>
          </v-tooltip>
        </span>

        <span v-else>
          <div>
            <v-icon outline color="success" class="action-left" @click="annotate(true)">check</v-icon>
          </div>

          <div>
            <v-icon outline color="error" class="action-right" @click="annotate(false)">clear</v-icon>
          </div>
        </span>
      </span>

      <span v-if="!loggedIn">
        <span v-if="majority != undefined">
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-icon v-if="majority[0]>=majority[1]" v-on="on">{{svgCheckbox}}</v-icon>
              <v-icon v-else v-on="on">{{svgRectangle}}</v-icon>
            </template>
            <span>Klassifizierung der Mehrheit ({{majority[0]}} von {{majority[0]+majority[1]}})</span>
          </v-tooltip>
        </span>
        <span v-else>
          <v-tooltip top>
            <template #activator="{ on }">
              <v-icon v-on="on" class="mr-0 ml-0">not_interested</v-icon>
            </template>
            <span>Keine weiteren Labels vorhanden</span>
          </v-tooltip>
        </span>
      </span>

      <span :class="{centerClassificationIcon:label===undefined && loggedIn}">
        <span v-if="confidence != undefined">
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-icon v-if="confidence>=0.5" v-on="on" class="ml-1">{{svgCheckbox}}</v-icon>
              <v-icon v-else v-on="on" class="ml-1">{{svgRectangle}}</v-icon>
            </template>
            <span>Automatische Klassifizierung ({{confidence > 0.5? confidence : 1-confidence | toPercentage}} Konfidenz)</span>
          </v-tooltip>
        </span>
        <span v-else>
          <v-tooltip top>
            <template #activator="{ on }">
              <v-icon v-on="on" class="ml-1">not_interested</v-icon>
            </template>
            <span>Keine Klassifizierung vorhanden</span>
          </v-tooltip>
        </span>
      </span>
    </v-flex>

    <v-snackbar v-model="snackbar" :timeout="timeout" top right>
      {{ text }}
      <v-btn color="blue" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </v-layout>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { mapGetters } from "vuex";
import { Getters } from "../store/const";
import { mdiCropSquare, mdiCheckBoxOutline } from "@mdi/js";

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
      svgRectangle: mdiCropSquare,
      svgCheckbox: mdiCheckBoxOutline,
      snackbar: false,
      text: "Snackbar text",
      timeout: 4000
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
        const { data } = await Service.put(
          Endpoint.ADD_ANNOTATION_TO_COMMENT(
            this.commentId,
            this.labelId,
            +value
          ),
          {},
          this[Getters.jwt]
        );
        const { annotations } = data;
        const label_name = this[Getters.getLabelname](this.labelId);
        this.text = `${annotations} annotierte`;
        if (annotations == 1) this.text += "r";
        this.text += ` "${label_name}" Kommentar`;
        if (annotations > 1) this.text += "e";
        this.text += ".";
        this.snackbar = true;

        this.manualLabel = value;
        return true;
      } catch (error) {
        console.error(error);
        return false;
      }
    }
  },
  computed: {
    ...mapGetters([Getters.jwt, Getters.jwtLoggedIn, Getters.getLabelname]),
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
.centerClassificationIcon {
  position: relative;
  top: 25%;
}
</style>