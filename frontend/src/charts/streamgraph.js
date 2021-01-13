import * as d3 from "d3";

function streamgraph() {

var w = 1300
var h = 350

var margin = {top: 20, right: 20, bottom: 90, left: 40}
var margin2 = {top: 280, right: 20, bottom: 30, left: 40}
var width = w - margin.left - margin.right
var height = h - margin.top - margin.bottom
var height2 = h - margin2.top - margin2.bottom

var keys

var xScale = d3.scaleTime().range([0, width])
var xScale2 = d3.scaleTime().range([0, width])
var yScale = d3.scaleLinear().range([height, 0])
var yScale2 = d3.scaleLinear().range([height2, 0])

var xAxis = d3.axisBottom(xScale)
var xAxis2 = d3.axisBottom(xScale2)
var yAxis = d3.axisLeft(yScale)

var zColors = d3.scaleOrdinal()
 .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

var svg
var focus, focusPaths
var kontext
//var g
var x
var x2
var y
//var b
var kontextPaths

var area = d3.area()
 .x(d => xScale(d.data.time))
 .y0(d => yScale(d[0]))
 .y1(d => yScale(d[1]))

var area2 = d3.area()
 .x(d => xScale2(d.data.time))
 .y0(d => yScale2(d[0]))
 .y1(d => yScale2(d[1]))

var stack = d3.stack()

var brush = d3.brushX()
 .extent([[0, 0], [width, height2]])
 .on("brush end", brushed);

var brushedListender = function() {}
var oldExtend = xScale2.range()
var extend
var isBrushed = false;

function brushed() {
 var selection = d3.event.selection;
 isBrushed = selection != null

 var s = d3.event.selection || xScale2.range();

 extend = s.map(xScale2.invert, xScale2)
 xScale.domain(extend)
 focusPaths.selectAll(".path").attr("d", area)
 focus.select(".axis-x").call(xAxis);

 if(s[0] != oldExtend[0] || s[1] != oldExtend[1]) {
   brushedListender(extend)
 }
 oldExtend = s;
}

function chart(selection) {
 selection.each(function(data) {

 // def dims
 keys = Object.keys(data[0])
 keys.splice( keys.indexOf('time'), 1 )
 stack.keys(keys).order(d3.stackOrderNone)

 // create svg 
 svg = d3.select(this).selectAll("svg").data([data])
 var svgEnter = svg.enter().append("svg")

 svgEnter.append("defs").append("clipPath")
 .attr("id", "clip")
   .append("rect")
 .attr("width", width)
 .attr("height", height);

 svgEnter.append("rect")
   .attr("x", margin.left)
   .attr("y", margin.top)
   .attr("width", width)
   .attr("height", height)
   .attr("fill", "lightgrey")

 svg.merge(svgEnter)
   .attr("width", w)
   .attr("height", h)


 if(!focus) {

   focusPaths = svgEnter
     .append("g")
     .attr("class", "focusPaths")
     .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

   focus = svgEnter.append("g")
     .attr("class", "focusGroup")
     .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

   x = focus.append("g")
     .attr("class", "axis-x")
     .attr("transform", "translate(0," + height + ")")

   y = focus.append("g")
     .attr("class", "axis-y")

   kontextPaths = svgEnter
     .append("g")
     .attr("class", "kontextPaths")
     .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")")

   kontext = svgEnter.append("g")
     .attr("class", "kontextGroup")
     .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")")

   x2 = kontext.append("g")
     .attr("class", "axis-x")
     .attr("transform", "translate(0," + height2 + ")")

   kontext.append("g") // b
     .attr("class", "brush")
     .call(brush)
     .call(brush.move, [0, 0]);
 }

 drawChart()

 function drawChart() {

   var series = stack(data);

   var max = d3.max(series, layer => d3.max(layer, d => d[1]))
   var min = d3.min(series, layer => d3.min(layer, d => d[0] ))


   if(isBrushed) {
     xScale.domain(extend)
   } else {
     xScale.domain(d3.extent(data, d => d.time))
   }
   
   xScale2.domain(d3.extent(data, d => d.time) )
   yScale.domain([min, max])
   yScale2.domain([min, max])

   zColors.domain(keys);

   x2.transition().duration(300).call(xAxis2)
   x.transition().duration(300).call(xAxis)
   y.transition().duration(300).call(yAxis)

   var path = focusPaths.selectAll("path").data(series)

   path.enter()
     .append("path")
     .attr("class", "path")
     .style("fill", d => zColors(d.key))
     .attr("d", area )

   path.exit().remove()

   path
     .transition()
     .duration(300) //(duration === undefined ? 300 : duration)
     .attr("d", area);

   var path2 = kontextPaths.selectAll("path").data(series)

   path2.enter()
     .append("path")
     .style("fill", d => zColors(d.key))
     .attr("d", area2 )

   path2.exit().remove()

   path2
     .transition()
     .duration(300) //(duration === undefined ? 300 : duration)
     .attr("d", area2);
 }
})
}

chart.setStackOffset = function(offset) {
stack.offset(offset)
}

chart.setInterpolation = function(curve) {
area.curve(curve)
}

chart.setBrushedListender = function(callback) {
brushedListender = callback
}

return chart;
}

export default streamgraph