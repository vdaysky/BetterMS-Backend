import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import { loadFonts } from './plugins/webfontloader'
import MsApi, { MsApi as MsApiType } from './api/api'
import Datepicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css'
import {ModelManager} from "@/api/model/modelBase";

declare global {
    interface Window {
        $api: MsApiType;
        $virtualTables: any[],
        $models: ModelManager;
        $socket: any;
        $Vue: any;
    }
}

loadFonts()

const reactiveModels = {
  install(Vue: any) {
    Vue.config.globalProperties.$api = MsApi;
    Vue.config.globalProperties.$models = store.state.$models;
    Vue.config.globalProperties.$socket = store.state.$socket;
    Vue.config.globalProperties.$Vue = Vue;

    window.$api = Vue.config.globalProperties.$api;
    window.$models = Vue.config.globalProperties.$models;
    window.$socket = Vue.config.globalProperties.$socket;
    window.$Vue = Vue;
  }
}

//@ts-ignore
Array.prototype.remove = function(callback: any) {
  let i = this.length;
  while (i--) {
      if (callback(this[i], i)) {
          this.splice(i, 1);
      }
  }
};
Date.prototype.toJSON = function () {
  const timezoneOffsetInHours = -(this.getTimezoneOffset() / 60); //UTC minus local time
  const sign = timezoneOffsetInHours >= 0 ? '+' : '-';
  const leadingZero = (Math.abs(timezoneOffsetInHours) < 10) ? '0' : '';

  //It's a bit unfortunate that we need to construct a new Date instance 
  //(we don't want _this_ Date instance to be modified)
  const correctedDate = new Date(this.getFullYear(), this.getMonth(), 
      this.getDate(), this.getHours(), this.getMinutes(), this.getSeconds(), 
      this.getMilliseconds());
  correctedDate.setHours(this.getHours() + timezoneOffsetInHours);
  const iso = correctedDate.toISOString().replace('Z', '');

  return iso + sign + leadingZero + Math.abs(timezoneOffsetInHours).toString() + ':00';
}


const app = createApp(App);

app.component('vDatepicker', Datepicker);


app.use(router)
  .use(store)
  .use(vuetify)
  .use(reactiveModels)
  .mount('#app')
