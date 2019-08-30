<template>
  <div>
    <v-radio-group v-model="radios" :mandatory="false" row class="align-center justify-center">
      <v-radio label="Tag" value="d"></v-radio>
      <v-radio label="Monat" value="m"></v-radio>
      <v-radio label="Jahr" value="y"></v-radio>
    </v-radio-group>
  </div>
</template>

<script>
import { Getters, Mutations } from "../store/const";
import { mapGetters, mapMutations } from "vuex";
import Service, { Endpoint } from "../api/db";

export default {
  methods: {
    ...mapMutations([Mutations.setTimeFrequency])
  },
  computed: {
    ...mapGetters([Getters.timeFrequency]),
    radios: {
      set(state) {
        this[Mutations.setTimeFrequency](state);
      },
      get() {
        return this[Getters.timeFrequency];
      }
    }
  }
};
</script>

<style>
</style>
