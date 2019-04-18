<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <h1>{{ msg2 }}</h1>
  </div>
</template>

<script>
import axios from "axios";
import Service from "../api/db"

export default {
  name: "HelloWorld",
  data: function() {
    return {
      msg: String,
      msg2 : String
    }
  },
  mounted: function() {
    var payload = {
	"pipeline":[
		{ "$match": 
			{ "title": 
				{ "$exists": true }
			}
		},
		{ "$limit": 10}
	],
	    "options": { }
};

    Service.get("db/comments/count", (status, data) => this.msg = data)
    Service.post("db/comments/aggregate", payload, (status, data) => this.msg2 = data)
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
