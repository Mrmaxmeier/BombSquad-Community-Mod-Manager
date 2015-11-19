'use strict'

const fs = require('fs')

const express = require('express')
const app = express()

app.use(express.static('.'))

var server = app.listen(3000, function () {
	var host = server.address().address
	var port = server.address().port

	console.log('Temporary file server listening at http://%s:%s', host, port)

	fetchAndRender()
})

const Browser = require('zombie')

const browser = new Browser()

browser.pipeline.addHandler((browser, request) => {
	if (request.url == 'https://raw.githubusercontent.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/master/index.json') {
		return new Promise(() => {})
	}
	return null
})

function fetchAndRender() {
	browser.visit('http://localhost:3000', function() {
		let prerendered = browser.document.querySelector('#container').innerHTML
		var src = browser.source
		src = src.replace('<!-- pre rendered elements -->', prerendered)
		console.log(src)
		fs.writeFile('prerendered.html', src, (err) => {
			if (err) {
				console.log(err)
				process.exit(1)
			}
			console.log('saved as \'prerendered.html\'')
			process.exit()
		})
	})
	browser.on('opened', function(window) {
		console.log('setting __PRERENDER')
		window.__PRERENDER = true
	})
}
