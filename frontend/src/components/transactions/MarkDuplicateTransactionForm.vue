<template>
  <div class="modal-card" style="width: auto">
    <header class="modal-card-head">
      <p class="modal-card-title">{{ $t('transaction.duplicate.mark.title') }}</p>
      <button class="delete" icon-left="times" @click="$emit('close')"></button>
    </header>
    <section class="modal-card-body">
      <section>
        <div v-if="transactions.length > 0">
          <b-field :label="$t('transaction.duplicate.mark.original')" label-position="on-border">
            <b-select v-model="selectedOriginal">
              <option v-for="t in transactions" :key="t.id" :value="t">
                <p>{{ $t('transaction.title') }} #{{ t.id }} - <datetime-display :asdate="true" :datetime="t.when" /></p>
              </option>
            </b-select>

          </b-field>
        </div>
        <div v-else>
          <b-message
            :has-icon="true"
            icon="info-circle"
            icon-size="small"
            type="is-danger"
          >
            <p>{{ $t('transaction.duplicate.mark.no_candidate') }}</p>
          </b-message>

        </div>
      </section>
      <section>
        <duplicate-comparison-table :duplicate-transaction="candidateTransaction" :original-transaction="selectedOriginal" />
      </section>
    </section>
    <footer class="modal-card-foot">
      <b-button
        :label="$t('cancel')"
        @click="$emit('close')" />
    <b-button
        :label="$t('apply')"
        type="is-primary"
        @click="markAsDuplicate" />
    </footer>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Transaction from '@/utils/api/Transaction';
import DuplicateComparisonTable from './DuplicateComparisonTable.vue';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay.vue';

export default defineComponent({
  components: { DuplicateComparisonTable, DatetimeDisplay },
  props: {
    candidateTransaction: {
      type: Transaction,
      required: true
    }
  },
  data() {
    return {
      selectedOriginal: null,
      transactions: []
    };
  },
  async mounted() {
    this.transactions = await this.candidateTransaction.getCandidateDuplicates();
  },
  methods: {
    async markAsDuplicate() {
      await this.candidateTransaction.markAsDuplicate(this.selectedOriginal.id).then(() => {
        this.$buefy.toast.open({
          message: this.$t('transaction.duplicate.mark.success'),
          type: 'is-success'
        });
        this.$emit('close');
      }).catch(() => {
        this.$buefy.toast.open({
          message: this.$t('transaction.duplicate.mark.error'),
          type: 'is-danger'
        });
      });
    }
  }
});
</script>
