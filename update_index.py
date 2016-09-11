import os
import os.path
import json
import hashlib
import git

PROTOCOL_VERSION = 1.1

gitRepo = git.Repo("./")

mods = {}

current_commit = gitRepo.rev_parse("HEAD")

url_base = "https://cdn.rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/"
modurl = url_base + current_commit.hexsha + "/mods/"

old_data = None

for blob in gitRepo.head.object.tree.traverse():
    if blob.path.startswith("mods/") and blob.path.endswith(".py"):
        filename = blob.path[5:]
        base = filename[:-3]
        data = blob.data_stream.read()
        md5 = hashlib.md5(data).hexdigest()
        mod = {
            "changelog": [],
            "md5": md5,
            "url": modurl + filename,  # TODO: remove url field and bump version to 1.6
            "filename": filename,
            "commit_sha": current_commit.hexsha,
            "old_md5s": [],
        }
        if os.path.isfile("mods/" + base + ".json"):
            with open("mods/" + base + ".json", "r") as json_file:
                mod.update(json.load(json_file))
        if mod.get("index", True):
            mods[base] = mod
    elif blob.path == "index.json":
        old_data = json.loads(blob.data_stream.read().decode("UTF-8"))

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
                mod_slug = filename[:-3]
                mods[mod_slug]["changelog"].append(txt)
                if filename not in specific_sha:
                    # TODO: remove url field and bump version to 1.6
                    mods[mod_slug]["url"] = url_base + commit.hexsha + "/mods/" + filename
                    mods[mod_slug]["commit_sha"] = commit.hexsha
                    specific_sha.add(filename)
    for blob in commit.tree["mods"].blobs:
        if not blob.path.endswith(".py"):
            continue
        name = blob.path[5:-3]
        if name in mods:
            data = blob.data_stream.read()
            md5 = hashlib.md5(data).hexdigest()
            if md5 not in mods[name]["old_md5s"] and md5 != mods[name]["md5"] and len(mods[name]['old_md5s']) < 5:
                mods[name]["old_md5s"].append(md5)

for mod in mods:
    if not mod + ".py" in specific_sha:
        print("didnt find latest commit for", mod + ", head is used")

for mod in mods.values():
    mod["changelog"] = mod["changelog"][:2]
    # TODO: if the index.json gets too big
    # mod["old_md5s"] = [md5[:10] for md5 in mod["old_md5s"]]

index_data = {"mods": mods, "version": PROTOCOL_VERSION}
with open("index.json", "w") as f:
    json.dump(index_data, f, indent=4, sort_keys=True)

if old_data:
    old_mods = old_data["mods"]
    text = ""

    def add(text, mod, spacer, *args):
        if spacer:
            text += " " * (spacer + 2)
        else:
            text += mod + ": "
            spacer = len(mod)
        text += " ".join(args) + "\n"
        return text, spacer
    spacer = None
    for mod in set(list(old_mods.keys()) + list(mods.keys())):
        if spacer:
            spacer = None
            text += "\n"
        if mod in mods and mod in old_mods:
            md, omd = mods[mod], old_mods[mod]
            for key in set(list(md.keys()) + list(omd.keys())):
                if key in md and key in omd:
                    if md[key] != omd[key]:
                        text, spacer = add(text, mod, spacer, 'updated', key)
                elif key not in md:
                    text, spacer = add(text, mod, spacer, 'removed', key)
                else:
                    text, spacer = add(text, mod, spacer, 'added', key)
        elif mod in mods:
            text, spacer = add(text, mod, spacer, 'added')
        else:
            text, spacer = add(text, mod, spacer, 'removed')

    if len(text) == 0:
        print("no changes.")
    else:
        text = "update index.json\n\n" + text
        print(text)
        if input("Do commit? [Yn]") in ["", "Y", "y"]:
            print("staging index.json")
            gitRepo.index.add(["index.json"])
            print("committing")
            gitRepo.index.commit(text)
        else:
            print("didnt commit changes.")
