import os
import json
import hashlib
import git

mods = {}

for filepath in os.listdir("mods"):
	if filepath.endswith(".json"):
		base = filepath[:-5]
		mod = {"changelog": []}
		with open("mods/" + filepath, "r") as json_file:
			mod.update(json.load(json_file))
		with open("mods/" + base + ".py") as py_file:
			mod["md5"] = hashlib.md5(py_file.read().encode("utf-8")).hexdigest()
		mod["url"] = "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/master/mods/" + base + ".py"
		mod["filename"] = base + ".py"
		mods[base] = mod


gitRepo = git.Repo("./")

for commit in gitRepo.iter_commits(max_count=50, paths="mods/"):
	for filename in commit.stats.files:
		if filename.startswith("mods/"):
			filename = filename[5:]
			if filename.endswith(".py"):
				if not filename[:-3] in mods:
					continue
				txt = commit.message
				txt = txt.replace("\n", "")
				mods[filename[:-3]]["changelog"].append(txt)

for mod in mods.values():
	mod["changelog"] = mod["changelog"][:3]

with open("index.json", "w") as f:
	json.dump(mods, f, indent=4, sort_keys=True)
