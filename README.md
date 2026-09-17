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
    the sarcophagus lid and one bridge cage piece disappear and Ysgramor's body lies in
    the open sarcophagus with the set in its inventory. Until then the tomb is exactly
    as vanilla left it - sealed.

HOW THE TOMB OPENS
    A marker of this mod's own, invisible and off by default, is the enable parent of
    the lid, the cage and the body. A script on it (YsgramorsArmorTombGate) checks
    whether Glory of the Dead is complete - once when the game first loads the mod,
    and then every few seconds only while you are inside the tomb - and switches the
    marker on when it is. The lid and cage follow it off, the body follows it on, and
    the game remembers. After it fires, nothing runs again.

    If you finished the questline before installing this, the tomb opens the next time
    you enter it.

WHY EBONY-TIER
    The armour carries the vanilla keyword ArmorMaterialEbony, read out of the mod's own
    plugin - so its recipes follow vanilla ebony exactly rather than being invented.

REQUIREMENTS
    Ysgramor's Armor    https://www.nexusmods.com/skyrimspecialedition/mods/130153

COMPATIBILITY
    Anything that edits Ysgramor's Tomb's cell may conflict over the two references this
    changes: the sarcophagus lid and one bridge cage piece. Nothing else in the tomb is
    touched, and no vanilla record is deleted. Because the switch is this mod's own
    marker, removing the plugin removes the marker and both references return to
    vanilla.

CREDITS
    DeSepticOasis   Ysgramor's Armor, and everything this plugin is built on.
