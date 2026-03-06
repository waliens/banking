<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Accordion from 'primevue/accordion'
import AccordionPanel from 'primevue/accordionpanel'
import AccordionHeader from 'primevue/accordionheader'
import AccordionContent from 'primevue/accordioncontent'

const { t } = useI18n()

const sections = [
  'transactions',
  'wallets',
  'categories',
  'tagging',
  'tagRules',
  'transactionGroups',
  'duplicates',
  'importProcess',
  'aiTagging',
]
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold mb-2">{{ t('help.title') }}</h1>
    <p class="text-surface-500 mb-6">{{ t('help.subtitle') }}</p>

    <Accordion multiple>
      <AccordionPanel
        v-for="section in sections"
        :key="section"
        :value="section"
      >
        <AccordionHeader>{{ t(`help.${section}.question`) }}</AccordionHeader>
        <AccordionContent>
          <div class="prose prose-sm max-w-none text-surface-700 whitespace-pre-line">{{ t(`help.${section}.answer`) }}</div>
        </AccordionContent>
      </AccordionPanel>
    </Accordion>
  </div>
</template>
