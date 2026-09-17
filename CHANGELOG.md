# Changelog - Ysgramor's Armor addon

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
