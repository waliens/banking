<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import { useTransactionStore } from '../stores/transactions'
import { useTransactionGroupStore } from '../stores/transactionGroups'
import api from '../services/api'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import TransactionGroupDetail from '../components/transactions/TransactionGroupDetail.vue'
import TransactionGroupDialog from '../components/transactions/TransactionGroupDialog.vue'
import DuplicateCandidates from '../components/transactions/DuplicateCandidates.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const transactionStore = useTransactionStore()
const groupStore = useTransactionGroupStore()

const transaction = ref(null)
const originalTransaction = ref(null)
const group = ref(null)
const loading = ref(false)

async function loadTransaction() {
  loading.value = true
  transaction.value = null
  originalTransaction.value = null
  group.value = null

  try {
    const id = Number(route.params.id)
    transaction.value = await transactionStore.fetchTransaction(id)

    const promises = []

    if (transaction.value.id_duplicate_of) {
      promises.push(
        transactionStore.fetchTransaction(transaction.value.id_duplicate_of)
          .then((data) => { originalTransaction.value = data })
      )
    }

    if (transaction.value.id_transaction_group) {
      promises.push(
        api.get(`/transaction-groups/${transaction.value.id_transaction_group}`)
          .then(({ data }) => { group.value = data })
      )
    }

    await Promise.all(promises)
  } finally {
    loading.value = false
  }
}

const groupDialogVisible = ref(false)

function openGroupDialog() {
  groupDialogVisible.value = true
}

function onGroupSaved() {
  loadTransaction()
}

function onGroupDeleted() {
  loadTransaction()
}

async function removeFromGroup() {
  if (!group.value) return
  const remainingIds = group.value.transactions
    .filter((t) => t.id !== transaction.value.id)
    .map((t) => t.id)
  if (remainingIds.length === 0) {
    await groupStore.deleteGroup(group.value.id)
  } else {
    await groupStore.updateGroup(group.value.id, {
      name: group.value.name,
      transaction_ids: remainingIds,
    })
  }
  await loadTransaction()
}

async function unmarkDuplicate() {
  await transactionStore.unmarkDuplicate(transaction.value.id)
  await loadTransaction()
}

function onCategoryChanged() {
  loadTransaction()
}

function onDuplicateResolved() {
  loadTransaction()
}

watch(() => route.params.id, loadTransaction, { immediate: true })
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <Button
      :label="t('flow.backToFlow')"
      icon="pi pi-arrow-left"
      text
      size="small"
      class="mb-4"
      @click="router.back()"
    />

    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
    </div>

    <template v-else-if="transaction">
      <!-- Transaction Detail -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <TransactionDetail :transaction="transaction" @categoryChanged="onCategoryChanged" />
      </div>

      <!-- Duplicate-of status -->
      <div v-if="transaction.id_duplicate_of" class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
        <h3 class="text-sm font-semibold text-amber-800 mb-2">{{ t('transactionDetail.duplicateOf') }}</h3>
        <div v-if="originalTransaction" class="flex items-center gap-4 text-sm mb-3">
          <span>{{ originalTransaction.date }}</span>
          <span class="font-medium">
            <CurrencyDisplay :amount="originalTransaction.amount" :currencySymbol="originalTransaction.currency?.symbol || ''" />
          </span>
          <span class="text-surface-500 truncate">{{ originalTransaction.description }}</span>
          <AccountDisplay v-if="originalTransaction.source" :account="originalTransaction.source" />
        </div>
        <div class="flex gap-2">
          <router-link :to="`/transactions/${transaction.id_duplicate_of}`">
            <Button :label="t('transactionDetail.viewOriginal')" severity="secondary" size="small" icon="pi pi-external-link" />
          </router-link>
          <Button :label="t('transactionDetail.unmarkDuplicate')" severity="warn" size="small" @click="unmarkDuplicate" />
        </div>
      </div>

      <!-- Duplicate Candidates -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.duplicateCandidates') }}</h3>
        <DuplicateCandidates :transactionId="transaction.id" @resolved="onDuplicateResolved" />
      </div>

      <!-- Transaction Group -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.transactionGroup') }}</h3>
        <template v-if="group">
          <TransactionGroupDetail :group="group" />
          <div class="flex gap-2 mt-3">
            <Button
              :label="t('transactionDetail.editGroup')"
              icon="pi pi-pencil"
              severity="secondary"
              size="small"
              @click="openGroupDialog"
              data-testid="edit-group-btn"
            />
            <Button
              :label="t('transactionDetail.removeFromGroup')"
              icon="pi pi-times"
              severity="warn"
              size="small"
              @click="removeFromGroup"
              data-testid="remove-from-group-btn"
            />
          </div>
        </template>
        <template v-else>
          <Button
            :label="t('transactionDetail.linkTransactions')"
            icon="pi pi-link"
            severity="secondary"
            size="small"
            @click="openGroupDialog"
            data-testid="link-transactions-btn"
          />
        </template>
      </div>

      <!-- Group Dialog -->
      <TransactionGroupDialog
        :visible="groupDialogVisible"
        @update:visible="groupDialogVisible = $event"
        :group="group"
        :initialTransaction="!group ? transaction : null"
        @saved="onGroupSaved"
        @deleted="onGroupDeleted"
      />
    </template>
  </div>
</template>
