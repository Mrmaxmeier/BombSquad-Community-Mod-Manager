'use strict'

const React = require('react')

const Card = require('material-ui/lib/card/card')
const CardActions = require('material-ui/lib/card/card-actions')
const CardHeader = require('material-ui/lib/card/card-header')
const CardText = require('material-ui/lib/card/card-text')
const Avatar = require('material-ui/lib/avatar')
const FlatButton = require('material-ui/lib/flat-button')



class Mod extends React.Component {
	render() {
		return (
			<Card initiallyExpanded={false}>
				<CardHeader
					title={this.props.data.name}
					subtitle={'by ' + this.props.data.author}
					avatar={<Avatar style={{color:'red'}}>{this.props.data.name.charAt(0).toUpperCase()}</Avatar>}
					actAsExpander={true}
					showExpandableButton={true}>
				</CardHeader>
  <CardText expandable={true}>
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Donec mattis pretium massa. Aliquam erat volutpat. Nulla facilisi.
    Donec vulputate interdum sollicitudin. Nunc lacinia auctor quam sed pellentesque.
    Aliquam dui mauris, mattis quis lacus id, pellentesque lobortis odio.
  </CardText>
  <CardActions expandable={true}>
    <FlatButton label="Action1"/>
    <FlatButton label="Action2"/>
  </CardActions>
  <CardText expandable={true}>
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Donec mattis pretium massa. Aliquam erat volutpat. Nulla facilisi.
    Donec vulputate interdum sollicitudin. Nunc lacinia auctor quam sed pellentesque.
    Aliquam dui mauris, mattis quis lacus id, pellentesque lobortis odio.
  </CardText>
</Card>
		)
	}
}
module.exports = Mod
