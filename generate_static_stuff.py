import os
import os.path
import json
import hashlib
import git

gitRepo = git.Repo("./")

mods = {}

current_commit = gitRepo.rev_parse("HEAD")

url_base = "https://cdn.rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/"
modurl = url_base + current_commit.hexsha + "/mods/"

tracked_mods = [key[0][5:-3] for key in gitRepo.index.entries if key[0].startswith("mods/") and key[0].endswith(".py")]

for filepath in os.listdir("mods"):
	if filepath.endswith(".py"):
		base = filepath[:-3]
		if not base in tracked_mods:
			continue
		mod = {"changelog": []}
		if os.path.isfile("mods/" + base + ".json"):
			with open("mods/" + base + ".json", "r") as json_file:
				mod.update(json.load(json_file))
		with open("mods/" + base + ".py") as py_file:
			mod["md5"] = hashlib.md5(py_file.read().encode("utf-8")).hexdigest()
		mod["url"] = modurl + base + ".py"
		mod["filename"] = base + ".py"
		mods[base] = mod

specific_sha = set()

for commit in gitRepo.iter_commits(max_count=1000, paths="mods/"):
	for filename in commit.stats.files:
		if filename.startswith("mods/"):
			filename = filename[5:]
			if filename.endswith(".py"):
				if not filename[:-3] in mods:
					continue
				txt = commit.message
				txt = txt.replace("\n", "")
				mods[filename[:-3]]["changelog"].append(txt)
				if not filename in specific_sha:
					mods[filename[:-3]]["url"] = url_base + commit.hexsha + "/mods/" + filename
					specific_sha.add(filename)

for mod in mods.values():
	mod["changelog"] = mod["changelog"][:2]

with open("index.json", "w") as f:
	json.dump(mods, f, indent=4, sort_keys=True)
