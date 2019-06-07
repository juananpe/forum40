<template>
  <div>
    <h3>Kommentarfilter</h3>
    <v-layout row wrap>
      <v-flex xs3>
        <DataSelector />
      </v-flex>
      <v-flex xs9 pl-2>
        <v-combobox v-model="filters" :items="items" label="Aktive Filter" chips clearable multiple>
          <template v-slot:selection="data">
            <v-chip :selected="data.selected" close @input="remove(data.item)">
              <strong>{{ data.item }}</strong>
            </v-chip>
          </template>
        </v-combobox>
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import DataSelector from "./DataSelector";
export default {
  data() {
    return {
      filters: [],
      items: ["Text", "Zeit", "Genauigkeit", "Nutzer"]
    };
  },

  methods: {
    remove(item) {
      this.filters.splice(this.filters.indexOf(item), 1);
      this.filters = [...this.filters];
    }
  },
  components: {
    DataSelector
  }
};
</script>

<style>
</style>
