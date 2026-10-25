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

WHAT IS ADDED
    Ten COBJ recipes; Ysgramor's body (OTFT, NPC_, and its ACHR in a holding CELL of our own); a
    draugr-primary armature per tomb piece; and one start-game-enabled QUST whose script opens the
    tomb at run time. The plugin overrides NO vanilla cell, worldspace or placed reference (the
    owner, 2026-10-25) - the build refuses to write one that does (walk_output). Of the original
    mod's records, ARMO/ARMA gain the draugr armature and race entries (add_draugr_race); the rest,
    including its NPC_ override of Skyrim.esm's MQ305Ysgramor (Sovngarde), pass through unchanged.
    No master is added; the header changes only its record count and next object id.

    New form ids start at the plugin's own nextObjectID (0x80E), so they cannot collide with the
    ids already in use (0x800-0x80D). The plugin is ESL-flagged already, and every new id stays
    inside the light range, so it keeps its free load-order slot.

WHY THESE INGREDIENTS
    The armour carries vanilla ArmorMaterialEbony + ArmorHeavy, read out of the plugin itself, so
    the recipes follow vanilla ebony. Their SHAPE is copied byte-for-byte from Skyrim.esm's
    RecipeArmorEbonyCuirass (0x000DD989) and TemperArmorEbonyCuirass (0x000EB448) - the condition
    layout is verified against those real bytes on every run, because a CTDA that is the wrong
    length loads without complaint and then misbehaves.

The recipes are gated on OWNING the piece (GetItemCount >= 1), which in turn comes from Ysgramor's
body in his tomb once Glory of the Dead (C06) is complete.
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



# ---------------------------------------------------------------- the tomb (redesigned 2026-10-25)
# The owner, 2026-10-25, on 1.0.2's full copy of the tomb cell: "I don't see why Ysgramor's armor
# add-on needs to have a copy of the cell, because now any mod that changes that cell is going to be
# incompatible with our mod, when all that our mod really needs to do is follow the quest ... to read
# the right moment for the tomb sarcophagus lid to disappear, and that's it."
#
# So the plugin overrides NO vanilla cell, worldspace or placed reference. 1.0.0-1.0.2 placed the
# body in Ysgramor's tomb and overrode the lid and the cage there, and a plugin cannot do either
# without carrying the parent CELL record - which then wins over every other mod's edit of the tomb.
# Now:
#
#   QUST  AR_YsgramorTombQuest   start-game enabled, one script (YsgramorsArmorTombQuest.psc beside
#                                this file). Every few seconds: if Glory of the Dead (C06) is complete,
#                                move the body into the sarcophagus once, and - while the player is
#                                in the tomb - disable the lid and the cage with a fade.
#   CELL  AR_YsgramorHoldingCell an interior of the mod's OWN, never visited, no doors - where the
#                                body waits. (The same shape as Simple Loadout System's storage cell.)
#   ACHR  AR_YsgramorCorpseRef   the body: starts dead, persistent, initially disabled, with vanilla's
#                                saved ragdoll pose (XRGD) - in the holding cell now.
#
# The form ids stay where 1.0.1 (posted) put them: OTFT 0x818, NPC_ 0x819, ACHR 0x81A, the draugr
# armatures 0x81C-0x81F. 0x81B was 1.0.1's gate marker and is retired, never reused, so a save that
# knew it does not meet a different record under the same id. The quest and the cell take 0x820 and
# 0x821.
#
# EVERY vanilla fact the script depends on is read out of Skyrim.esm on each build (check_tomb_facts):
#   * REFR 0x000AF824 is NorSarcophagusTop (base 0x00034CE3) and REFR 0x000D83AB NorBridgeCageMid01
#     (base 0x00034019), both TEMPORARY children of YsgramorsTomb01 (0x00015254) - so the script looks
#     them up with Game.GetForm only while the tomb is loaded.
#   * REFR 0x00033DFE NorSarcophagusBottom is PERSISTENT and in that cell - the body's anchor, reachable
#     whether or not the tomb is loaded.
#   * C06 stage 200 carries the "completes quest" flag.
#   * the tomb's encounter zone (0x0003EC91) has Never Resets, so the disabled lid stays disabled.

TOMB_CELL        = 0x00015254   # CELL YsgramorsTomb01
TOMB_ZONE        = 0x0003EC91   # ECZN YsgramorsTombZone
LID_REF          = 0x000AF824   # REFR NorSarcophagusTop
LID_BASE         = 0x00034CE3
CAGE_REF         = 0x000D83AB   # REFR NorBridgeCageMid01 (the owner named it, 2026-09-10)
CAGE_BASE        = 0x00034019
SARCOPHAGUS_REF  = 0x00033DFE   # REFR NorSarcophagusBottom
SARCOPHAGUS_BASE = 0x00034CE1
SARCOPHAGUS_ORIGIN = (895.26, -358.02, -1350.99)
C06_QUEST        = 0x0001CEF6   # QUST "C06", Glory of the Dead
C06_DONE_STAGE   = 200

FLAG_PERSISTENT         = 0x00000400
FLAG_INITIALLY_DISABLED = 0x00000800
FLAG_STARTS_DEAD        = 0x00000200   # ACHR record flag; every vanilla corpse placement carries it

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

# --- where the body lies, copied from how VANILLA lays a corpse in a closed sarcophagus -----------
# Two early attempts put him on the floor behind the coffin. The answer was vanilla's own: all 17
# corpses lying within 90 units of one of the 220 NorSarcophagusBottom placements in Skyrim.esm carry
# XRGD - saved RAGDOLL DATA - which pins a dead body in a hand-authored pose. The pair copied:
#   REFR 0x0007884F NorSarcophagusBottom     pos (1409.31, 2460.86, -1423.75) rotZ 6.0332
#   ACHR 0x00078850 TreasCorpseDraugrFemale  dist 43.2u, dZ +40.5, flags StartsDead, NAME/XRGD/XLCN/DATA
# Its XY offset and rotation, rotated out of that sarcophagus's frame into ours, give the position
# below; XRGD holds bone offsets in the actor's own frame, so it transplants unchanged. The script
# (YsgramorsArmorTombQuest.psc) carries the same numbers - check_script_constants() compares them.
CORPSE_POS   = (909.66, -362.16, -1310.44)
CORPSE_ROTZ  = 1.8792            # radians; the script's BodyAngleZ is this in degrees
RAGDOLL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ysgramor-corpse-ragdoll.bin")
SCRIPT_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "YsgramorsArmorTombQuest.psc")

QUEST_SCRIPT     = b"YsgramorsArmorTombQuest"
QUEST_EDID       = b"AR_YsgramorTombQuest\x00"
HOLDING_EDID     = b"AR_YsgramorHoldingCell\x00"
RETIRED_IDS      = (0x81B,)      # 1.0.1's AR_YsgramorTombGateMarker - never reused


def wstr(s: bytes) -> bytes:
    """VMAD's string form: uint16 length, no terminator."""
    return struct.pack("<H", len(s)) + s


def vmad_script(script: bytes, props) -> bytes:
    """A VMAD subrecord carrying ONE script, in the v5 / object-format-2 layout every SE record uses:
    version, objFormat, scriptCount; per script name + status + props; per property name, type,
    status 1 (edited), value. Type 1 (Object) is objFormat-2's uint16 unused, int16 alias (-1 =
    none), uint32 form id; type 3 (Int) is an int32. A quest's VMAD may end right after its scripts -
    vanilla DialogueGeneric (0x00013EB3) carries one script, two Object properties and nothing more."""
    b = struct.pack("<hhH", 5, 2, 1)
    b += wstr(script) + struct.pack("<B", 0) + struct.pack("<H", len(props))
    for name, kind, value in props:
        if kind == "object":
            b += wstr(name) + struct.pack("<BB", 1, 1) + struct.pack("<HhI", 0, -1, value)
        elif kind == "int":
            b += wstr(name) + struct.pack("<BB", 3, 1) + struct.pack("<i", value)
        else:
            raise ValueError(kind)
    return b


def group(label: bytes, gtype: int, payload: bytes) -> bytes:
    """A GRUP: 24-byte header whose size field INCLUDES the header."""
    return (b"GRUP" + struct.pack("<I", len(payload) + 24) + label +
            struct.pack("<i", gtype) + struct.pack("<I", 0) + struct.pack("<HH", 0, 0) + payload)


def clone_vanilla_npc(skyrim_esm: str, formid: int, want_type: bytes = b"NPC_"):
    """Return the subrecord list of a vanilla record (NPC_ by default), decompressing if needed. The
    list ends with three pseudo-subrecords: __FV (the record's form version), __FL (its record
    flags) and __GP (the type and label of the group it sits in).

    Cloning a real record beats hand-building one: an NPC_ has a dozen structurally required
    subrecords (race, template, voice, AI data, stats) and getting any of them wrong produces a
    plugin that loads and then misbehaves. TreasCorpseDraugrMale is the vanilla draugr CORPSE
    used for exactly this - a body lying in a tomb with an inventory to loot.
    """
    d = open(skyrim_esm, "rb").read()

    def walk(off, end, gtype, glabel):
        while off + 24 <= end:
            typ = d[off:off + 4]
            size = struct.unpack_from("<I", d, off + 4)[0]
            if typ == b"GRUP":
                r = walk(off + 24, off + size, struct.unpack_from("<i", d, off + 12)[0],
                         struct.unpack_from("<I", d, off + 8)[0])
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
                    out.append((b"__FL", struct.pack("<I", fl)))
                    out.append((b"__GP", struct.pack("<iI", gtype, glabel)))
                    return out
                off += 24 + size
        return None

    return walk(24 + struct.unpack_from("<I", d, 4)[0], len(d), 0, 0)


PSEUDO = (b"__FV", b"__FL", b"__GP")


def check_tomb_facts(skyrim_esm: str) -> None:
    """Read every vanilla fact the script relies on out of Skyrim.esm - refuse to build on a guess."""
    def rec(rtype, fid):
        subs = clone_vanilla_npc(skyrim_esm, fid, rtype)
        if subs is None:
            raise SystemExit(f"{rtype.decode()} 0x{fid:08X} not found in {skyrim_esm}")
        return subs

    def ref_facts(fid, base, persistent):
        subs = dict(rec(b"REFR", fid))
        got_base = struct.unpack("<I", subs[b"NAME"])[0]
        flags = struct.unpack("<I", subs[b"__FL"])[0]
        gtype, glabel = struct.unpack("<iI", subs[b"__GP"])
        want_group = 8 if persistent else 9
        if got_base != base or glabel != TOMB_CELL or gtype != want_group \
                or bool(flags & FLAG_PERSISTENT) != persistent:
            raise SystemExit(f"REFR 0x{fid:08X}: base 0x{got_base:08X} group {gtype}/0x{glabel:08X} "
                             f"flags 0x{flags:08X} - not what the script expects")
        return subs

    ref_facts(LID_REF, LID_BASE, False)
    ref_facts(CAGE_REF, CAGE_BASE, False)
    sarc = ref_facts(SARCOPHAGUS_REF, SARCOPHAGUS_BASE, True)
    pos = struct.unpack("<3f", sarc[b"DATA"][:12])
    if any(abs(a - b) > 0.01 for a, b in zip(pos, SARCOPHAGUS_ORIGIN)):
        raise SystemExit(f"NorSarcophagusBottom is at {pos}, not {SARCOPHAGUS_ORIGIN}")

    quest = rec(b"QUST", C06_QUEST)
    stage_flags, cur = {}, None
    for tag, val in quest:
        if tag == b"INDX":
            cur = struct.unpack("<H", val[:2])[0]
        elif tag == b"QSDT" and cur is not None:
            stage_flags[cur] = val[0]
    if not stage_flags.get(C06_DONE_STAGE, 0) & 0x01:
        raise SystemExit(f"C06 stage {C06_DONE_STAGE} does not carry the completes-quest flag")

    zone = dict(rec(b"ECZN", TOMB_ZONE))
    if not zone[b"DATA"][10] & 0x01:
        raise SystemExit("YsgramorsTombZone no longer has Never Resets")
    cell = dict(rec(b"CELL", TOMB_CELL))
    if struct.unpack("<I", cell[b"XEZN"])[0] != TOMB_ZONE:
        raise SystemExit("YsgramorsTomb01 is no longer in YsgramorsTombZone")
    print("  Skyrim.esm: lid and cage are temporary refs in YsgramorsTomb01, the sarcophagus bottom is "
          "persistent, C06 stage 200 completes the quest, the tomb never resets")


def check_script_constants() -> None:
    """The script's body position and angle must be the generator's (one number, two files)."""
    import math, re
    text = open(SCRIPT_FILE, encoding="utf-8").read()
    want = {"BodyX": CORPSE_POS[0], "BodyY": CORPSE_POS[1], "BodyZ": CORPSE_POS[2],
            "BodyAngleZ": math.degrees(CORPSE_ROTZ)}
    for name, value in want.items():
        m = re.search(r"Float Property " + name + r" = (-?[0-9.]+) AutoReadOnly", text)
        if not m or abs(float(m.group(1)) - value) > 0.01:
            raise SystemExit(f"{SCRIPT_FILE}: {name} is {m.group(1) if m else 'missing'}, "
                             f"the generator says {value:.2f}")


def build_placement(next_id: int, skyrim_esm: str):
    """Ysgramor's body and its outfit: OTFT, NPC_ (top-level records), and the ACHR, which goes in
    the holding cell built by build_tomb_quest (it is returned separately for that).

    The owner, 2026-09-10: "add a draugr corpse there call it ygremore and put the armor on the
    corpse".
        OTFT  the four pieces (NO CLOAK, as asked earlier)
        NPC_  a clone of TreasCorpseDraugrMale, renamed Ysgramor, wearing that outfit
        ACHR  him, flagged STARTS DEAD | PERSISTENT | INITIALLY DISABLED, with vanilla's ragdoll pose;
              the quest script moves him into the sarcophagus and enables him
    """
    fid = next_id

    # --- the outfit: four pieces, no cloak
    outfit_id = fid; fid += 1
    body = sub(b"EDID", b"AR_YsgramorTombOutfit" + b"\x00")
    body += sub(b"INAM", b"".join(struct.pack("<I", a) for nm, a, _ing in ARMOUR if nm != "Cloak"))
    otft = record(b"OTFT", 0x04000000 | outfit_id, body)

    # --- the corpse, cloned from vanilla so every required subrecord is real
    npc_id = fid; fid += 1
    src = clone_vanilla_npc(skyrim_esm, CORPSE_TEMPLATE)
    if not src:
        raise SystemExit(f"could not read NPC_ 0x{CORPSE_TEMPLATE:08X} from {skyrim_esm}")
    npc_form_version = struct.unpack("<H", dict(src)[b"__FV"])[0]      # vanilla's own (40)
    src = [(t, v) for t, v in src if t not in PSEUDO]
    out = []
    for tag, val in src:
        if tag == b"EDID":
            out.append((b"EDID", b"AR_YsgramorCorpse" + b"\x00"))
        elif tag == b"FULL":
            continue                                        # ours is written after CNAM
        elif tag == b"CNAM":
            # FULL belongs AFTER CNAM and before DATA - where every vanilla NPC_ carries it,
            # including MQ305Ysgramor in this very plugin.
            out.append((b"CNAM", val))
            out.append((b"FULL", b"Ysgramor" + b"\x00"))
        elif tag == b"DOFT":
            out.append((b"DOFT", struct.pack("<I", 0x04000000 | outfit_id)))
        elif tag == b"ACBS":
            # templateDataFlags sits at OFFSET 18 (offset 16 is dispositionBase). 0x0FFF is "inherit
            # everything from TPLT"; clear "Use Base Data" (0x0080) so our FULL is used, and "Use
            # Inventory" (0x0100) so our DOFT is used.
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
    npc = record(b"NPC_", 0x04000000 | npc_id, b"".join(sub(t, v) for t, v in out),
                 form_version=npc_form_version)

    # --- him, waiting in the holding cell
    achr_id = fid; fid += 1
    x, y, z = CORPSE_POS
    body = sub(b"EDID", b"AR_YsgramorCorpseRef" + b"\x00")
    body += sub(b"NAME", struct.pack("<I", 0x04000000 | npc_id))
    # The saved ragdoll pose, verbatim from vanilla ACHR 0x00078850, in vanilla's subrecord order
    # (NAME then XRGD). Read from a file: embedded NUL escapes in this script were corrupted by
    # editing more than once.
    with open(RAGDOLL_FILE, "rb") as f:
        ragdoll = f.read()
    if len(ragdoll) != 504:
        raise SystemExit(f"ragdoll blob is {len(ragdoll)} bytes, expected the vanilla 504")
    body += sub(b"XRGD", ragdoll)
    # The tomb coordinates are kept as the record's own position too, so the reference carries the
    # place it is meant for; the script moves him there with MoveTo + SetPosition + SetAngle.
    body += sub(b"DATA", struct.pack("<6f", x, y, z, 0.0, 0.0, CORPSE_ROTZ))
    achr = record(b"ACHR", 0x04000000 | achr_id, body,
                  flags=FLAG_STARTS_DEAD | FLAG_PERSISTENT | FLAG_INITIALLY_DISABLED)

    while fid in RETIRED_IDS:
        fid += 1                                            # 0x81B, 1.0.1's gate marker
    top = group(b"OTFT", 0, otft) + group(b"NPC_", 0, npc)
    return top, achr, 0x04000000 | achr_id, fid


def build_tomb_quest(next_id: int, achr: bytes, achr_fid: int):
    """The quest that opens the tomb, and the holding cell the body waits in."""
    fid = next_id
    quest_id = fid; fid += 1
    vmad = vmad_script(QUEST_SCRIPT, [
        (b"GloryOfTheDead",    "object", C06_QUEST),
        (b"YsgramorsTomb",     "object", TOMB_CELL),
        (b"SarcophagusBottom", "object", SARCOPHAGUS_REF),
        (b"YsgramorBody",      "object", achr_fid),
        (b"LidFormID",         "int",    LID_REF),
        (b"CageFormID",        "int",    CAGE_REF),
    ])
    # DNAM in vanilla DialogueGeneric's shape: flags 0x0011 (Start Game Enabled | Starts Enabled),
    # priority 0, form version byte 0, unknown 0, type 0 (none). NEXT and ANAM close the record as
    # they do in every vanilla quest with no aliases.
    body = (sub(b"EDID", QUEST_EDID) + sub(b"VMAD", vmad) +
            sub(b"DNAM", struct.pack("<HBBII", 0x0011, 0, 0, 0, 0)) +
            sub(b"NEXT", b"") + sub(b"ANAM", struct.pack("<I", 0)))
    quest = record(b"QUST", 0x04000000 | quest_id, body)

    cell_id = fid; fid += 1
    cell = record(b"CELL", 0x04000000 | cell_id,
                  sub(b"EDID", HOLDING_EDID) + sub(b"DATA", struct.pack("<H", 0x0001)))  # interior
    # interior block / sub-block: the last and second-to-last decimal digits of the object index
    index = cell_id & 0xFFFFFF
    block, subblock = index % 10, (index // 10) % 10
    label = struct.pack("<I", 0x04000000 | cell_id)
    children = group(label, 6, group(label, 8, achr))          # persistent children
    cells = group(b"CELL", 0, group(struct.pack("<i", block), 2,
                                    group(struct.pack("<i", subblock), 3, cell + children)))
    return group(b"QUST", 0, quest), cells, fid


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

# Record types that live inside cells and worldspaces. Overriding any of them (or the CELL/WRLD
# parents they force) is what made 1.0.0-1.0.2 conflict with every mod that edits the tomb; the build
# now refuses to write a plugin that overrides one of a master's.
WORLD_TYPES = {b"CELL", b"WRLD", b"REFR", b"ACHR", b"PGRE", b"PMIS", b"PHZD", b"PARW", b"PBAR",
               b"PBEA", b"PCON", b"PFLA", b"NAVM", b"LAND"}


def walk_output(blob: bytes, n_masters: int):
    """(records + groups in the blob, [world-type records that belong to a master])."""
    total, bad, i = 0, [], 0
    while i + 24 <= len(blob):
        typ = blob[i:i + 4]
        size = struct.unpack_from("<I", blob, i + 4)[0]
        total += 1
        if typ == b"GRUP":
            n, b2 = walk_output(blob[i + 24:i + size], n_masters)
            total += n; bad += b2
            i += size
            continue
        fid = struct.unpack_from("<I", blob, i + 12)[0]
        if typ in WORLD_TYPES and (fid >> 24) < n_masters:
            bad.append(f"{typ.decode()} 0x{fid:08X}")
        i += 24 + size
    return total, bad


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

    cobj_last = fid - 1                  # remembered before the tomb records take ids
    blob = b"".join(records)
    cobj_group = (b"GRUP" + struct.pack("<I", len(blob) + 24) + b"COBJ" +
                  struct.pack("<i", 0) + struct.pack("<I", 0) + struct.pack("<HH", 0, 0) + blob)

    check_tomb_facts(SKYRIM_ESM)
    check_script_constants()
    top, achr, achr_fid, fid = build_placement(fid, SKYRIM_ESM)
    print(f"  Ysgramor (ACHR 0x{achr_fid:08X}) waits disabled in the mod's holding cell, posed by vanilla's "
          f"own ragdoll data, wearing the four pieces (no cloak)")

    # the draugr-primary armatures, and the two edits to the mod's own records that carry them
    draugr_arma, fid = build_draugr_armatures(rest, fid)
    if fid > 0xFFF:
        raise SystemExit(f"form ids would reach 0x{fid:X}, past the ESL range")
    rest, armas, armos = add_draugr_race(rest, draugr_arma)
    if armos != len(draugr_arma):
        raise SystemExit(f"attached {armos} armatures but built {len(draugr_arma)}")

    quest_group, cell_group, fid = build_tomb_quest(fid, achr, achr_fid)
    if fid > 0xFFF:
        raise SystemExit(f"form ids would reach 0x{fid:X}, past the ESL range")
    print(f"  QUST AR_YsgramorTombQuest + CELL AR_YsgramorHoldingCell: the quest opens the tomb at run time "
          f"(lid REFR 0x{LID_REF:08X}, cage REFR 0x{CAGE_REF:08X}) once C06 stage {C06_DONE_STAGE} is done")

    body_out = rest + cobj_group + top + quest_group + cell_group
    total, overrides = walk_output(body_out, n_masters=4)
    if overrides:
        raise SystemExit("the plugin would override vanilla placed/world records: " + ", ".join(overrides))

    # the two header fields that must change: the count (records AND groups, as the source's own 17
    # = 13 records + 4 groups shows) and the next object id
    new_tes4_body = bytearray(tes4_body)
    struct.pack_into("<fiI", new_tes4_body, hedr_at, version, total, fid)
    new_tes4 = record(b"TES4", 0, bytes(new_tes4_body), flags=tes4_flags)

    out = new_tes4 + body_out
    with open(dst, "wb") as f:
        f.write(out)

    print(f"  added {len(records)} COBJ records at 0x{0x04000000 | next_id:08X}"
          f"-0x{0x04000000 | cobj_last:08X}")
    print(f"  header: {num_records} -> {total} records and groups, "
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
