<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Popover from 'primevue/popover'
import Button from 'primevue/button'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue'])

const popoverRef = ref(null)
const filterText = ref('')

// FontAwesome Free Solid icons (curated ~200 icons)
const FA_ICONS = [
  // Household & Home
  'fa-home', 'fa-door-open', 'fa-door-closed', 'fa-bed', 'fa-chair', 'fa-couch',
  'fa-table', 'fa-desk', 'fa-lamp', 'fa-lightbulb', 'fa-key', 'fa-lock', 'fa-unlock',
  'fa-window-maximize', 'fa-hammer', 'fa-wrench', 'fa-tools', 'fa-toolbox', 'fa-broom',
  'fa-dumpster', 'fa-trash', 'fa-trash-can', 'fa-recycle', 'fa-fan', 'fa-window-restore',
  // Food & Drink
  'fa-utensils', 'fa-spoon', 'fa-fork', 'fa-knife', 'fa-plate-wheat', 'fa-drumstick-bite',
  'fa-egg', 'fa-apple', 'fa-lemon', 'fa-burger', 'fa-pizza-slice', 'fa-cake-candles',
  'fa-carrot', 'fa-bread-slice', 'fa-bottle-water', 'fa-wine-bottle', 'fa-beer', 'fa-coffee',
  'fa-martini-glass', 'fa-champagne-glasses', 'fa-glass-water', 'fa-pot-food', 'fa-mug-hot',
  // Transport
  'fa-car', 'fa-car-side', 'fa-taxi', 'fa-truck', 'fa-bus', 'fa-train', 'fa-subway',
  'fa-bicycle', 'fa-motorcycle', 'fa-scooter', 'fa-skateboard', 'fa-wheelchair',
  'fa-helicopter', 'fa-plane', 'fa-rocket', 'fa-ship', 'fa-anchor', 'fa-sailboat',
  'fa-car-crash', 'fa-gas-pump', 'fa-oil-can', 'fa-charging-station', 'fa-traffic-light',
  // Health & Medicine
  'fa-heart', 'fa-heartbeat', 'fa-cross', 'fa-plus-minus', 'fa-dumbbell', 'fa-person-running',
  'fa-person-hiking', 'fa-person-biking', 'fa-person-swimming', 'fa-spa', 'fa-pill',
  'fa-bottle', 'fa-droplet', 'fa-syringe', 'fa-stethoscope', 'fa-hospital', 'fa-hospital-user',
  'fa-tooth', 'fa-teeth', 'fa-bandage', 'fa-person-cane', 'fa-crutch', 'fa-wheelchair',
  'fa-person-breastfeeding', 'fa-lung', 'fa-brain', 'fa-ear', 'fa-nose', 'fa-eye',
  // Finance & Money
  'fa-barcode', 'fa-credit-card', 'fa-dollar-sign', 'fa-euro-sign', 'fa-pound-sign',
  'fa-yen-sign', 'fa-rupee-sign', 'fa-receipt', 'fa-money-bill', 'fa-money-bill-wave',
  'fa-money-check', 'fa-cash-register', 'fa-wallet', 'fa-coins', 'fa-gem', 'fa-piggy-bank',
  'fa-calculator', 'fa-chart-bar', 'fa-chart-line', 'fa-chart-pie', 'fa-building-columns',
  'fa-handshake-dollar', 'fa-briefcase', 'fa-suitcase', 'fa-suitcase-rolling',
  // Entertainment & Games
  'fa-chess', 'fa-chess-pawn', 'fa-chess-knight', 'fa-chess-bishop', 'fa-chess-rook',
  'fa-chess-queen', 'fa-chess-king', 'fa-dice', 'fa-gamepad', 'fa-guitar', 'fa-drum',
  'fa-trumpet', 'fa-violin', 'fa-music', 'fa-film', 'fa-ticket', 'fa-tv', 'fa-camera',
  'fa-camera-retro', 'fa-video', 'fa-photo-film', 'fa-microphone', 'fa-headphones',
  'fa-speaker', 'fa-compact-disc', 'fa-play', 'fa-pause', 'fa-circle-pause', 'fa-stop',
  // Work & Business
  'fa-briefcase', 'fa-briefcase-medical', 'fa-building', 'fa-building-user', 'fa-handshake',
  'fa-handshake-angle', 'fa-file', 'fa-file-pdf', 'fa-file-word', 'fa-file-excel',
  'fa-folder', 'fa-folder-open', 'fa-envelope', 'fa-envelope-open', 'fa-pen', 'fa-pencil',
  'fa-pen-fancy', 'fa-paintbrush', 'fa-eraser', 'fa-palette', 'fa-ruler', 'fa-tape',
  'fa-paperclip', 'fa-link', 'fa-chain', 'fa-phone', 'fa-mobile', 'fa-laptop', 'fa-desktop',
  'fa-computer', 'fa-keyboard', 'fa-monitor', 'fa-printer', 'fa-scanner', 'fa-fax',
  'fa-copy', 'fa-scissors', 'fa-inbox', 'fa-archive', 'fa-trash', 'fa-magnifying-glass',
  // Clothing & Fashion
  'fa-shirt', 'fa-shoe-prints', 'fa-socks', 'fa-shoe', 'fa-boot', 'fa-hat-cowboy',
  'fa-hat-wizard', 'fa-crown', 'fa-glasses', 'fa-ring', 'fa-watch', 'fa-backpack',
  'fa-bag-personal', 'fa-handbag', 'fa-briefcase', 'fa-umbrella', 'fa-umbrella-beach',
  'fa-scarf', 'fa-gloves', 'fa-mitten', 'fa-vest', 'fa-vest-patches',
  // Nature & Plants
  'fa-tree', 'fa-leaf', 'fa-tree-city', 'fa-clover', 'fa-shamrock', 'fa-flower',
  'fa-rose', 'fa-sunflower', 'fa-tulip', 'fa-mushroom', 'fa-cactus', 'fa-lotus',
  'fa-seedling', 'fa-herb', 'fa-cannabis', 'fa-frog', 'fa-cat', 'fa-dog', 'fa-horse',
  'fa-horse-head', 'fa-mouse', 'fa-feather', 'fa-paw', 'fa-cow', 'fa-ox', 'fa-pig',
  'fa-sheep', 'fa-goat', 'fa-camel', 'fa-elephant', 'fa-rhino', 'fa-giraffe', 'fa-zebra',
  'fa-lion', 'fa-tiger', 'fa-leopard', 'fa-panda', 'fa-sloth', 'fa-otter', 'fa-skunk',
  'fa-kangaroo', 'fa-llama', 'fa-peacock', 'fa-swan', 'fa-dove', 'fa-eagle', 'fa-owl',
  'fa-parrot', 'fa-penguin', 'fa-flamingo', 'fa-fish', 'fa-shrimp', 'fa-squid', 'fa-octopus',
  'fa-crab', 'fa-lobster', 'fa-snail', 'fa-butterfly', 'fa-bee', 'fa-bug', 'fa-grasshopper',
  'fa-ant', 'fa-beetle', 'fa-spider', 'fa-turtle', 'fa-snake', 'fa-lizard', 'fa-dinosaur',
  'fa-t-rex', 'fa-dragon', 'fa-unicorn', 'fa-moon', 'fa-sun', 'fa-star', 'fa-cloud',
  'fa-cloud-rain', 'fa-cloud-snow', 'fa-wind', 'fa-water', 'fa-droplet', 'fa-droplets',
  'fa-snowflake', 'fa-snowman', 'fa-tornado', 'fa-fire', 'fa-flame', 'fa-bolt', 'fa-zap',
  // Tech & Science
  'fa-atom', 'fa-flask', 'fa-flask-vial', 'fa-microscope', 'fa-telescope', 'fa-satellite',
  'fa-satellite-dish', 'fa-rocket', 'fa-robot', 'fa-computer', 'fa-laptop', 'fa-desktop',
  'fa-tablet', 'fa-mobile', 'fa-mobile-screen', 'fa-keyboard', 'fa-mouse', 'fa-display',
  'fa-monitor', 'fa-screen', 'fa-gamepad', 'fa-headphones', 'fa-microphone', 'fa-speaker',
  'fa-wifi', 'fa-signal', 'fa-rss', 'fa-podcast', 'fa-wifi-slash', 'fa-battery-full',
  'fa-battery-half', 'fa-battery-empty', 'fa-plug', 'fa-power-off', 'fa-lightbulb',
  'fa-light', 'fa-flashlight', 'fa-candle', 'fa-magnifying-glass', 'fa-magnifying-glass-plus',
  'fa-magnifying-glass-minus', 'fa-code', 'fa-terminal', 'fa-user-secret',
  // People & Community
  'fa-user', 'fa-users', 'fa-user-plus', 'fa-user-minus', 'fa-user-check', 'fa-user-clock',
  'fa-user-doctor', 'fa-user-nurse', 'fa-user-secret', 'fa-user-tie', 'fa-user-shield',
  'fa-person', 'fa-person-walking', 'fa-person-running', 'fa-person-biking', 'fa-person-hiking',
  // Miscellaneous
  'fa-gift', 'fa-star', 'fa-star-fill', 'fa-heart-fill', 'fa-heart-crack', 'fa-thumbs-up',
  'fa-thumbs-down', 'fa-check', 'fa-xmark', 'fa-times', 'fa-plus', 'fa-minus', 'fa-slash',
  'fa-percent', 'fa-equals', 'fa-magnifying-glass', 'fa-flag', 'fa-flag-checkered',
  'fa-bookmark', 'fa-tag', 'fa-tags', 'fa-bell', 'fa-bell-slash', 'fa-clock', 'fa-hourglass',
  'fa-hourglass-end', 'fa-stopwatch', 'fa-timer', 'fa-calendar', 'fa-calendar-check',
  'fa-calendar-xmark', 'fa-graduation-cap', 'fa-medal', 'fa-trophy', 'fa-award', 'fa-map',
  'fa-location-dot', 'fa-compass', 'fa-mountain', 'fa-volcano', 'fa-island', 'fa-bridge',
  'fa-tunnel', 'fa-road', 'fa-railroad', 'fa-elevator', 'fa-stairs', 'fa-ramp-loading',
]

const filteredIcons = computed(() => {
  if (!filterText.value) return FA_ICONS
  const q = filterText.value.toLowerCase()
  return FA_ICONS.filter((icon) => icon.includes(q))
})

function selectIcon(icon) {
  emit('update:modelValue', `fas ${icon}`)
  popoverRef.value?.hide()
}

function clearIcon() {
  emit('update:modelValue', null)
  popoverRef.value?.hide()
}

function togglePopover(event) {
  popoverRef.value?.toggle(event)
}
</script>

<template>
  <div class="flex items-center gap-2">
    <Button
      type="button"
      outlined
      size="small"
      @click="togglePopover"
      class="min-w-[3rem] h-[2.5rem]"
    >
      <i v-if="modelValue" :class="modelValue" class="text-lg"></i>
      <span v-else class="text-surface-400 text-xs">{{ t('categories.icon') }}</span>
    </Button>
    <span v-if="modelValue" class="text-xs text-surface-500">{{ modelValue }}</span>

    <Popover ref="popoverRef">
      <div class="w-80">
        <InputText
          v-model="filterText"
          :placeholder="t('common.search')"
          class="w-full mb-2"
          size="small"
        />
        <div class="h-60 overflow-y-auto">
          <div class="grid grid-cols-8 gap-1">
            <button
              v-for="icon in filteredIcons"
              :key="icon"
              type="button"
              class="flex items-center justify-center w-8 h-8 rounded hover:bg-primary-50 transition-colors"
              :class="{ 'bg-primary-100 ring-2 ring-primary-500': modelValue === `fas ${icon}` }"
              :title="icon"
              @click="selectIcon(icon)"
            >
              <i :class="`fas ${icon}`" class="text-base"></i>
            </button>
          </div>
          <div v-if="filteredIcons.length === 0" class="text-center text-surface-400 py-4 text-sm">
            {{ t('common.noResults') }}
          </div>
        </div>
        <div v-if="modelValue" class="mt-2 pt-2 border-t border-surface-100">
          <Button :label="t('categories.clearIcon')" text size="small" severity="secondary" @click="clearIcon" />
        </div>
      </div>
    </Popover>
  </div>
</template>
