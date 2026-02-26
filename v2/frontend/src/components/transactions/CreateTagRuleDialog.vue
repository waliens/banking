<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import CategorySelect from '../common/CategorySelect.vue'
import AccountSelect from '../common/AccountSelect.vue'
import { useTagRuleStore } from '../../stores/tagRules'
import { useCategoryStore } from '../../stores/categories'

const { t } = useI18n()
const toast = useToast()
const tagRuleStore = useTagRuleStore()
const categoryStore = useCategoryStore()

const props = defineProps({
  visible: { type: Boolean, default: false },
  transaction: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'created'])

// Criteria toggles
const includeDescription = ref(true)
const includeAmount = ref(false)
const includeAccountFrom = ref(false)
const includeAccountTo = ref(false)

// Criteria values
const matchDescription = ref('')
const matchAmountMin = ref(null)
const matchAmountMax = ref(null)
const matchAccountFrom = ref(null)
const matchAccountTo = ref(null)

// Action
const categoryId = ref(null)
const ruleName = ref('')
const applyAfterCreate = ref(true)
const saving = ref(false)
const nameManuallyEdited = ref(false)

// Auto-generated name
const autoName = computed(() => {
  const descPart = includeDescription.value && matchDescription.value
    ? matchDescription.value.trim()
    : ''
  const cat = categoryId.value ? categoryStore.categoryMap.get(categoryId.value) : null
  const catName = cat ? cat.name : ''
  if (descPart && catName) return `${descPart} → ${catName}`
  if (descPart) return descPart
  if (catName) return catName
  return ''
})

watch(autoName, (val) => {
  if (!nameManuallyEdited.value) {
    ruleName.value = val
  }
})

function onNameInput() {
  nameManuallyEdited.value = true
}

const isRegexValid = computed(() => {
  if (!includeDescription.value || !matchDescription.value) return true
  try {
    new RegExp(matchDescription.value)
    return true
  } catch {
    return false
  }
})

const canSave = computed(() => {
  return categoryId.value != null &&
    isRegexValid.value &&
    (includeDescription.value || includeAmount.value || includeAccountFrom.value || includeAccountTo.value)
})

// Reset and pre-fill when dialog opens
watch(() => props.visible, (val) => {
  if (val && props.transaction) {
    const tx = props.transaction
    includeDescription.value = true
    includeAmount.value = false
    includeAccountFrom.value = false
    includeAccountTo.value = false

    matchDescription.value = tx.description || ''
    const amt = tx.amount != null ? Math.abs(Number(tx.amount)) : null
    matchAmountMin.value = amt
    matchAmountMax.value = amt
    matchAccountFrom.value = tx.id_source || null
    matchAccountTo.value = tx.id_dest || null

    categoryId.value = tx.id_category || null
    nameManuallyEdited.value = false
    ruleName.value = ''
    applyAfterCreate.value = true
    saving.value = false

    // Trigger autoName sync
    ruleName.value = autoName.value
  }
})

async function save() {
  if (!canSave.value || saving.value) return
  saving.value = true

  try {
    const payload = {
      name: ruleName.value || autoName.value,
      id_category: categoryId.value,
      match_description: includeDescription.value ? matchDescription.value.trim() : null,
      match_amount_min: includeAmount.value ? matchAmountMin.value : null,
      match_amount_max: includeAmount.value ? matchAmountMax.value : null,
      match_account_from: includeAccountFrom.value ? matchAccountFrom.value : null,
      match_account_to: includeAccountTo.value ? matchAccountTo.value : null,
      priority: 0,
      is_active: true,
    }

    const rule = await tagRuleStore.createRule(payload)

    let appliedCount = 0
    if (applyAfterCreate.value) {
      appliedCount = await tagRuleStore.applyRules()
    }

    toast.add({
      severity: 'success',
      summary: applyAfterCreate.value
        ? t('rules.ruleCreatedApplied', { count: appliedCount })
        : t('rules.ruleCreated'),
      life: 3000,
    })

    emit('created', { rule, appliedCount })
    emit('update:visible', false)
  } finally {
    saving.value = false
  }
}

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    :header="t('rules.createFromTransaction')"
    modal
    class="w-full max-w-md"
  >
    <div class="flex flex-col gap-4">
      <!-- Match criteria -->
      <div class="text-sm font-semibold text-surface-500">{{ t('rules.matchWhen') }}</div>

      <!-- Description -->
      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <Checkbox v-model="includeDescription" :binary="true" inputId="chk-desc" />
          <label for="chk-desc" class="text-sm">{{ t('rules.descriptionContains') }}</label>
        </div>
        <InputText
          v-model="matchDescription"
          :disabled="!includeDescription"
          :invalid="!isRegexValid"
          class="w-full"
          :class="{ 'opacity-50': !includeDescription }"
        />
      </div>

      <!-- Amount -->
      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <Checkbox v-model="includeAmount" :binary="true" inputId="chk-amount" />
          <label for="chk-amount" class="text-sm">{{ t('rules.amountBetween') }}</label>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <InputNumber
            v-model="matchAmountMin"
            :disabled="!includeAmount"
            mode="decimal"
            :minFractionDigits="2"
            class="w-full"
            :class="{ 'opacity-50': !includeAmount }"
          />
          <InputNumber
            v-model="matchAmountMax"
            :disabled="!includeAmount"
            mode="decimal"
            :minFractionDigits="2"
            class="w-full"
            :class="{ 'opacity-50': !includeAmount }"
          />
        </div>
      </div>

      <!-- From account -->
      <div v-if="transaction?.id_source" class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <Checkbox v-model="includeAccountFrom" :binary="true" inputId="chk-from" />
          <label for="chk-from" class="text-sm">{{ t('rules.fromAccount') }}</label>
        </div>
        <AccountSelect
          v-model="matchAccountFrom"
          :showClear="true"
          :disabled="!includeAccountFrom"
          class="w-full"
          :class="{ 'opacity-50': !includeAccountFrom }"
        />
      </div>

      <!-- To account -->
      <div v-if="transaction?.id_dest" class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <Checkbox v-model="includeAccountTo" :binary="true" inputId="chk-to" />
          <label for="chk-to" class="text-sm">{{ t('rules.toAccount') }}</label>
        </div>
        <AccountSelect
          v-model="matchAccountTo"
          :showClear="true"
          :disabled="!includeAccountTo"
          class="w-full"
          :class="{ 'opacity-50': !includeAccountTo }"
        />
      </div>

      <!-- Divider -->
      <hr class="border-surface-200" />

      <!-- Category -->
      <div>
        <label class="block text-sm font-semibold text-surface-500 mb-1">{{ t('rules.thenAssign') }}</label>
        <CategorySelect
          v-model="categoryId"
          :placeholder="t('categories.selectCategory')"
          :showClear="true"
          class="w-full"
        />
      </div>

      <!-- Rule name -->
      <div>
        <label class="block text-sm font-medium mb-1">{{ t('rules.ruleName') }}</label>
        <InputText v-model="ruleName" @input="onNameInput" class="w-full" />
      </div>

      <!-- Apply after create -->
      <div class="flex items-center gap-2">
        <Checkbox v-model="applyAfterCreate" :binary="true" inputId="chk-apply" />
        <label for="chk-apply" class="text-sm">{{ t('rules.applyAfterCreate') }}</label>
      </div>
    </div>

    <template #footer>
      <Button :label="t('common.cancel')" severity="secondary" text @click="close" />
      <Button
        :label="t('common.create')"
        icon="pi pi-check"
        :disabled="!canSave"
        :loading="saving"
        @click="save"
      />
    </template>
  </Dialog>
</template>
