<template>
  <v-select
      :items="languages"
      v-model="$i18n.locale"
      class="language-select"
  />
</template>

<script>
  export default {
    computed: {
      languages() {
        return Object.keys(this.$i18n.messages)
            .map(value => ({value, text: value.toUpperCase()}));
      }
    }
  }
</script>

<style>
.language-select {
  flex: none;
  width: 4rem;
}

.language-select .v-input__control {
  flex-direction: row;
  flex-wrap: nowrap;
}
</style>
