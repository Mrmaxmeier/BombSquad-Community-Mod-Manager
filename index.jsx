'use strict'

const React = require('react')
const ReactDOM = require('react-dom')
const App = require('./app')
const injectTapEventPlugin = require('react-tap-event-plugin')
injectTapEventPlugin()

console.log('React.version: ' + React.version)

ReactDOM.render(
	<App />,
	document.getElementById('container')
)
