module.exports = {
	entry: './index.jsx',
	output: {
		filename: 'bundle.js'
	},
	module: {
		loaders: [
			{
				test: /\.jsx$/,
				loader: 'babel-loader'
			}
		]
	},
	externals: {},
	resolve: {
		extensions: ['', '.js', '.jsx', '.css']
	}
}
