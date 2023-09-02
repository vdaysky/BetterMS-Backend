<template>
  <div>
    <router-link :to="{name: 'match', params: {id: match.id} }"> {{ match._name }} </router-link>
  </div>
</template>

<script>

export default {
    props: ['match']
}
</script>

<style>

</style>