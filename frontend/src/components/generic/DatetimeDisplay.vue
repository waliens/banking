<template>
  <span>{{ formattedDatetime }}</span>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import moment from 'moment-timezone';


export default defineComponent({
  props: {
    datetime: {
      type: String,
      required: true
    },
    asdate: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  computed: {
    formattedDatetime() {
      return this.asdate ? this.formatDate(this.datetime) : this.formatDatetime(this.datetime); 
    }
  },
  methods: {
    formatDate(iso8601) {
      const datetime = moment(iso8601);
      return datetime.format('L');
    },
    formatDatetime(iso8601) {
      const datetime = moment(iso8601);
      return datetime.format('LLL');
    }
  }
})
</script>