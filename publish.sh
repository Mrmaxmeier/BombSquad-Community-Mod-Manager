git checkout gh-pages
git reset --hard gh-pages-clean
webpack -p || exit
node prerender.js || exit
mv prerendered.html index.html
git add --force index.html
git add --force bundle.js
git commit -m "pushed bundle.js"
git push --force
git checkout gh-pages-clean
