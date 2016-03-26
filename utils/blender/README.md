
1. Download [this file](https://github.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/blob/master/utils/blender/bob_plugin.py).
2. Open Blender. (tested using version 2.76)
3. Go to File > User Preferences... > Addons tab.
4. On the bottom, click `Install from File...`
5. Select the `bob_plugin.py` from this project.
6. Enable the plugin by checking the checkbox.
7. Now you should now have new import/export menu items for .bob files.

To-Dos:
- [x] Import
	- [x] Mesh
	- [x] UV-Maps
		- [x] fix material loading
		- [ ] allow custom texture files?
	- [x] Normals
- [x] Export
	- [x] Mesh
	- [x] Normals
	- [x] UV-Maps
- [x] Cob
	- [x] Import
		- [ ] import normals?
	- [x] Export
- [ ] Import Level-Defs
