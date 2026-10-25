ScriptName YsgramorsArmorTombQuest Extends Quest
{Ysgramor's Armor addon - opens Ysgramor's sarcophagus once Glory of the Dead is complete.

 The plugin overrides no cell, worldspace or placed reference of the game (1.0.2; 1.0.1 overrode
 the tomb cell and two of its references, so any mod that edits the tomb conflicted with it). The
 tomb is changed at run time instead, by this script on a small start-game-enabled quest of the
 mod's own:

   * Ysgramor's body is a reference of this mod, kept disabled in a holding cell of its own. When
     the quest is complete it is moved into the sarcophagus (once) and enabled.
   * The sarcophagus lid and one bridge cage piece are vanilla references that are not persistent,
     so they exist in memory only while the tomb is loaded. Whenever the player is in the tomb and
     the quest is complete, they are disabled (with a fade). The game keeps that in the save, and
     the tomb's encounter zone never resets.

 The check is a single update every few seconds: is Glory of the Dead complete (stage 200, the
 stage that completes it, or the completed flag - console completequest sets only the flag), and
 is the player in the tomb. It covers every way the state can arrive: the quest finishing while
 the player stands in the tomb, a save made after it finished, and the mod installed on a save that
 finished it long ago.}

Quest Property GloryOfTheDead Auto
{C06, Glory of the Dead (Skyrim.esm).}

Cell Property YsgramorsTomb Auto
{YsgramorsTomb01 (Skyrim.esm) - the tomb's one interior cell.}

ObjectReference Property SarcophagusBottom Auto
{NorSarcophagusBottom in the tomb (Skyrim.esm) - a PERSISTENT reference, so it can always be
 reached; the body is moved to it.}

Actor Property YsgramorBody Auto
{The mod's own Ysgramor corpse, starts dead and disabled in the mod's holding cell.}

Int Property LidFormID Auto
{The sarcophagus lid (NorSarcophagusTop) - a temporary reference, looked up only while loaded.}

Int Property CageFormID Auto
{The bridge cage piece (NorBridgeCageMid01) - likewise.}

Float Property PollSeconds = 5.0 AutoReadOnly

; Where the body lies, in the tomb's own coordinates: vanilla's corpse-in-sarcophagus offset, read
; from Skyrim.esm by the generator (Add-YsgramorsArmorRecipes.py, CORPSE_POS / CORPSE_ROTZ).
Float Property BodyX = 909.66 AutoReadOnly
Float Property BodyY = -362.16 AutoReadOnly
Float Property BodyZ = -1310.44 AutoReadOnly
Float Property BodyAngleZ = 107.67 AutoReadOnly

Bool BodyPlaced = False

Bool Function QuestComplete()
    If GloryOfTheDead == None
        Return False
    EndIf
    Return GloryOfTheDead.IsCompleted() || GloryOfTheDead.GetStageDone(200)
EndFunction

Function PlaceBody()
    If BodyPlaced || YsgramorBody == None || SarcophagusBottom == None
        Return
    EndIf
    YsgramorBody.MoveTo(SarcophagusBottom)
    YsgramorBody.SetPosition(BodyX, BodyY, BodyZ)
    YsgramorBody.SetAngle(0.0, 0.0, BodyAngleZ)
    YsgramorBody.Enable()
    BodyPlaced = True
    Debug.Trace("YsgramorsArmorTombQuest: Ysgramor laid in his sarcophagus")
EndFunction

Function Remove(Int formID)
    ObjectReference ref = Game.GetForm(formID) as ObjectReference
    If ref != None && !ref.IsDisabled()
        ref.Disable(True)
        Debug.Trace("YsgramorsArmorTombQuest: disabled tomb reference " + formID)
    EndIf
EndFunction

Function Check()
    If QuestComplete()
        PlaceBody()
        If Game.GetPlayer().GetParentCell() == YsgramorsTomb
            Remove(LidFormID)
            Remove(CageFormID)
        EndIf
    EndIf
EndFunction

Event OnInit()
    RegisterForSingleUpdate(1.0)
EndEvent

Event OnUpdate()
    Check()
    RegisterForSingleUpdate(PollSeconds)
EndEvent
