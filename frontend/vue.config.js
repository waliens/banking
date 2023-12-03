// vue.config.js
module.exports = {
    // options...
    devServer: {
        allowedHosts: ['http://' + process.env.VUE_APP_API],
    }
}