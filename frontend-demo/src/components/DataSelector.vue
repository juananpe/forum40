<template>
<div id="select">
    <v-select :items="items" label="Standard" ></v-select>

 <form>
  <p>Auswahl: {{ selected }}</p>
    <select v-model="selected">
      <option v-for="(item, index) in items" v-bind:key="index">{{ item }}</option> 
    </select>
</form>

</div>
</template>

<script>
  export default {
    name: "DataSelector",
    methods: {

    },
    data: () => ({ // TODO DB query
      selected : 'argumentsused',
      items: ['argumentsused', 'personalstories', 'possiblyfeedback', 'discriminating']
    })
  }
</script>