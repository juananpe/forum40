<template>
  <v-layout>
    <v-flex xs12 v-if="loggedIn">
      <div v-if="label != undefined">
        <v-checkbox
          class="justify-center"
          :input-value="label"
          color="green"
          :disabled="!loggedIn"
          @change="annotate"
          hide-details
          prepend-icon="person"
        ></v-checkbox>
      </div>
      <div v-else>
        <v-flex xs5 pr-1>
          <v-icon outline color="success" class="action-left" @click="annotate(true)">check</v-icon>
        </v-flex>
        <v-flex xs5 pl-1>
          <v-icon outline color="error" class="action-right" @click="annotate(false)">clear</v-icon>
        </v-flex>
      </div>
    </v-flex>

    <v-flex xs12>
      <div v-if="majority != undefined">
        <v-checkbox
          class="justify-center"
          :input-value="majority[0]>=majority[1]"
          color="black"
          disabled
          hint="Test"
          prepend-icon="people"
        ></v-checkbox>
      </div>
      <div v-else>
        <v-icon>not_interested</v-icon>
      </div>
    </v-flex>

    <v-flex xs12>
      <div v-if="confidence != undefined">
        <v-checkbox
          class="justify-center"
          :input-value="confidence>=0.5"
          color="grey"
          :label="confidence | toPercentage"
          :prepend-icon="svgPath"
          disabled
          hide-details
        ></v-checkbox>
      </div>
      <div v-else>
        <v-icon>not_interested</v-icon>
      </div>
    </v-flex>
  </v-layout>
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
      if (this.manualLabel) {
        return this.manualLabel;
      }
      return this.personalLabel;
    }
  }
};
</script>

<style>
.v-input__slot {
  align-items: center;
  justify-content: center;
}
</style>