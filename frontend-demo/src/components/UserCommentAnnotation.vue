<template>
  <v-layout row wrap justify-center>
    <v-flex v-if="showCheckbox" class="text-xs-center" row>
      <v-checkbox
        class="align-center justify-center"
        :input-value="checkbox"
        :color="checkBoxColor"
        :label="label.confidence[0] | toPercentage"
        :disabled="!loggedIn"
        @change="checkboxClicked"
        hide-details
      ></v-checkbox>
    </v-flex>
    <div v-else-if="loggedIn">
      <v-layout class="text-xs-center" row>
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
    commentId: String,
    initialLabel: Object,
    labelName: String
  },
  data() {
    return {
      labeledManually: false,
      manualLabel: false
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
    async checkboxClicked(value) {
      try {
        await Service.put(
          Endpoint.ADD_LABEL_TO_COMMENT(this.commentId, this.labelName, +value),
          {},
          this[Getters.jwt]
        );
        this.labeledManually = true;
        return true;
      } catch (error) {
        const status = error.response.status;
        console.error(error);
        console.error(status);
        return false;
      }
    },
    async annotate(value) {
      if (await this.checkboxClicked(value)) {
        this.manualLabel = {
          confidence: [],
          manualLabel: {
            annotatorId: this[Getters.jwtUser],
            label: value
          }
        };
        this.labeledManually = true;
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
    checkbox() {
      if (this.label) {
        if (this.label.manualLabel) {
          return this.label.manualLabel.label;
        } else {
          return this.label.confidence[0] > 0.5;
        }
      }
      return false;
    },
    checkBoxColor() {
      if (this.label.manualLabel || this.labeledManually) {
        return "success";
      }
      return "grey";
    },
    showCheckbox() {
      return (
        this.label &&
        (this.label.confidence.length > 0 || this.label.manualLabel)
      );
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