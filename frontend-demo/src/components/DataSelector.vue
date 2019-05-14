<template>
  <div id="select">
    <form>
      <p>Auswahl: {{ selection }}</p>
      <select v-model="selection">
        <option v-for="(item, index) in items" v-bind:key="index">{{ item }}</option> 
      </select>
    </form>
  </div>
</template>

<script>
  import { mapGetters, mapMutations } from "vuex";

  export default {
    name: "DataSelector",
    data: () => ({ // TODO DB query
      items: ['argumentsused', 'personalstories', 'possiblyfeedback', 'discriminating']
    }),
    methods: {
      ...mapMutations(["setCurrentLabel"])
    },
    computed: {
      ...mapGetters(["currentLabel"]),
      selection: {
        set(state) {
          this.setCurrentLabel(state)
        }, 
        get() {
          return this.currentLabel
        }
      }
    }
}
</script>