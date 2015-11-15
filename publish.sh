git checkout gh-pages
git reset --hard gh-pages-clean
webpack || exit
git add --force bundle.js
git commit -m "pushed bundle.js"
git push --force
git checkout gh-pages-clean
