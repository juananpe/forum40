<template>
  <div>
    <v-radio-group v-model="radios" :mandatory="false" row class="align-center justify-center">
      <v-radio :label="$t('granularity.day')" value="d"></v-radio>
      <v-radio :label="$t('granularity.month')" value="m"></v-radio>
      <v-radio :label="$t('granularity.year')" value="y"></v-radio>
    </v-radio-group>
  </div>
</template>

<script>
import { Getters, Mutations } from "../store/const";
import { mapGetters, mapMutations } from "vuex";

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
