<template>
  <v-layout>
    <v-flex v-if="showCheckbox">
      <v-checkbox
        class="justify-center"
        :input-value="checkbox"
        :color="checkBoxColor"
        :label="confidence | toPercentage"
        :disabled="!loggedIn"
        @change="annotate"
        hide-details
      ></v-checkbox>
    </v-flex>
    <div v-else-if="loggedIn">
      <v-layout>
        <v-flex pr-1>
          <v-icon outline color="success" class="action-left" @click="annotate(true)">check</v-icon>
        </v-flex>
        <v-flex pl-1>
          <v-icon outline color="error" class="action-right" @click="annotate(false)">clear</v-icon>
        </v-flex>
      </v-layout>
    </div>
    <div v-else>Keine Klassifizierung</div>
  </v-layout>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { mapGetters } from "vuex";
import { Getters } from "../store/const";

export default {
  name: "UserCommentAnnotation",
  props: {
    commentId: Number,
    labelId: Number,
    initialLabel: Boolean,
    confidence: Number
  },
  data() {
    return {
      manualLabel: undefined
    };
  },
  mounted() {},
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
    ...mapGetters([Getters.jwt, Getters.jwtLoggedIn, Getters.jwtUser]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    label() {
      if (this.manualLabel) {
        return this.manualLabel;
      }
      return this.initialLabel;
    },
    labeledManually() {
      return this.manualLabel != undefined;
    },
    checkbox() {
      if (this.label) {
        // manual label
        return this.label;
      } else {
        //Classification
        return this.confidence >= 0.5;
      }

      return false;
    },
    checkBoxColor() {
      if (this.label != undefined) {
        return "success";
      }
      return "grey";
    },
    showCheckbox() {
      return this.label != undefined || this.confidence != undefined;
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