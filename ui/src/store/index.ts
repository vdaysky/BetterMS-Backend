import {ModelManager, sessionId,} from '@/api/model/modelBase'
import { SocketConnection } from '@/api/utils'
import { AnonymousPlayer } from '@/api/model/models'
import { createStore } from 'vuex'

export default createStore({
  state: {
    $models: new ModelManager(),
    $socket: new SocketConnection(sessionId),
    player: new AnonymousPlayer(),
  },
  getters: {

  },
  mutations: {
    setPlayer(state, player) {
      if (player == null) {
        state.player = new AnonymousPlayer();
        return;
      }
      state.player = player;
    }
  },
  actions: {
  },
  modules: {
  }
})
