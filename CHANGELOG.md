# Changelog - Ysgramor's Armor addon

## 1.0.0

Never posted. Built 2026-09-10, reworked 2026-09-17 before its first upload.

* Forge recipes for all five pieces at ebony tier behind Ebony Smithing, each one only once you
  own that piece (GetItemCount >= 1 on the crafter, so the forge copies what the tomb gave you).
* Armour-table tempering for all five pieces, one ebony ingot each, Arcane Blacksmith only when
  the piece is enchanted - conditions copied byte-for-byte from Skyrim.esm's ebony recipes and
  verified against those bytes on every build.
* Ysgramor's body in his sarcophagus in Ysgramor's Tomb with the set in its inventory, posed by
  vanilla's own saved ragdoll data.
* The tomb opens only after Glory of the Dead: the sarcophagus lid, one bridge cage piece and the
  body are enable-parented to a marker of this mod's own, switched on by a small script
  (`YsgramorsArmorTombGate`) when the quest reports complete. The first design hung them off
  Kodlak's ghost reference; that reference is disabled again when his farewell ends, which would
  have resealed the tomb the moment the quest completed - found by decompiling the vanilla quest
  scripts, and replaced before release.
* Every record the generator authors is form version 44; a record cloned from a master keeps the
  master's own form version. An earlier build wrote 0 into every authored record and into the
  header, which MO2 reported as a pre-SE plugin.
* Ships as the mod's own plugin with the records added, so no second entry appears in the load
  order.
