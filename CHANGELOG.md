# Changelog - Ysgramor's Armor addon

## 1.0.2 - 2026-10-25 - untested

### Fixed
- The compiled scripts' headers no longer carry the build machine's account and computer name (the Papyrus compiler writes both into every .pex; they are now blanked after compiling). No gameplay change from this item - 1.0.2 also carries the tomb changes listed below, which are what this release changes in game.
- The plugin no longer edits Ysgramor's Tomb. 1.0.1 placed the body in the tomb and overrode the sarcophagus lid and a bridge cage piece there, which forced it to carry the tomb's cell record - so any mod that edits the tomb (Northern Scenery's tomb edit, for one) conflicted with it, and 1.0.1's copy of that record held only its editor ID, so whichever loaded last could strip the tomb's lighting, location, music and acoustics. Now the plugin overrides no cell, worldspace or placed reference of the game; the build refuses to write one that does.
- The tomb opens at run time instead: a start-game-enabled quest of the mod's own (AR_YsgramorTombQuest, script YsgramorsArmorTombQuest) checks every few seconds whether Glory of the Dead is complete (stage 200 or the completed flag). When it is, Ysgramor's body - now kept disabled in a holding cell of the mod's own - is moved into the sarcophagus once and enabled, and while the player is in the tomb the lid and the cage are disabled with a fade. Saves that finished the questline earlier open the same way.
- The quest's check is re-armed on every game load. In testing, an autosave written a few seconds after New Game (Alternate Perspective's start-cell save) held the quest running with no check pending - the script armed it only once, when the quest first initialised - so on that save finishing Glory of the Dead opened nothing. The quest now has a player alias (alias 0, forced to the player) whose script, YsgramorsArmorTombPlayer, re-arms the check whenever a save is loaded; arming is idempotent (a new arm replaces the pending one), so a running check never doubles.
- 1.0.1's gate marker (0x81B) and its script YsgramorsArmorTombGate are retired; the id is not reused. Every other form id is unchanged.
- The plugin header's record count now counts groups as well as records, as the original plugin's does.

## 1.0.1

Built 2026-09-17, before the mod's first upload; 1.0.0 was never posted.

* The tomb opens only after Glory of the Dead. The sarcophagus lid, one bridge cage piece and
  Ysgramor's body are enable-parented to a marker of this mod's own, switched on by a small script
  (`YsgramorsArmorTombGate`) when the quest reports complete - checked once at first load and then
  every few seconds only while the player is in the tomb. 1.0.0 shipped the lid and cage disabled
  outright, so the tomb stood open on a character that had never touched the questline. The first
  gate design hung everything off Kodlak's ghost reference; that reference is disabled again when
  his farewell ends, which would have resealed the tomb the moment the quest completed - found by
  decompiling the vanilla quest scripts, and replaced before release.
* Forge recipes now also require owning that piece (GetItemCount >= 1 on the crafter), so the forge
  copies what the tomb gave you rather than replacing the find.
* Every record the generator authors is form version 44; a record cloned from a master keeps the
  master's own form version. 1.0.0 wrote 0 into every authored record and into the header, which
  MO2 reported as a pre-SE plugin.
* The generator, the script and the build now live in this repository; Skyrim.esm and the Papyrus
  compiler are discovered rather than hard-coded.

## 1.0.0

* Forge recipes for all five pieces at ebony tier behind Ebony Smithing.
* Armour-table tempering for all five pieces, one ebony ingot each, Arcane Blacksmith only when
  the piece is enchanted - conditions copied byte-for-byte from Skyrim.esm's ebony recipes and
  verified against those bytes on every build.
* Ysgramor's body in his sarcophagus in Ysgramor's Tomb with the set in its inventory, posed by
  vanilla's own saved ragdoll data.
* The sarcophagus lid and one bridge cage piece disabled so the body can be reached.
* Ships as the mod's own plugin with the records added, so no second entry appears in the load
  order.
