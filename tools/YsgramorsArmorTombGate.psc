ScriptName YsgramorsArmorTombGate Extends ObjectReference
{Ysgramor's Armor addon - the switch that opens Ysgramor's sarcophagus.

 This script sits on an XMarker that starts disabled. The sarcophagus lid and the bridge cage
 piece are enable-parented to the marker with "opposite of parent", and Ysgramor's body is
 enable-parented to it normally. Enabling the marker once removes the lid and the cage and reveals
 the body, and the game keeps that state in the save. Removing the plugin removes the marker, and
 every vanilla reference returns to its vanilla state.

 The marker is enabled when Glory of the Dead (C06) is complete. No vanilla reference changes
 state permanently at that moment (Kodlak's ghost is disabled again after his farewell), so the
 check is made here: once at first load, and then only while the tomb's cell is attached, every
 few seconds, until it fires. After that nothing runs again.}

Quest Property GloryOfTheDead Auto
{C06, Glory of the Dead. The tomb opens once this quest is complete.}

Float Property PollSeconds = 5.0 Auto
{How often to re-check while the player is in the tomb and the quest is not yet complete.}

Bool Function QuestComplete()
    If GloryOfTheDead == None
        Return False
    EndIf
    Return GloryOfTheDead.IsCompleted() || GloryOfTheDead.GetStageDone(200)
EndFunction

Function OpenIfDue()
    If Self.IsDisabled() && QuestComplete()
        Self.Enable(True)
    EndIf
EndFunction

Function Watch()
    If Self.IsDisabled()
        RegisterForSingleUpdate(PollSeconds)
    EndIf
EndFunction

Event OnInit()
    OpenIfDue()
    Watch()
EndEvent

Event OnCellAttach()
    OpenIfDue()
    Watch()
EndEvent

Event OnCellDetach()
    UnregisterForUpdate()
EndEvent

Event OnUpdate()
    OpenIfDue()
    Cell here = Self.GetParentCell()
    If Self.IsDisabled() && here != None && here.IsAttached()
        RegisterForSingleUpdate(PollSeconds)
    EndIf
EndEvent
