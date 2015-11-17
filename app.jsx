'use strict'

const _ = require('underscore')
const React = require('react')
const Paper = require('material-ui/lib/paper')
const Tabs = require('material-ui/lib/tabs/tabs')
const Tab = require('material-ui/lib/tabs/tab')
const LinearProgress = require('material-ui/lib/linear-progress')

const Router = require('react-router').Router
const Route = require('react-router').Route
const Link = require('react-router').Link


const Mod = require('./mod')
const AppBar = require('./appbar')

var data = require('./data')

class ModList extends React.Component {
	render() {
		return (
			<div>
				{_.map(this.props.mods, (mod, name) => <Mod data={mod} key={name} />)}
			</div>
		)
	}
}

class MainView extends React.Component {
	constructor(props) {
		super(props)
		this.type = 'all'
		this.state = {
			data: data.data,
			branch: data.branch
		}
		data.cb = this.onData.bind(this)
	}

	onData() {
		this.setState({
			data: data.data,
			branch: data.branch
		})
	}

	filter(mods, type, filter) {
		switch (type) {
		case 'category':
			if (filter == 'all')
				return mods
			return _.filter(mods, (m) => m.category == filter)
		default:
			return mods
		}
	}

	getCategories() {
		var categories = new Set(['all'])
		_.each(data.data.mods, (mod) => {
			categories.add(mod.category)
		})
		return Array.from(categories)
	}

	renderTab(name) {
		let mods = this.filter(data.data.mods, this.type, this.props.params.splat)
		return (
			<Tab key={name} value={name} label={name.toUpperCase()}>
				<ModList mods={mods} />
			</Tab>
		)
	}

	handleTabChange(tab) {
		this.props.history.replace('/category/' + tab)
	}

	render() {
		let hasData = data.data != null
		let currentTab = (this.type == 'all') ? 'all' : this.props.params.splat
		return (
			<div>
				<AppBar refresh={data.refresh} />
				{hasData ? (
					<Paper>
						<Tabs valueLink={{value: currentTab, requestChange: this.handleTabChange.bind(this)}}>
							{_.map(this.getCategories(), this.renderTab.bind(this))}
						</Tabs>
					</Paper>
				) : (
					<LinearProgress mode='indeterminate' style={{height: '8px', backgroundColor: 'red'}} />
				)}
			</div>
		)
	}
}

class CategoryView extends MainView {
	constructor(props) {
		super(props)
		this.type = 'category'
	}
}

class FilterView extends MainView {
	constructor(props) {
		super(props)
		this.type = 'filter'
	}
}

class App extends React.Component {
	render() {
		return (
			<Router>
				<Route path='/' component={MainView} />
				<Route path='/category/*' component={CategoryView} />
				<Route path='/filter/*' component={FilterView} />
			</Router>
		)
	}
}
module.exports = App
