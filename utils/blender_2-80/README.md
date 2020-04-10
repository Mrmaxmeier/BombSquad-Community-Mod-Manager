
1. Download [this file](https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/blob/master/utils/blender/bob_plugin.py).
2. Open Blender. (tested using version 2.82)
3. Go to Edit > Preferences... > Add-ons tab.
4. On the bottom, click `Install...`
5. Select the `bob_plugin.py` from this project.
6. Enable the plugin by checking the checkbox.
7. Now you should now have new import/export menu items for .bob files.

To-Dos:
- [x] Import
	- [x] Mesh
	- [x] UV-Maps
		- [ ] fix material loading
		- [ ] allow specifying texture files
	- [ ] import normals?
- [x] Export
	- [x] Mesh
	- [x] Normals
	- [x] UV-Maps
- [x] Cob
	- [x] Import
		- [ ] import normals?
	- [x] Export
- [x] Import Level-Defs
- [x] Export Level-Defs

---

To use the ```character_workflow.py``` plugin make sure you have the ```bob_plugin.py``` plugin enabled.

![preview](images/preview.gif)



###Attribution

The bob_plugin addon is the creation of [Mrmaxmeier](https://github.com/Mrmaxmeier) and the [community](https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager). I just ported it to work with blender 2.80+. 

The new workflow addon is loosely based on [Godot Game Tools for Blender](https://github.com/vini-guerrero/Godot_Game_Tools/). with the permission of the original authors.
