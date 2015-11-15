'use strict'

const _ = require('underscore')
const React = require('react')
const Paper = require('material-ui/lib/paper')
const Tabs = require('material-ui/lib/tabs/tabs')
const Tab = require('material-ui/lib/tabs/tab')

const Mod = require('./mod')



class App extends React.Component {
	renderTab(name) {
		let mods = _.filter(this.props.data.mods, (mod) => {
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
	render() {
		if (this.props.data == null)
			return <pre>Fetching Data..</pre>

		var categories = new Set(['all'])
		_.each(this.props.data.mods, (mod) => {
			categories.add(mod.category)
		})
		categories = Array.from(categories)
		return (
			<div>
				<Paper>
					<Tabs>
						{_.map(categories, this.renderTab.bind(this))}
					</Tabs>
				</Paper>
			</div>
		)
	}
}
module.exports = App
