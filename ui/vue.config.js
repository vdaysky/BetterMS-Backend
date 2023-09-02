const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,

  pluginOptions: {
    vuetify: {
			// https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vuetify-loader
		}
  },
  chainWebpack: config => {
    config.optimization
        .minimizer('terser')
        .tap(args => {
          const { terserOptions } = args[0]
          terserOptions.keep_classnames = true
          terserOptions.keep_fnames = true
          return args
        })
  },
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        },
        logLevel: 'debug',
      },
      '^/subscribe': {
        target: 'http://localhost:8000/subscribe',
        ws: true,
        pathRewrite: {
          '^/subscribe': '/subscribe'
        },
        changeOrigin: true,
        logLevel: 'debug'
    }
    }
  }
})
