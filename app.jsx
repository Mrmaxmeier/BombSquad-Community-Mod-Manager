'use strict'

const _ = require('underscore')
const React = require('react')
const Paper = require('material-ui/lib/paper')
const Tabs = require('material-ui/lib/tabs/tabs')
const Tab = require('material-ui/lib/tabs/tab')
const LinearProgress = require('material-ui/lib/linear-progress')


const Mod = require('./mod')
const AppBar = require('./appbar')



function getData(branch, cb) {
	if (branch == undefined)
		branch = 'master'
	var req = new XMLHttpRequest()

	req.onreadystatechange = function() {
		if (req.readyState == 4 && req.status == 200) {
			let data = JSON.parse(req.responseText)
			cb(data)
		}
	}
	req.open('get', 'https://raw.githubusercontent.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/' + branch + '/index.json')
	req.send()
}


class App extends React.Component {
	constructor() {
		this.state = {
			data: null,
			branch: 'master'
		}
		getData(this.state.branch, this.onData.bind(this))
	}
	onData(d) {
		this.setState({
			data: d,
			branch: d.branch
		})
	}
	renderTab(name) {
		let mods = _.filter(this.state.data.mods, (mod) => {
			if (name == 'all')
				return true
			return mod.category == name
		})
		return (
			<Tab key={name} value={name} label={name.toUpperCase()}>
				{_.map(mods, (mod, name) => {
					return <Mod data={mod} key={name} />
				})}
			</Tab>
		)
	}
	refresh() {
		this.setState({
			data: null,
			branch: this.state.branch
		})
		getData(this.state.branch, this.onData.bind(this))
	}
	renderData() {
		var categories = new Set(['all'])
		_.each(this.state.data.mods, (mod) => {
			categories.add(mod.category)
		})
		categories = Array.from(categories)
		return (
			<Paper>
				<Tabs>
					{_.map(categories, this.renderTab.bind(this))}
				</Tabs>
			</Paper>
		)
	}
	render() {
		let hasData = this.state.data != null
		return (
			<div>
				<AppBar refresh={this.refresh.bind(this)} />
				{hasData ? this.renderData() : (
					<LinearProgress mode="indeterminate" style={{height: '8px', backgroundColor: 'red'}} />
				)}
			</div>
		)
	}
}
module.exports = App
