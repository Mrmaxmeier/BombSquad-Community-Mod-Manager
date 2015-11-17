function refresh() {
	let branch = data.branch
	var req = new XMLHttpRequest()
	req.onreadystatechange = function() {
		if (req.readyState == 4 && req.status == 200) {
			data.data = JSON.parse(req.responseText)
			data.fetchedBranch = branch
			if (data.cb)
				data.cb()
		}
	}
	req.open('get', 'https://raw.githubusercontent.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/' + branch + '/index.json')
	req.send()
}

function fetch() {
	if (data.fetchedBranch != data.branch)
		refresh()
}

var data = {
	fetch: fetch,
	refresh: refresh,
	setBranch: (branch) => {
		data.branch = branch
	},
	branch: 'master',
	fetchedBranch: null,
	data: null,
	cb: null
}
window.data = data

data.fetch()

module.exports = data
