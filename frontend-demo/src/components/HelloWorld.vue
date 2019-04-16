<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "HelloWorld",
  props: {
    msg: String
  },

  mounted: function() {
    var config = {
      pipeline: [{ $match: { title: { $exists: true } } }, { $limit: 10 }],
      options: {}
    };

    console.log(process.env);

    axios
      .post(process.env.VUE_APP_ROOT_API + "comments/aggregate", config)
      .then(response => {
        this.msg = response.data;
      })
      .catch(e => {
        this.msg = e;
        console.log(e);
      });
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
