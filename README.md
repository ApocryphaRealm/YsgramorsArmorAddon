Ysgramor's Armor addon
Version 1.0.0

WHAT THIS IS
    An addon for DeSepticOasis's "Ysgramor's Armor" (Nexus SE 130153) that gives the
    set crafting and tempering recipes, and puts it in Ysgramor's Tomb on Ysgramor
    himself instead of leaving it console-only.

    It is the mod's own plugin - YsgramorsArmor.esp - with the new records added to
    it, plus one small script. Install it after Ysgramor's Armor and let it overwrite
    the plugin. No second entry appears in your load order.

WHAT IT ADDS
    Crafting, at a forge, behind the Ebony Smithing perk - and only once you OWN that
    piece, so the forge copies what the tomb gave you rather than replacing the find:
        Helmet     3 ebony ingots, 2 leather strips
        Gauntlets  2 ebony ingots, 1 leather strip
        Cuirass    5 ebony ingots, 3 leather strips
        Boots      2 ebony ingots, 1 leather strip
        Cloak      3 leather, 2 leather strips, 1 ebony ingot

    Tempering, at an armour workbench, 1 ebony ingot each. As in vanilla, Arcane
    Blacksmith is only needed if the piece is enchanted - the recipes' conditions are
    copied byte-for-byte from Skyrim.esm's own ebony recipes.

    In Ysgramor's Tomb: once Glory of the Dead (the Companions questline) is complete,
    the sarcophagus lid and one bridge cage piece fade away and Ysgramor's body lies in
    the open sarcophagus with the set in its inventory. Until then the tomb is exactly
    as it was - sealed.

HOW THE TOMB OPENS
    The plugin does not edit the tomb. It carries no copy of the tomb's cell and
    changes none of the objects in it, so a mod that redesigns the tomb keeps its
    changes.

    Instead a small quest of this mod's own runs a script (YsgramorsArmorTombQuest)
    that checks every few seconds whether Glory of the Dead is complete. When it is:
      - Ysgramor's body, which waits switched off in a closed cell of this mod's own,
        is moved into the sarcophagus and switched on (once);
      - while you are inside the tomb, the sarcophagus lid and the bridge cage piece
        are switched off, with a fade. The game remembers this in your save, and the
        tomb never resets.

    If you finished the questline before installing this, the body is placed at once
    and the lid goes the next time you enter the tomb.

WHY EBONY-TIER
    The armour carries the vanilla keyword ArmorMaterialEbony, read out of the mod's own
    plugin - so its recipes follow vanilla ebony exactly rather than being invented.

REQUIREMENTS
    Ysgramor's Armor    https://www.nexusmods.com/skyrimspecialedition/mods/130153

COMPATIBILITY
    No cell, worldspace or placed object of the game is overridden, so mods that edit
    Ysgramor's Tomb (Northern Scenery's tomb edit, for example) do not conflict with
    it. The script looks the lid and the cage up by their vanilla IDs; if another mod
    has deleted or replaced them, there is simply nothing to switch off.

    The plugin also carries the original Ysgramor's Armor's own change to Sovngarde's
    Ysgramor (he wears the set), unchanged.

    Uninstalling: the body goes with the plugin. A lid and cage already switched off
    stay off in that save.

CREDITS
    DeSepticOasis   Ysgramor's Armor, and everything this plugin is built on.
