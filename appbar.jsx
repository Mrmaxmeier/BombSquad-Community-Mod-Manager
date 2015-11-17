'use strict'

const React = require('react')
const IconButton = require('material-ui/lib/icon-button')
const AppBar = require('material-ui/lib/app-bar')
const MenuItem = require('material-ui/lib/menus/menu-item')
const IconMenu = require('material-ui/lib/menus/icon-menu')
const MoreVertIcon = require('material-ui/lib/svg-icons/navigation/more-vert')

const GITHUB_URL = 'https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager'
const BOMBSQUAD_URL = 'http://www.froemling.net/apps/bombsquad'

class AppBarComponent extends React.Component {
	render() {
		return (
			<AppBar
				title="BombSquad Mod List Viewer"
				iconElementLeft={<IconButton href={GITHUB_URL}> TODO </IconButton>}
				iconElementRight={
					<IconMenu iconButtonElement={<IconButton><MoreVertIcon /></IconButton>}>
						<MenuItem onClick={this.props.refresh} primaryText="Refresh" />
						<MenuItem href={GITHUB_URL} primaryText="GitHub" />
						<MenuItem href={BOMBSQUAD_URL} primaryText="BombSquad" />
					</IconMenu>
				} />
		)
	}
}

module.exports = AppBarComponent
