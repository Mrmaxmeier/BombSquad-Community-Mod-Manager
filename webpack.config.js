module.exports = {
	entry: './index.jsx',
	output: {
		filename: 'bundle.js'
	},
	module: {
		loaders: [
			{
				test: /\.jsx$/,
				exclude: /(node_modules)/,
				loader: 'babel',
				query: {
					presets: [
						'react',
						'es2015'
					]
				}
			}
		]
	},
	externals: {},
	resolve: {
		extensions: ['', '.js', '.jsx', '.css']
	}
}
