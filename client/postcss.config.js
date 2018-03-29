module.exports = {
  plugins: [
    require('postcss-import')({ path: [__dirname, '__dirname/node_modules'] }),
  ]
}
