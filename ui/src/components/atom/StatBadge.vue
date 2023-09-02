<template>
  <v-sheet class="badge text-center w-25">
    <div class="d-flex flex-column justify-space-between py-4" style="height: 100%">
        <h2 class="mb-2">
          <slot name="value"></slot>
        </h2>
        <div style="height: 100%;" class="text-center">
            <p class="text-center">
              <slot name="metric"></slot>
            </p>
        </div>
    </div>
    
  </v-sheet>
</template>

<script>
export default {
};
</script>

<style scoped>
.badge {
    background: #f4f4f4;
    padding: .5rem .5rem;
    border-radius: 5px;
}
h5 {
    font-weight: 400;
}
</style>