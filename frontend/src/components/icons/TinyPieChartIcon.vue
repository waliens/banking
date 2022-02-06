
<template>
  <svg :height="svgDimension" :width="svgDimension" :viewBox="`0 0 ${svgDimension} ${svgDimension}`">
    <path :d="d" :fill="color" :fill-opacity="opacity" style="stroke-opacity: 0;" stroke-width="1px"></path>
  </svg>
</template>


<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: {
    ratio: {type: Number}, 
    color: {type: String, default: "black"},
    opacity: {type: Number, default: 0.8},
    isSmall: {type: Boolean},
    isMedium: {type: Boolean},
    isLarge: {type: Boolean} 
  },
  data() {
    return {
      startAngle: - Math.PI / 2,
      margin: 2
    };
  },
  computed: {
    svgDimension() {
      if (this.isSmall) {
        return 10;
      } else if (this.isLarge) {
        return 30;
      } else {
        return 20;
      } 
    },
    dimension() {
      return this.svgDimension - 2 * this.margin;
    },
    radius() {
      return this.dimension/2;
    },
    endAngle() {
      return this.startAngle - 2 * Math.PI * (this.ratio >= 1.0 ? 0.9999999 : this.ratio); 
    },
    largeArc() {
      return this.ratio > 0.5 ? "1" : "0";
    },
    sweepFlag() {
      return "0";
    },
    d() {
      let xCenter = this.margin + this.dimension / 2, yCenter = this.margin + this.dimension / 2;
      let xStart = xCenter + this.radius * Math.cos(this.startAngle),
          yStart = yCenter + this.radius * Math.sin(this.startAngle),
          xEnd = xCenter + this.radius * Math.cos(this.endAngle),
          yEnd = yCenter + this.radius * Math.sin(this.endAngle);
      return `M ${xCenter}, ${yCenter} L ${xStart}, ${yStart} A ${this.radius}, ${this.radius} 0 ${this.largeArc},${this.sweepFlag} ${xEnd}, ${yEnd} Z`;
    }
  }
})
</script>
