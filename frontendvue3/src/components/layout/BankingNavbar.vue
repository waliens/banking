

<template>
  <div class="card">
    <menu-bar :model="items">
      <template #start>
        {{ $t('app-name') }}
      </template>
      <template #end>
        <i class="pi pi-check"></i>
      </template>
    </menu-bar>
  </div>
</template>


<script setup>
import MenuBar from 'primevue/menubar';
const items = [
  {
    label: 'Home',
    icon: 'pi pi-fw pi-home',
    to: '/',
  },
  {
    label: 'About',
    icon: 'pi pi-fw pi-info',
    to: '/about',
  },
  {
    label: 'Contact',
    icon: 'pi pi-fw pi-envelope',
    to: '/contact',
  },
];
</script>