ScriptName YsgramorsArmorTombPlayer Extends ReferenceAlias
{Ysgramor's Armor addon - the player alias (alias 0) of AR_YsgramorTombQuest.

 Its one job is the load hook: on every game load it re-arms the quest's poll
 (YsgramorsArmorTombQuest.Arm), so a save written before the poll was first armed - such as an
 autosave made a few seconds after New Game - still opens Ysgramor's tomb once Glory of the Dead
 is complete. Arming is idempotent, so a load while the poll is already running changes nothing.}

Event OnPlayerLoadGame()
    YsgramorsArmorTombQuest tomb = GetOwningQuest() as YsgramorsArmorTombQuest
    If tomb == None
        Debug.Trace("YsgramorsArmorTombPlayer: owning quest is not YsgramorsArmorTombQuest - poll not re-armed")
        Return
    EndIf
    tomb.Arm("game loaded")
EndEvent
