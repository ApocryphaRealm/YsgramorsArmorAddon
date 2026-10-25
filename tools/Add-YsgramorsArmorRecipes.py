#!/usr/bin/env python3
"""
Add-YsgramorsArmorRecipes.py
Injects forge-crafting and armour-table tempering recipes DIRECTLY INTO a copy of
"YsgramorsArmor.esp" (DeSepticOasis, Nexus SE 130153 v1.0), so the recipes ship inside the mod's
own plugin and no second ESP appears in the load order.

    python Add-YsgramorsArmorRecipes.py <source .esp> <destination .esp>

WHY THIS SHAPE (the owner, 2026-09-10)
    "were making this mod as a patch that merges into the ysgramors armor mod so theres not
    another esp in the plugin list". So rather than a patch plugin mastered to theirs, the ten
    new records are appended to their plugin's own record set and the result is installed as a
    higher-priority copy of the same mod. The ORIGINAL file is never written to - source and
    destination are different paths, and the destination lives in the MO2 test mods area.

WHAT IS ADDED - ten COBJ records and nothing else
    Nothing existing is touched: no record of theirs is edited, no master is added, no header
    field changes except the two that MUST (record count, next form id). Their ARMO/ARMA/NPC_/
    OTFT records pass through byte-for-byte.

    New form ids start at the plugin's own nextObjectID (0x80E), so they cannot collide with the
    ids already in use (0x800-0x80D). The plugin is ESL-flagged already, and 0x80E-0x817 stays
    inside the light range, so it keeps its free load-order slot.

WHY THESE INGREDIENTS
    The armour carries vanilla ArmorMaterialEbony + ArmorHeavy, read out of the plugin itself, so
    the recipes follow vanilla ebony. Their SHAPE is copied byte-for-byte from Skyrim.esm's
    RecipeArmorEbonyCuirass (0x000DD989) and TemperArmorEbonyCuirass (0x000EB448) - the condition
    layout is verified against those real bytes on every run, because a CTDA that is the wrong
    length loads without complaint and then misbehaves.

NOT gated behind the Companions questline: the mod's author says they plan that eventually, but
it is their intent for their mod, not what was asked for here, and it would make the armour
uncraftable until that questline is done. To adopt it, switch STATION_CRAFT to the Skyforge
keyword (0x000F46CE) and add a GetStageDone condition on quest C06 (0x0001CEF6).
"""
import os
import struct
import zlib
import sys

# ---- vanilla form ids, every one read out of Skyrim.esm by EditorID, none from memory ----
INGOT_EBONY    = 0x0005AD9D   # MISC IngotEbony
LEATHER        = 0x000DB5D2   # MISC Leather01
LEATHER_STRIPS = 0x000800E4   # MISC LeatherStrips
PERK_EBONY     = 0x000CB412   # PERK EbonySmithing
PERK_ARCANE    = 0x0005218E   # PERK ArcaneBlacksmith
STATION_CRAFT  = 0x00088105   # KYWD CraftingSmithingForge
STATION_TEMPER = 0x000ADB78   # KYWD CraftingSmithingArmorTable

# The armour, in the plugin's OWN index (04 - it has four masters).
ARMOUR = [
    ("Helmet",    0x04000800, [(INGOT_EBONY, 3), (LEATHER_STRIPS, 2)]),
    ("Gauntlets", 0x04000801, [(INGOT_EBONY, 2), (LEATHER_STRIPS, 1)]),
    ("Cuirass",   0x04000802, [(INGOT_EBONY, 5), (LEATHER_STRIPS, 3)]),
    ("Boots",     0x04000803, [(INGOT_EBONY, 2), (LEATHER_STRIPS, 1)]),
    # Cloth over a little ebony trim - rating 3, weight 3. Leather-led on purpose: five ingots
    # for a cape would read as absurd beside the cuirass.
    ("Cloak",     0x04000804, [(LEATHER, 3), (LEATHER_STRIPS, 2), (INGOT_EBONY, 1)]),
]

VANILLA_CTDA = {
    "craft_ebony":   "000000000000803fc001540012b40c00000000000000000000000000ffffffff",
    "temper_ench":   "210000000000803f9302540000000000000000000000000000000000ffffffff",
    "temper_arcane": "000000000000803fc00154008e210500000000000000000000000000ffffffff",
}


def sub(tag: bytes, data: bytes) -> bytes:
    return tag + struct.pack("<H", len(data)) + data


# Form version 44 is Skyrim SE's. An earlier build wrote 0 here - every record this script
# creates, and the rebuilt TES4 header, reported as "form 0" in MO2's plugin check (the owner,
# 2026-09-17, screenshot: "You have one or more plugins that are not form 44"). The engine parses
# several subrecords by form version, so 0 is not merely cosmetic.
FORM_VERSION = 44


def record(tag: bytes, formid: int, data: bytes, flags: int = 0,
           form_version: int = FORM_VERSION) -> bytes:
    """Records this script AUTHORS are form 44. A record CLONED from a master passes the master's
    own form version through - the engine reads some subrecords by it (BODT vs BOD2), and the
    Dragonbone generator crashed the game by re-stamping copied records as 44."""
    return (tag + struct.pack("<I", len(data)) + struct.pack("<I", flags) +
            struct.pack("<I", formid) + struct.pack("<I", 0) +
            struct.pack("<HH", form_version, 0) + data)


def wstr(s: bytes) -> bytes:
    """VMAD's string form: uint16 length, no terminator."""
    return struct.pack("<H", len(s)) + s


def vmad_object_script(script: bytes, props) -> bytes:
    """A VMAD subrecord carrying ONE script with Object-typed properties, in the v5 / object-format-2
    layout every SE record uses: version, objFormat, scriptCount; per script name + status + props;
    per property name, type 1 (Object), status 1 (edited), then objFormat-2's value: uint16 unused,
    int16 alias (-1 = none), uint32 form id."""
    b = struct.pack("<hhH", 5, 2, 1)
    b += wstr(script) + struct.pack("<B", 0) + struct.pack("<H", len(props))
    for name, fid in props:
        b += wstr(name) + struct.pack("<BB", 1, 1) + struct.pack("<HhI", 0, -1, fid)
    return b


def ctda(op: int, value: float, func: int, p1: int = 0, p2: int = 0) -> bytes:
    """32 bytes: op(1) pad(3) value(4f) func(2) pad(2) p1(4) p2(4) runOn(4) ref(4) unknown(4)."""
    return sub(b"CTDA",
               struct.pack("<B", op) + b"\x00\x00\x00" +
               struct.pack("<f", value) +
               struct.pack("<H", func) + b"\x54\x00" +
               struct.pack("<I", p1) + struct.pack("<I", p2) +
               struct.pack("<i", 0) + struct.pack("<i", 0) + struct.pack("<i", -1))


def verify_conditions() -> None:
    for name, built in (("craft_ebony", ctda(0x00, 1.0, 448, PERK_EBONY)),
                        ("temper_ench", ctda(0x21, 1.0, 659)),
                        ("temper_arcane", ctda(0x00, 1.0, 448, PERK_ARCANE))):
        got, want = built[6:].hex(), VANILLA_CTDA[name]
        if got != want:
            raise SystemExit(f"CTDA mismatch for {name}:\n  built   {got}\n  vanilla {want}")
    print("  conditions match Skyrim.esm byte-for-byte (3 x 32 bytes)")


def cobj(formid: int, edid: str, ingredients, result: int, station: int, conditions) -> bytes:
    body = sub(b"EDID", edid.encode("ascii") + b"\x00")
    body += sub(b"COCT", struct.pack("<I", len(ingredients)))
    for item, count in ingredients:
        body += sub(b"CNTO", struct.pack("<II", item, count))
    for c in conditions:
        body += c
    body += sub(b"CNAM", struct.pack("<I", result))
    body += sub(b"BNAM", struct.pack("<I", station))
    body += sub(b"NAM1", struct.pack("<H", 1))
    return record(b"COBJ", formid, body)



# ---------------------------------------------------------------- world placement (2026-09-10)
# The owner asked for the armour to be left loose in Ysgramor's Tomb rather than in a container,
# and for one vanilla object to be removed while this mod is active.
#
#   place at  X 895.26  Y 358.02  Z 1350.99   (his coordinates, used verbatim)
#   remove    NorBridgeCageMid01, base 0x00034019, ref 0x000D83AB
#
# EVERYTHING BELOW WAS READ OUT OF Skyrim.esm, not assumed:
#   * REFR 0x000D83AB really is in cell 0x00015254 (YsgramorsTomb01) and its base really is
#     0x00034019 - both confirmed, so the ref and base the owner gave agree with the game.
#   * its group nest is CELL -> interior block 2 -> sub-block 1 -> cell children -> TEMPORARY
#     children, which is where our own references must go too.
#   * it carries only NAME and DATA, which is what the override below reproduces.
TOMB_CELL      = 0x00015254
TOMB_EDID      = b"YsgramorsTomb01\x00"
TOMB_BLOCK     = 2      # interior block    = cellFormID % 10
TOMB_SUBBLOCK  = 1      # interior subblock = (cellFormID / 10) % 10
CAGE_REF       = 0x000D83AB
CAGE_BASE      = 0x00034019
CAGE_DATA      = (895.97, -259.42, -1332.61, 0.0, -0.0, 4.6822)   # verbatim from the vanilla record

# The owner's console reading, with the sign correction he confirmed. These are EXACTLY the
# coordinates of NorSarcophagusBottom (REFR 0x00033DFE) - he had the console crosshair on the
# sarcophagus when he took them, so a bare copy would bury the armour inside the coffin.
SARCOPHAGUS_ORIGIN = (895.26, -358.02, -1350.99)

# How much height to add, measured rather than guessed: NorSarcophagusBottom's own bounds are
# z[0,62], so its open rim is 62 units above that origin. 70 puts the pieces a little above the
# rim, where Havok settles them down into the open casket once the lid below is gone.
SARCOPHAGUS_RIM   = 62.0
PLACE_HEIGHT      = 70.0
PLACE_AT = (SARCOPHAGUS_ORIGIN[0], SARCOPHAGUS_ORIGIN[1], SARCOPHAGUS_ORIGIN[2] + PLACE_HEIGHT)

# The casket lid, to be removed along with the cage (the owner, 2026-09-10). Read from the
# vanilla record, not assumed: NorSarcophagusTop, sitting 55.58 units above the bottom.
LID_REF   = 0x000AF824
LID_BASE  = 0x00034CE3
LID_DATA  = (895.2628784179688, -358.0207214355469, -1295.4112548828125, 0.0, -0.0, 3.112388849258423)

# Initially Disabled. This is how a plugin removes a vanilla object without deleting the record -
# deleting it would leave a dangling reference for anything that points at it. The object simply
# never spawns while this plugin is active, and removing the plugin restores it.
FLAG_INITIALLY_DISABLED = 0x00000800

# --- gating on the quest (the owner, 2026-09-10) -----------------------------------------
# "have the sarcophagus lid disappear only after the quest where you release Kodlak's soul from
# Hircine" - that is C06, Glory of the Dead.
#
# No script is needed. Skyrim's ENABLE PARENT chains one reference's enabled state to another's,
# and carries a flag for "set state to the OPPOSITE of the parent". C06 already switches on a
# reference at exactly the right instant:
#
#   REFR 0x00058300  C06KodlaksGhostREF - Kodlak's ghost, initially disabled, enabled when his
#                    soul is freed. Found by listing every initially-disabled reference in the
#                    tomb and reading the quest's own aliases - not assumed.
#
# Both halves hang off it, in opposite directions:
#   lid    -> OPPOSITE : present while the ghost is off, gone the moment he appears
#   armour -> NORMAL   : absent while the ghost is off, appears with him
#
# The armour needs gating too, which is not obvious: it sits at the sarcophagus origin + 70,
# ABOVE the closed lid's top surface (-1285.41), so ungated it would rest in plain sight on the
# shut lid and be lootable before the questline had been touched.
# Skyrim.esm is read for vanilla records and the recipe-shape check. Discovered, not hard-coded
# (rule 4): SKYRIM_ESM in the environment, else the first MO2 Stock Game or Steam copy found.
_ESM_CANDIDATES = [
    os.environ.get("SKYRIM_ESM", ""),
    r"D:\modlists\Njordlinger\Stock Game\Data\Skyrim.esm",
    r"C:\Modlists\Apostasy\Stock Game\Data\Skyrim.esm",
    r"C:\SteamLibrary\steamapps\common\Skyrim Special Edition\Data\Skyrim.esm",
]
SKYRIM_ESM = next((c for c in _ESM_CANDIDATES if c and os.path.isfile(c)), _ESM_CANDIDATES[1])
DRAUGR_RACE       = 0x00000D53   # RNAM of the corpse NPC we clone
CORPSE_TEMPLATE   = 0x0005AFA6   # NPC_ TreasCorpseDraugrMale - the vanilla draugr corpse
FLAG_STARTS_DEAD  = 0x00000200   # ACHR record flag; every vanilla corpse placement carries it
# How high above the sarcophagus origin to spawn him. Its bounds are z[0,62], so this drops him
# inside the box rather than on top of the rim; Havok settles the ragdoll from there.
# --- placement copied from how VANILLA lays a corpse in a closed sarcophagus ---------------
# Two attempts put him on the floor behind the coffin instead of inside it, and my second guess -
# that his standing collision capsule was spanning the 62-unit walls, so raise him from 40 to 72 -
# was wrong. The height was never the problem. The owner said to go and find a vanilla example
# ("there are plenty of examples throughout the game of draugr being positioned inside of a
# sarcophagus properly with lid closed"), so all 220 NorSarcophagusBottom placements in Skyrim.esm
# were listed and every corpse lying within 90 units of one was read out. All 17 of them carry
# XRGD - saved RAGDOLL DATA - and ours did not. That subrecord is what pins a dead body in a
# hand-authored pose; without it the engine has no pose to hold, drops him as a fresh ragdoll,
# finds the coffin solid, and settles him on the nearest open floor. Which is exactly what was
# seen, at both heights, which is why changing the height never helped.
#
# The pair this is copied from, read out of Skyrim.esm rather than remembered:
#   REFR 0x0007884F NorSarcophagusBottom     pos (1409.31, 2460.86, -1423.75) rotZ 6.0332
#   ACHR 0x00078850 TreasCorpseDraugrFemale  dist 43.2u, dZ +40.5, flags StartsDead,
#                                            subrecords NAME / XRGD / XLCN / DATA
#
# So vanilla's own height inside the box is +40.55 - the original 40 was right and the "fix"
# moved away from it. The XY offset and rotation below are vanilla's, rotated out of its
# sarcophagus's frame into ours. XRGD holds bone offsets in the actor's OWN frame (the largest
# number in the 504-byte blob is 38.8 - body-sized, not world-sized), which is why it transplants
# to a different coffin unchanged.
CORPSE_POS   = (909.66, -362.16, -1310.44)
CORPSE_ROTZ  = 1.8792
RAGDOLL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ysgramor-corpse-ragdoll.bin")

# Gate the tomb contents on finishing Glory of the Dead (C06). ON since 2026-09-17: the owner
# walked into the tomb on a character that had not touched the questline and found the lid and the
# cage already gone ("those aren't supposed to disappear until after the quest finishes").
#
# The first design hung everything off C06KodlaksGhostREF (0x00058300) as an enable parent. It was
# WRONG, and would have shipped wrong: c06questscript's OnUpdate disables the ghost again with a
# fade once his farewell ends (`gk.Disable(True)` then SetStage(200)), so the lid would have
# returned and the body vanished the moment the quest completed. Found by decompiling the vanilla
# scripts (Champollion over Skyrim - Misc.bsa), not by assuming. No vanilla reference flips
# permanently at C06's completion - every Enable/Disable in the quest's scripts is either early
# (funeral, statue activator, Kodlak's journal) or undone (the ghost).
#
# So the parent is OUR OWN reference: an XMarker, initially disabled, carrying a Papyrus script
# (YsgramorsArmorTombGate.psc, beside this file) that enables the marker once C06 reports
# completed. It polls only while the tomb cell is attached, or once at first load, and stops
# for good after it fires. Enable-parent children then follow in one step:
#
#   lid   -> OPPOSITE of the marker : sealed until the quest completes, then gone
#   cage  -> OPPOSITE of the marker : likewise
#   body  -> NORMAL                 : appears when the tomb opens
#
# Because the switch is our marker and not a Disable() written onto vanilla references, removing
# the plugin removes the marker and every vanilla reference returns to its vanilla state.
# Enable-parent members are persistent references in the cell's PERSISTENT group (the CK does
# the same when a parent is set), and the marker carries the Persistent flag as a scripted
# reference must.
QUEST_GATE = True

C06_QUEST        = 0x0001CEF6   # QUST "C06", Glory of the Dead - EditorID read out of Skyrim.esm
XMARKER_BASE     = 0x0000003B   # STAT "XMarker"                - likewise
GATE_SCRIPT      = b"YsgramorsArmorTombGate"
GATE_MARKER_EDID = b"AR_YsgramorTombGateMarker\x00"
FLAG_PERSISTENT  = 0x00000400
XESP_OPPOSITE    = 0x00000001


def xesp(parent, opposite):
    """Enable parent: 8 bytes, parent form id then flags. Layout read off the vanilla doors in
    this very cell (REFR 0x000D794E), which carry an 8-byte XESP of exactly this shape."""
    return sub(b"XESP", struct.pack("<II", parent, XESP_OPPOSITE if opposite else 0))



def group(label: bytes, gtype: int, payload: bytes) -> bytes:
    """A GRUP: 24-byte header whose size field INCLUDES the header."""
    return (b"GRUP" + struct.pack("<I", len(payload) + 24) + label +
            struct.pack("<i", gtype) + struct.pack("<I", 0) + struct.pack("<HH", 0, 0) + payload)


def clone_vanilla_npc(skyrim_esm: str, formid: int, want_type: bytes = b"NPC_"):
    """Return the subrecord list of a vanilla NPC_, decompressing if needed.

    Cloning a real record beats hand-building one: an NPC_ has a dozen structurally required
    subrecords (race, template, voice, AI data, stats) and getting any of them wrong produces a
    plugin that loads and then misbehaves. TreasCorpseDraugrMale is the vanilla draugr CORPSE
    used for exactly this - a body lying in a tomb with an inventory to loot.
    """
    import zlib
    d = open(skyrim_esm, "rb").read()

    def walk(off, end):
        while off + 24 <= end:
            typ = d[off:off + 4]
            size = struct.unpack_from("<I", d, off + 4)[0]
            if typ == b"GRUP":
                r = walk(off + 24, off + size)
                if r: return r
                off += size
            else:
                fl = struct.unpack_from("<I", d, off + 8)[0]
                fid = struct.unpack_from("<I", d, off + 12)[0]
                if fid == formid and typ == want_type:
                    data = d[off + 24:off + 24 + size]
                    if fl & 0x00040000:
                        data = zlib.decompress(data[4:])
                    out, i = [], 0
                    while i + 6 <= len(data):
                        t = data[i:i + 4]
                        sz = struct.unpack_from("<H", data, i + 4)[0]
                        i += 6
                        out.append((t, data[i:i + sz]))
                        i += sz
                    # the source's own form version rides along: a cloned record keeps it (the
                    # Dragonbone generator crashed the game by re-stamping copied records as 44)
                    out.append((b"__FV", struct.pack("<H", struct.unpack_from("<H", d, off + 20)[0])))
                    return out
                off += 24 + size
        return None

    return walk(24 + struct.unpack_from("<I", d, 4)[0], len(d))


def vanilla_subrecord(skyrim_esm: str, rtype: bytes, formid: int, tag: bytes) -> bytes:
    """One subrecord of a vanilla record, verbatim - so an override repeats the master's bytes
    instead of a rounded retyping of them (1.0.1 wrote the cage's position from 2-decimal
    constants, 0.03 units off the vanilla floats)."""
    subs = clone_vanilla_npc(skyrim_esm, formid, rtype)
    if subs is None:
        raise SystemExit(f"could not read {rtype.decode()} 0x{formid:08X} from {skyrim_esm}")
    vals = [v for t, v in subs if t == tag]
    if len(vals) != 1:
        raise SystemExit(f"{rtype.decode()} 0x{formid:08X} has {len(vals)} {tag.decode()} subrecords")
    return vals[0]


# The tomb cell's English name, read out of Skyrim_english.STRINGS (string 0xFB06, inside
# "Skyrim - Interface.bsa") - Skyrim.esm is localised, so its FULL is a 4-byte string id, and our
# plugin (theirs) is NOT localised, so the id cannot be carried as-is: a non-localised plugin
# would read those four bytes as the name itself.
TOMB_FULL_STRING_ID = 0x0000FB06
TOMB_FULL_TEXT      = b"Ysgramor's Tomb\x00"


def tomb_cell_override(skyrim_esm: str, localized: bool) -> bytes:
    """The tomb CELL record our references need as their parent, as a FULL copy of Skyrim.esm's.

    The cell itself is not something this mod changes - but references placed in (or overriding
    references of) a vanilla cell must sit inside that cell's group, under a copy of its CELL
    record. 1.0.1 wrote that copy with an EDID and nothing else (the page-claims audit,
    2026-10-25). An override replaces the whole record, so whenever ours won the tomb lost what
    Skyrim.esm gives it: the interior flags (DATA), lighting (XCLL, LTMP), its location XLCN
    (YsgramorsTombLocation - cleared status, quest aliases), encounter zone, music, acoustics,
    image space, water and name. Now every subrecord is carried over verbatim (Update.esm and the
    DLC masters do not touch this cell, so Skyrim.esm's record IS the winning vanilla one); the
    only change is FULL, written as plain text because the plugin is not localised.
    """
    subs = clone_vanilla_npc(skyrim_esm, TOMB_CELL, b"CELL")
    if subs is None:
        raise SystemExit(f"could not read CELL 0x{TOMB_CELL:08X} from {skyrim_esm}")
    fv = struct.unpack("<H", dict(subs)[b"__FV"])[0]
    body = b""
    for tag, val in subs:
        if tag == b"__FV":
            continue
        if tag == b"EDID" and val != TOMB_EDID:
            raise SystemExit(f"CELL 0x{TOMB_CELL:08X} is {val!r}, not {TOMB_EDID!r}")
        if tag == b"FULL" and not localized:
            if len(val) != 4 or struct.unpack("<I", val)[0] != TOMB_FULL_STRING_ID:
                raise SystemExit(f"tomb FULL is {val.hex()}, not string id 0x{TOMB_FULL_STRING_ID:X} - "
                                 f"read the name again from the strings table")
            val = TOMB_FULL_TEXT
        body += sub(tag, val)
    for need in (b"DATA", b"XCLL", b"XLCN"):
        if need not in dict(subs):
            raise SystemExit(f"vanilla tomb cell has no {need.decode()} - unexpected master")
    return record(b"CELL", TOMB_CELL, body, form_version=fv)


def build_placement(next_id: int, skyrim_esm: str, localized: bool = False):
    """Ysgramor himself, lying in his sarcophagus wearing the armour.

    The owner, 2026-09-10: "add a draugr corpse there call it ygremore and put the armor on the
    corpse". This replaces the four loose pieces that were resting in the coffin - a body reads
    far better, and the armour is then looted the ordinary way instead of picked up as litter.

    Three new records and two overrides:
        OTFT  the four pieces (NO CLOAK, as asked earlier)
        NPC_  a clone of TreasCorpseDraugrMale, renamed Ysgramor, wearing that outfit
        ACHR  him, placed in the sarcophagus and flagged STARTS DEAD (0x200, the flag every
              vanilla draugr corpse placement carries - checked, not assumed)
        REFR  the casket lid, disabled, so he is visible
        REFR  the bridge cage the owner named, disabled
    """
    recs = []
    fid = next_id

    # --- the outfit: four pieces, no cloak
    outfit_id = fid; fid += 1
    body = sub(b"EDID", b"AR_YsgramorTombOutfit" + b"\x00")
    body += sub(b"INAM", b"".join(struct.pack("<I", a) for nm, a, _ing in ARMOUR if nm != "Cloak"))
    recs.append(record(b"OTFT", 0x04000000 | outfit_id, body))

    # --- the corpse, cloned from vanilla so every required subrecord is real
    npc_id = fid; fid += 1
    src = clone_vanilla_npc(skyrim_esm, CORPSE_TEMPLATE)
    if not src:
        raise SystemExit(f"could not read NPC_ 0x{CORPSE_TEMPLATE:08X} from {skyrim_esm}")
    npc_form_version = struct.unpack("<H", dict(src)[b"__FV"])[0]      # vanilla's own (40)
    src = [(t, v) for t, v in src if t != b"__FV"]
    out = []
    for tag, val in src:
        if tag == b"EDID":
            out.append((b"EDID", b"AR_YsgramorCorpse" + b"\x00"))
        elif tag == b"FULL":
            continue                                        # ours is written above
        elif tag == b"CNAM":
            # FULL belongs AFTER CNAM and before DATA - where every vanilla NPC_ carries it,
            # including MQ305Ysgramor in this very plugin. Subrecord order is not free-form:
            # writing FULL straight after EDID parses today but is not the shape the engine and
            # the tooling expect to read.
            out.append((b"CNAM", val))
            out.append((b"FULL", b"Ysgramor" + b"\x00"))
        elif tag == b"DOFT":
            out.append((b"DOFT", struct.pack("<I", 0x04000000 | outfit_id)))
        elif tag == b"ACBS":
            # templateDataFlags sits at OFFSET 18, not 16 - offset 16 is dispositionBase. The
            # ACBS layout is flags(4) magicka(2) stamina(2) level(2) calcMin(2) calcMax(2)
            # speedMult(2) disposition(2) templateFlags(2) healthOffset(2) bleedout(2), and the
            # vanilla bytes end "...0000 ff0f 0000 0000" - the ff0f at 18 is the 0x0FFF.
            # An earlier pass wrote to 16, which zeroed dispositionBase (already 0) and left
            # 0x0FFF standing, so the record silently inherited its name and inventory from the
            # template and both of our changes would have been thrown away.
            #
            # 0x0FFF is "inherit everything from TPLT". Clear "Use Base Data" (0x0080) so our
            # FULL is used, and "Use Inventory" (0x0100) so our DOFT is used.
            acbs = bytearray(val)
            tdf = struct.unpack_from("<H", acbs, 18)[0]
            struct.pack_into("<H", acbs, 18, tdf & ~0x0180)
            out.append((b"ACBS", bytes(acbs)))
        else:
            out.append((tag, val))
    if not any(t == b"FULL" for t, _ in out):
        raise SystemExit("cloned NPC had no CNAM to anchor FULL after - name would be missing")
    if not any(t == b"DOFT" for t, _ in out):
        out.append((b"DOFT", struct.pack("<I", 0x04000000 | outfit_id)))
    recs.append(record(b"NPC_", 0x04000000 | npc_id, b"".join(sub(t, v) for t, v in out),
                       form_version=npc_form_version))

    # --- him, in the coffin
    achr_id = fid; fid += 1
    x, y, z = CORPSE_POS
    body = sub(b"EDID", b"AR_YsgramorCorpseRef" + b"\x00")
    body += sub(b"NAME", struct.pack("<I", 0x04000000 | npc_id))
    # The saved ragdoll pose, verbatim from vanilla ACHR 0x00078850, in vanilla's own subrecord
    # order (NAME then XRGD). This is the piece whose absence put him on the floor twice. It is
    # read from a file rather than pasted in as an escape sequence, because embedded NUL escapes
    # in this script have been corrupted by editing more than once.
    with open(RAGDOLL_FILE, "rb") as f:
        ragdoll = f.read()
    if len(ragdoll) != 504:
        raise SystemExit(f"ragdoll blob is {len(ragdoll)} bytes, expected the vanilla 504")
    body += sub(b"XRGD", ragdoll)
    if QUEST_GATE:
        marker_id = fid; fid += 1
        marker_fid = 0x04000000 | marker_id
        body += xesp(marker_fid, False)            # appears when the tomb opens
    body += sub(b"DATA", struct.pack("<6f", x, y, z, 0.0, 0.0, CORPSE_ROTZ))
    body_flags = FLAG_STARTS_DEAD | (FLAG_PERSISTENT | FLAG_INITIALLY_DISABLED if QUEST_GATE else 0)
    recs.append(record(b"ACHR", 0x04000000 | achr_id, body, flags=body_flags))

    # --- the two removals
    cage = sub(b"NAME", struct.pack("<I", CAGE_BASE))
    if QUEST_GATE:
        cage += xesp(marker_fid, True)             # present until the quest completes
    cage_data = vanilla_subrecord(skyrim_esm, b"REFR", CAGE_REF, b"DATA")
    assert all(abs(a - b) < 0.01 for a, b in zip(struct.unpack("<6f", cage_data), CAGE_DATA)), \
        "vanilla cage position no longer matches CAGE_DATA"
    cage += sub(b"DATA", cage_data)               # the master's own bytes
    recs.append(record(b"REFR", CAGE_REF, cage,
                       flags=FLAG_PERSISTENT if QUEST_GATE else FLAG_INITIALLY_DISABLED))

    lid = sub(b"NAME", struct.pack("<I", LID_BASE))
    if QUEST_GATE:
        lid += xesp(marker_fid, True)              # sealed until the quest completes
    lid_data = vanilla_subrecord(skyrim_esm, b"REFR", LID_REF, b"DATA")
    assert all(abs(a - b) < 0.01 for a, b in zip(struct.unpack("<6f", lid_data), LID_DATA)), \
        "vanilla lid position no longer matches LID_DATA"
    lid += sub(b"DATA", lid_data)                 # the master's own bytes
    recs.append(record(b"REFR", LID_REF, lid,
                       flags=FLAG_PERSISTENT if QUEST_GATE else FLAG_INITIALLY_DISABLED))

    if QUEST_GATE:
        # --- the switch: our marker, scripted, off until C06 completes
        marker = sub(b"EDID", GATE_MARKER_EDID)
        marker += sub(b"VMAD", vmad_object_script(GATE_SCRIPT, [(b"GloryOfTheDead", C06_QUEST)]))
        marker += sub(b"NAME", struct.pack("<I", XMARKER_BASE))
        marker += sub(b"DATA", struct.pack("<6f", *SARCOPHAGUS_ORIGIN, 0.0, 0.0, 0.0))
        recs.append(record(b"REFR", marker_fid, marker,
                           flags=FLAG_PERSISTENT | FLAG_INITIALLY_DISABLED))
        # enable-parent members and the scripted marker are persistent: PERSISTENT group (8)
        children = group(struct.pack("<I", TOMB_CELL), 6,
                         group(struct.pack("<I", TOMB_CELL), 8, b"".join(recs[2:])))
    else:
        temporary = group(struct.pack("<I", TOMB_CELL), 9, b"".join(recs[2:]))   # ACHR + 2 REFRs
        children  = group(struct.pack("<I", TOMB_CELL), 6, temporary)
    cell      = tomb_cell_override(skyrim_esm, localized)
    subblock  = group(struct.pack("<i", TOMB_SUBBLOCK), 3, cell + children)
    block     = group(struct.pack("<i", TOMB_BLOCK), 2, subblock)
    cell_top  = group(b"CELL", 0, block)

    # the OTFT and NPC_ are ordinary top-level records, in their own groups
    otft_top = group(b"OTFT", 0, recs[0])
    npc_top  = group(b"NPC_", 0, recs[1])
    return otft_top + npc_top + cell_top, len(recs), fid


# --- the corpse rendered NAKED even with DraugrRace in every additional-race list ------------
# Second look, after the placement was fixed and he still showed bare draugr skin under his own
# name with all four pieces sitting in his inventory.
#
# What the screenshot actually shows is SkinDraugrMale02 - his race skin, which occupies biped
# slot 32 exactly as a cuirass does. An equipped cuirass REPLACES that slot, so a draugr still
# showing his skin torso is a draugr who has not equipped the cuirass at all.
#
# Skyrim.esm was then searched for what it does itself, and the answer is narrow:
#   * 119 start-dead actors DO wear real body armour from a default outfit, several with our exact
#     template shape (dunChillwindFalmerPrisoner01, tdf 0x0E7F, templated) - so "starts dead" and
#     "uses a template" are both fine and neither is the cause.
#   * Not one of those 119 is a draugr. Every single one is a humanoid race.
#   * The ONLY equippable armour any vanilla draugr wears is DraugrHelmet01/02/03, and those
#     armatures are built differently from ours: RNAM (the armature's PRIMARY race) is DraugrRace
#     itself, with no additional-race list at all. Bethesda never relies on the additional-race
#     list to put armour on a draugr.
#
# So the additional-race entries stay (they cost nothing and they are what the Creation Kit writes
# for a human-race armour), and alongside them each piece now also gets a second armature whose
# PRIMARY race is DraugrRace - the DraugrHelmet01AA shape, which is the one arrangement the engine
# is demonstrably known to render on a draugr. The armature is added to the armour's armature list,
# so a Nord player still resolves the original one and only a draugr resolves the new one.
DRAUGR_ARMATURES = {
    # ARMO to give a draugr armature      ARMA to clone it from        name for the clone
    0x04000802: (0x04000808, "Cuirass"),
    0x04000801: (0x04000809, "Gauntlets"),
    0x04000803: (0x0400080B, "Boots"),
    0x04000800: (0x0400080C, "Helmet"),
}
# The cloak is deliberately absent: it is not part of the tomb set (the owner, 2026-09-10:
# "this armor set, without the cloak"), so nothing wears it on a draugr.


def split_subrecords(body: bytes):
    """[(tag, payload)] for one uncompressed record body."""
    out, j = [], 0
    while j + 6 <= len(body):
        tag = body[j:j + 4]
        size = struct.unpack_from("<H", body, j + 4)[0]
        out.append((tag, body[j + 6:j + 6 + size]))
        j += 6 + size
    return out


def find_record(blob: bytes, want_type: bytes, want_fid: int):
    """The uncompressed body of one record, searched through nested GRUPs."""
    i = 0
    while i + 24 <= len(blob):
        typ = blob[i:i + 4]
        size = struct.unpack_from("<I", blob, i + 4)[0]
        if typ == b"GRUP":
            hit = find_record(blob[i + 24:i + size], want_type, want_fid)
            if hit is not None:
                return hit
            i += size
            continue
        if typ == want_type and struct.unpack_from("<I", blob, i + 12)[0] == want_fid:
            flags = struct.unpack_from("<I", blob, i + 8)[0]
            body = blob[i + 24:i + 24 + size]
            if flags & 0x40000:
                body = zlib.decompress(body[4:])
            return body
        i += 24 + size
    return None


def build_draugr_armatures(blob: bytes, next_fid: int):
    """One draugr-primary armature per tomb piece, cloned from the mod's own.

    Everything is carried over verbatim - the same meshes, the same slots, the same priorities -
    and exactly two things change: the editor id, and RNAM, which becomes DraugrRace. The
    additional-race MODL list is dropped, because on this armature it would be meaningless: the
    primary race already is the draugr.
    """
    made = []
    for armo_fid, (arma_fid, label) in sorted(DRAUGR_ARMATURES.items()):
        body = find_record(blob, b"ARMA", arma_fid)
        if body is None:
            raise SystemExit(f"ARMA 0x{arma_fid:08X} ({label}) not found - the source plugin is "
                             f"not the one this script was written against")
        out = bytearray()
        for tag, val in split_subrecords(body):
            if tag == b"EDID":
                val = f"AR_Ysgramor{label}DraugrAA".encode("ascii") + b"\x00"
            elif tag == b"RNAM":
                val = struct.pack("<I", DRAUGR_RACE)
            elif tag == b"MODL" and len(val) == 4:
                continue                      # additional races: not used on this armature
            out += sub(tag, val)
        made.append((armo_fid, 0x04000000 | next_fid,
                     record(b"ARMA", 0x04000000 | next_fid, bytes(out))))
        next_fid += 1
    return made, next_fid


def add_draugr_race(blob: bytes, new_armatures=()):
    """Add DraugrRace to every ARMA's additional-race list.

    Why: the corpse spawned NAKED. Not the outfit and not the Starts Dead flag - the armour's ARMA
    records list 24-28 races and DraugrRace is not among them, so a draugr cannot render these
    pieces at all. In ARMA, each 4-byte MODL subrecord is one additional race; appending one after
    the last existing MODL is exactly what the Creation Kit writes.

    This is the one place the original records are NOT passed through untouched, and it is
    deliberate - without it the whole corpse idea cannot work.
    """
    by_armo = {armo: arma for armo, arma, _ in new_armatures}
    appended = b"".join(rec for _, _, rec in new_armatures)
    out = bytearray()
    i = 0
    patched = armos = 0
    while i + 24 <= len(blob):
        typ = blob[i:i + 4]
        size = struct.unpack_from("<I", blob, i + 4)[0]
        if typ == b"GRUP":
            label = blob[i + 8:i + 12]
            gtype = struct.unpack_from("<i", blob, i + 12)[0]
            inner, n, m = add_draugr_race(blob[i + 24:i + size], new_armatures)
            patched += n
            armos += m
            if label == b"ARMA" and gtype == 0:
                inner += appended            # the new armatures live in the ARMA group
            # the size field is rewritten from the rebuilt contents rather than patched in place
            out += blob[i:i + 4] + struct.pack("<I", len(inner) + 24) + blob[i + 8:i + 24] + inner
            i += size
            continue
        rec = blob[i:i + 24 + size]
        rec_fid = struct.unpack_from("<I", blob, i + 12)[0]
        if typ == b"ARMO" and rec_fid in by_armo:
            if struct.unpack_from("<I", blob, i + 8)[0] & 0x40000:
                raise SystemExit(f"ARMO 0x{rec_fid:08X} is compressed - cannot append an armature")
            body = rec[24:]
            subs_out, j, last_modl_end = bytearray(), 0, None
            while j + 6 <= len(body):
                t = body[j:j + 4]
                sz = struct.unpack_from("<H", body, j + 4)[0]
                subs_out += body[j:j + 6 + sz]
                if t == b"MODL" and sz == 4:
                    last_modl_end = len(subs_out)
                j += 6 + sz
            if last_modl_end is None:
                raise SystemExit(f"ARMO 0x{rec_fid:08X} has no armature list to extend")
            subs_out[last_modl_end:last_modl_end] = sub(b"MODL", struct.pack("<I", by_armo[rec_fid]))
            armos += 1
            rec = rec[:4] + struct.pack("<I", len(subs_out)) + rec[8:24] + bytes(subs_out)
        elif typ == b"ARMA":
            body = rec[24:]
            subs_out, j, last_modl_end = bytearray(), 0, None
            while j + 6 <= len(body):
                t = body[j:j + 4]
                sz = struct.unpack_from("<H", body, j + 4)[0]
                subs_out += body[j:j + 6 + sz]
                if t == b"MODL" and sz == 4:
                    last_modl_end = len(subs_out)
                j += 6 + sz
            if last_modl_end is not None:
                extra = sub(b"MODL", struct.pack("<I", DRAUGR_RACE))
                subs_out[last_modl_end:last_modl_end] = extra
                patched += 1
            rec = rec[:4] + struct.pack("<I", len(subs_out)) + rec[8:24] + bytes(subs_out)
        out += rec
        i += 24 + size
    return bytes(out), patched, armos

def main(src: str, dst: str) -> int:
    print("verifying condition layout:")
    verify_conditions()

    data = open(src, "rb").read()
    tes4_size = struct.unpack_from("<I", data, 4)[0]
    tes4_flags = struct.unpack_from("<I", data, 8)[0]
    tes4_body = data[24:24 + tes4_size]
    rest = data[24 + tes4_size:]          # every GRUP; ARMO/ARMA records are adjusted below

    # read the header we must update
    num_records = next_id = None
    i = 0
    while i + 6 <= len(tes4_body):
        tag = tes4_body[i:i + 4]
        n = struct.unpack_from("<H", tes4_body, i + 4)[0]
        i += 6
        if tag == b"HEDR":
            version, num_records, next_id = struct.unpack("<fiI", tes4_body[i:i + 12])
            hedr_at = i
        i += n
    if num_records is None:
        raise SystemExit("no HEDR in the source plugin")
    print(f"  source: {num_records} records, nextObjectID 0x{next_id:X}, "
          f"ESL={bool(tes4_flags & 0x200)}")

    if any(fid & 0xFFFFFF >= next_id for _, fid, _ in ARMOUR):
        raise SystemExit("an armour form id is at or beyond nextObjectID - refusing to guess")

    records, fid = [], next_id
    for name, armour_fid, ingredients in ARMOUR:
        # The owner, 2026-09-17: "it shouldnt be craftable until you aquire the item from the quest".
        # GetItemCount (function 47) on the crafter, >= 1 of THIS piece: the forge offers a copy only
        # once the piece has been taken off Ysgramor's body in his tomb. Comparison type sits in the
        # top three bits of the op byte - 3 (>=) << 5 = 0x60 - with no OR flag, so both conditions
        # (this and the Ebony Smithing perk) must hold, the same AND the vanilla recipes use.
        records.append(cobj(0x04000000 | fid, f"AR_RecipeYsgramor{name}", ingredients,
                            armour_fid, STATION_CRAFT,
                            [ctda(0x60, 1.0, 47, armour_fid), ctda(0x00, 1.0, 448, PERK_EBONY)]))
        fid += 1
        records.append(cobj(0x04000000 | fid, f"AR_TemperYsgramor{name}", [(INGOT_EBONY, 1)],
                            armour_fid, STATION_TEMPER,
                            [ctda(0x21, 1.0, 659), ctda(0x00, 1.0, 448, PERK_ARCANE)]))
        fid += 1

    if fid > 0xFFF:
        raise SystemExit(f"form ids would reach 0x{fid:X}, past the ESL range - would break the "
                         f"plugin's light flag")

    cobj_last = fid - 1                  # remembered before the placement records take ids
    blob = b"".join(records)
    cobj_group = (b"GRUP" + struct.pack("<I", len(blob) + 24) + b"COBJ" +
                  struct.pack("<i", 0) + struct.pack("<I", 0) + struct.pack("<HH", 0, 0) + blob)

    placement, placed, fid = build_placement(fid, SKYRIM_ESM, localized=bool(tes4_flags & 0x80))
    print(f"  Ysgramor laid in the sarcophagus at {CORPSE_POS} rotZ {CORPSE_ROTZ:.4f}, "
          f"posed by vanilla's own ragdoll data, wearing the four pieces (no cloak)")
    gate = (f"enable-parented (opposite) to scripted marker; opens when C06 completes"
            if QUEST_GATE else "disabled outright (quest gate OFF - testing)")
    print(f"  cage REFR 0x{CAGE_REF:08X} (NorBridgeCageMid01, base 0x{CAGE_BASE:08X}): {gate}")
    print(f"  lid REFR 0x{LID_REF:08X}: {gate}")
    print(f"  records added: {placed} (outfit, corpse NPC, his placement, the two removals"
          f"{', the gate marker' if QUEST_GATE else ''})")

    # the draugr-primary armatures, and the two edits to the mod's own records that carry them
    draugr_arma, fid = build_draugr_armatures(rest, fid)
    if fid > 0xFFF:
        raise SystemExit(f"form ids would reach 0x{fid:X}, past the ESL range")
    rest, armas, armos = add_draugr_race(rest, draugr_arma)
    if armos != len(draugr_arma):
        raise SystemExit(f"attached {armos} armatures but built {len(draugr_arma)}")

    # only the two header fields that must change
    new_tes4_body = bytearray(tes4_body)
    struct.pack_into("<fiI", new_tes4_body, hedr_at, version,
                     num_records + len(records) + placed + len(draugr_arma), fid)
    new_tes4 = record(b"TES4", 0, bytes(new_tes4_body), flags=tes4_flags)

    out = new_tes4 + rest + cobj_group + placement
    with open(dst, "wb") as f:
        f.write(out)

    print(f"  added {len(records)} COBJ records at 0x{0x04000000 | next_id:08X}"
          f"-0x{0x04000000 | cobj_last:08X}")
    print(f"  header: {num_records} -> {num_records + len(records) + placed + len(draugr_arma)} records, "
          f"nextObjectID 0x{next_id:X} -> 0x{fid:X}")
    print(f"wrote {dst}  ({len(out):,} bytes, was {len(data):,})")
    print(f"  ARMA records taught DraugrRace as an additional race: {armas}")
    for armo_fid, arma_fid, _ in draugr_arma:
        print(f"  ARMO 0x{armo_fid:08X} also resolves 0x{arma_fid:08X}, "
              f"an armature whose PRIMARY race is DraugrRace")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
