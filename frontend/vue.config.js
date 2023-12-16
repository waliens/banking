// vue.config.js
module.exports = {
    // options...
    devServer: {
        allowedHosts: [process.env.BACKEND_BASE_URL],
    }
}