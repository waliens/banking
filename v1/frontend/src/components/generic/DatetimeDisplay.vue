<template>
  <span>{{ formattedDatetime }}</span>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import moment from 'moment-timezone';


export default defineComponent({
  props: {
    datetime: {
      type: [String, Date, moment],
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
      let datetime = this.datetime;
      if (this.datetime instanceof Date) {
        datetime = moment(this.datetime)
      }
      if (this.datetime instanceof moment) {
        datetime = this.datetime.toISOString();
      }
      return this.asdate ? this.formatDate(datetime) : this.formatDatetime(datetime);
    }
  },
  methods: {
    formatDate(iso8601) {
      const datetime = moment(iso8601);
      return datetime.format('DD/MM/YYYY');
    },
    formatDatetime(iso8601) {
      const datetime = moment(iso8601);
      return datetime.format('DD/MM/YYYY HH:mm');
    }
  }
})
</script>