<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../../stores/wallets'
import { useAccountStore } from '../../stores/accounts'
import { useActiveWalletStore } from '../../stores/activeWallet'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'

const { t } = useI18n()
const toast = useToast()
const walletStore = useWalletStore()
const accountStore = useAccountStore()
const activeWalletStore = useActiveWalletStore()

const showDialog = ref(false)
const editingWallet = ref(null)
const form = ref({ name: '', description: '', accountIds: [] })

function openCreate() {
  editingWallet.value = null
  form.value = { name: '', description: '', accountIds: [] }
  showDialog.value = true
}

function openEdit(wallet) {
  editingWallet.value = wallet
  form.value = {
    name: wallet.name,
    description: wallet.description || '',
    accountIds: wallet.accounts.map((a) => a.id_account),
  }
  showDialog.value = true
}

async function save() {
  const payload = {
    name: form.value.name,
    description: form.value.description || null,
    accounts: form.value.accountIds.map((id) => ({ id_account: id, contribution_ratio: 1.0 })),
  }
  try {
    if (editingWallet.value) {
      await walletStore.updateWallet(editingWallet.value.id, payload)
    } else {
      await walletStore.createWallet(payload)
    }
    showDialog.value = false
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

async function handleDelete(wallet) {
  if (!confirm(`Delete wallet "${wallet.name}"?`)) return
  await walletStore.deleteWallet(wallet.id)
}

function setAsDefault(walletId) {
  activeWalletStore.setActiveWallet(walletId)
  toast.add({ severity: 'success', summary: t('settings.defaultWallet'), detail: t('common.save'), life: 2000 })
}

onMounted(async () => {
  await Promise.all([walletStore.fetchWallets(), accountStore.fetchAccounts()])
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold">{{ t('settings.wallets') }}</h2>
      <Button :label="t('common.create')" icon="pi pi-plus" @click="openCreate" size="small" />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="wallet in walletStore.wallets"
        :key="wallet.id"
        class="bg-surface-0 rounded-xl shadow p-4"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-semibold">{{ wallet.name }}</h3>
            <i
              v-if="activeWalletStore.activeWalletId === wallet.id"
              class="pi pi-star-fill text-yellow-500 text-sm"
              :title="t('settings.defaultWallet')"
            />
          </div>
          <div class="flex gap-1">
            <Button
              v-if="activeWalletStore.activeWalletId !== wallet.id"
              icon="pi pi-star"
              text
              rounded
              size="small"
              :title="t('settings.defaultWallet')"
              @click="setAsDefault(wallet.id)"
            />
            <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(wallet)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="handleDelete(wallet)" />
          </div>
        </div>
        <p v-if="wallet.description" class="text-sm text-surface-500 mb-2">{{ wallet.description }}</p>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="wa in wallet.accounts"
            :key="wa.id_account"
            class="text-xs bg-surface-100 px-2 py-1 rounded"
          >
            {{ wa.account?.name || wa.account?.number || `#${wa.id_account}` }}
          </span>
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingWallet ? t('common.edit') : t('common.create')" modal class="w-full max-w-md">
      <div class="flex flex-col gap-4 pt-2">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Name</label>
          <InputText v-model="form.name" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Description</label>
          <InputText v-model="form.description" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('accounts.title') }}</label>
          <MultiSelect
            v-model="form.accountIds"
            :options="accountStore.accounts"
            optionLabel="name"
            optionValue="id"
            placeholder="Select accounts"
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDialog = false" />
        <Button :label="t('common.save')" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
