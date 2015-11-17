'use strict'

const React = require('react')

const Card = require('material-ui/lib/card/card')
const CardActions = require('material-ui/lib/card/card-actions')
const CardHeader = require('material-ui/lib/card/card-header')
const CardText = require('material-ui/lib/card/card-text')
const Avatar = require('material-ui/lib/avatar')
const FlatButton = require('material-ui/lib/flat-button')
const Slider = require('material-ui/lib/slider')

const PropTypes = require('react-router').PropTypes

class Mod extends React.Component {
	render() {
		return (
			<Card initiallyExpanded={this.props.expanded}>
				<CardHeader
					title={this.props.data.name}
					subtitle={'by ' + this.props.data.author}
					avatar={<Avatar style={{color:'red'}}>{this.props.data.name.charAt(0).toUpperCase()}</Avatar>}
					actAsExpander={true}
					showExpandableButton={true}>
				</CardHeader>
				{this.props.data.playability != null ? (
					<CardText expandable={true}>
						Playability:
						<Slider name="playability" disabled={true} value={this.props.data.playability} />
					</CardText>
				) : null}
				{this.props.data.requires != null ? (
					<CardText expandable={true}>
						Requires:
						<ul>
						{this.props.data.requires.map((e) => {
							return <li key={e}>{e}</li>
						})}
						</ul>
					</CardText>
				) : null}
				<CardText expandable={true}>
					Changelog:
					<ul>
					{this.props.data.changelog.map((e) => {
						return <li key={e}>{e}</li>
					})}
					</ul>
				</CardText>
				<CardActions expandable={true}>
					<FlatButton linkButton={true} onClick={() => {
						this.context.history.push('/mod/' + this.props.data.key)
					}} label="Permlink"/>
					<FlatButton linkButton={true} href={'https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/blob/master/mods/' + this.props.data.filename} label="View Source"/>
					<FlatButton linkButton={true} href={this.props.data.url} label="Download"/>
				</CardActions>
				<CardText expandable={true}></CardText>
			</Card>
		)
	}
}

Mod.contextTypes = { history: PropTypes.history }

module.exports = Mod
