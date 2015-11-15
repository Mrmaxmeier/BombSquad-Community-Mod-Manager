'use strict'

const React = require('react')
const ReactDOM = require('react-dom')
const App = require('./app')
const injectTapEventPlugin = require('react-tap-event-plugin')
injectTapEventPlugin()

console.log('React.version: ' + React.version)

var data = null
window.data = data

function getData(branch, cb) {
	if (branch == undefined)
		branch = 'master'
	var req = new XMLHttpRequest()

	req.onreadystatechange = function() {
		if (req.readyState == 4 && req.status == 200) {
			data = JSON.parse(req.responseText)
			cb(data)
		}
	}
	req.open('get', 'https://raw.githubusercontent.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/' + branch + '/index.json')
	req.send()
}

getData('master', (resp) => {
	ReactDOM.render(
		<App data={resp} />,
		document.getElementById('container')
	)
})

ReactDOM.render(
	<App />,
	document.getElementById('container')
)
