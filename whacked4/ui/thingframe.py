#!/usr/bin/env python
#coding=utf8

from dehacked import statefilter
from ui import windows, utils, editormixin
import copy
import wx


class ThingFrame(editormixin.EditorMixin, windows.ThingFrameBase):
    """
    Things editor window.
    """
    
    # Text control to internal key mappings.
    PROPS_VALUES = {
        windows.THING_VAL_ID: 'id',
        windows.THING_VAL_HEALTH: 'health',
        windows.THING_VAL_SPEED: 'speed',
        windows.THING_VAL_RADIUS: 'radius',
        windows.THING_VAL_HEIGHT: 'height',
        windows.THING_VAL_DAMAGE: 'damage',
        windows.THING_VAL_REACTIONTIME: 'reactionTime',
        windows.THING_VAL_PAINCHANCE: 'painChance',
        windows.THING_VAL_MASS: 'mass'
    }
    
    # State text control to partial internal key mappings.
    PROPS_STATES = {
        windows.THING_STATE_SPAWN: 'Spawn',
        windows.THING_STATE_WALK: 'Walk',
        windows.THING_STATE_PAIN: 'Pain',
        windows.THING_STATE_MELEE: 'Melee',
        windows.THING_STATE_ATTACK: 'Attack',
        windows.THING_STATE_DEATH: 'Death',
        windows.THING_STATE_EXPLODE: 'Explode',
        windows.THING_STATE_RAISE: 'Raise'
    }
    
    # State name label to partial internal key mappings.
    PROPS_STATENAMES = {
        windows.THING_STATENAME_SPAWN: 'Spawn',
        windows.THING_STATENAME_WALK: 'Walk',
        windows.THING_STATENAME_PAIN: 'Pain',
        windows.THING_STATENAME_MELEE: 'Melee',
        windows.THING_STATENAME_ATTACK: 'Attack',
        windows.THING_STATENAME_DEATH: 'Death',
        windows.THING_STATENAME_EXPLODE: 'Explode',
        windows.THING_STATENAME_RAISE: 'Raise'
    }
    
    # State set button to partial internal key mappings.
    PROPS_STATESET = {
        windows.THING_STATESET_SPAWN: windows.THING_STATE_SPAWN,
        windows.THING_STATESET_WALK: windows.THING_STATE_WALK,
        windows.THING_STATESET_PAIN: windows.THING_STATE_PAIN,
        windows.THING_STATESET_MELEE: windows.THING_STATE_MELEE,
        windows.THING_STATESET_ATTACK: windows.THING_STATE_ATTACK,
        windows.THING_STATESET_DEATH: windows.THING_STATE_DEATH,
        windows.THING_STATESET_EXPLODE: windows.THING_STATE_EXPLODE,
        windows.THING_STATESET_RAISE: windows.THING_STATE_RAISE
    }

    # Sound text control to partial internal key mappings.
    PROPS_SOUNDS = {
        windows.THING_SOUND_ALERT: 'Alert',
        windows.THING_SOUND_ATTACK: 'Attack',
        windows.THING_SOUND_PAIN: 'Pain',
        windows.THING_SOUND_DEATH: 'Death',
        windows.THING_SOUND_ACTIVE: 'Active'
    }
    
    # Fixed point unit divisor for certain thing properties.
    FIXED_UNIT = 0x10000
    
    # Doom missile thing flag.
    FLAG_MISSILE = 0x10000
    

    def __init__(self, params):
        windows.ThingFrameBase.__init__(self, params)
        editormixin.EditorMixin.__init__(self)
        
        self.SetIcon(wx.Icon('res/icon-weapons-small.png'))
        
        
    def build(self, patch):
        """
        @see EditorMixin.build
        """
        
        self.patch = patch
        self.clipboard = None
        
        self.selected_index = 0
        
        self.flaglist_build()
        self.thinglist_build()
        
        
    def thinglist_build(self):
        """
        Builds the thing names list from scratch.
        """
        
        self.ThingList.SetItems(self.patch.things.names)
        self.ThingList.SetSelection(0, True)
        
        
    def flaglist_build(self):
        """
        Build the flags list from scratch.
        """
        
        flaglist = []
        for data in self.patch.engine.things.flags.itervalues():
            flaglist.append(' ' + data['name'])
        self.ThingFlags.SetItems(flaglist)
        
    
    def activate(self, event):
        """
        Called when this editor window is activated by the user.
        """
        
        # Call the editor mixin function that we are overriding.
        editormixin.EditorMixin.activate(self, event)
        
        if self.IsBeingDeleted():
            return
        
        # Update the properties being displayed by this window, in case state or sound names have changed.
        self.update_properties()
            
            
    def edit_copy(self):
        """
        Copies the currently selected thing to this windows' clipboard.
        """
        
        self.clipboard = {
            'thing': copy.deepcopy(self.patch.things[self.selected_index]),
            'name': copy.copy(self.patch.things.names[self.selected_index])
        }
        
        
    def edit_paste(self):
        """
        Pastes the thing on this windows' clipboard over the currently selected thing.
        """
        
        if self.clipboard is None:
            return
        
        self.undo_add()
        
        dup = copy.deepcopy(self.clipboard['thing'])
        dup_name = copy.copy(self.clipboard['name'])
        
        # Copy references to newly duplicated thing.
        self.patch.things[self.selected_index] = dup
        self.patch.things.names[self.selected_index] = dup_name
        
        self.update_properties()
        self.is_modified(True)

    
    def update_properties(self):
        """
        Update the visible properties of the currently selected thing.
        """
        
        thing = self.patch.things[self.selected_index]
        thing_name = self.patch.things.names[self.selected_index]
        
        # Set basic property text control values.
        self.ThingId.ChangeValue(str(thing['id']))
        self.ThingHealth.ChangeValue(str(thing['health']))
        self.ThingRadius.ChangeValue(str(thing['radius'] / self.FIXED_UNIT))
        self.ThingHeight.ChangeValue(str(thing['height'] / self.FIXED_UNIT))
        self.ThingDamage.ChangeValue(str(thing['damage']))
        self.ThingReactionTime.ChangeValue(str(thing['reactionTime']))
        self.ThingPainChance.ChangeValue(str(thing['painChance']))
        self.ThingMass.ChangeValue(str(thing['mass']))
        
        # Speed is in fixed point if this thing is a missile, normal otherwise
        if (thing['flags'] & self.FLAG_MISSILE) != 0:
            speed = thing['speed'] / self.FIXED_UNIT
        else:
            speed = thing['speed']
        self.ThingSpeed.ChangeValue(str(speed))
        
        # Set flags.
        flags = thing['flags']
        bits = 1
        for flag in range(len(self.patch.engine.things.flags)):
            self.ThingFlags.Check(flag, (flags & bits != 0))
            bits *= 2
        
        # Set state and sound values.
        for name in self.PROPS_STATES.values():
            self.set_display_state(name)
        for name in self.PROPS_SOUNDS.values():
            self.set_display_sound(name)
            
        # Update name.
        self.ThingList.SetString(self.selected_index, thing_name)
        

    def set_display_state(self, state_name):
        """
        Sets state control values based on the partial name of a state thing property.
        """
        
        thing = self.patch.things[self.selected_index]
        state_index = thing['state' + state_name]
        self.__dict__['ThingState' + state_name].ChangeValue(str(state_index))
        self.__dict__['ThingState' + state_name + 'Name'].SetLabel(self.patch.get_state_name(state_index))
        
        
    def set_display_sound(self, sound_name):
        """
        Sets sound control values based on the partial name of a sound thing property.
        """
        
        thing = self.patch.things[self.selected_index]
        sound_index = thing['sound' + sound_name]
        self.__dict__['ThingSound' + sound_name].ChangeValue(str(sound_index))
        self.__dict__['ThingSound' + sound_name + 'Name'].SetLabel(self.patch.get_sound_name(sound_index))
        
        
    def set_value(self, event):
        """
        Sets the currently selected thing's property value.
        
        Which thing property to change is determined by the text control's id and the PROPS_VALUES lookup table.
        """
        
        self.undo_add()
        
        window_id = event.GetId()
        window = self.FindWindowById(window_id)
        value = utils.validate_numeric(window)
        
        thing = self.patch.things[self.selected_index]
        
        # Apply fixed point divisor if the value needs it.
        # This is also necessary for the speed property if the thing has it's MISSILE flag set.
        key = self.PROPS_VALUES[window_id]
        if key == 'radius' or key == 'height':
            value *= self.FIXED_UNIT
        elif key == 'speed' and (thing['flags'] & self.FLAG_MISSILE) != 0:
            value *= self.FIXED_UNIT
        
        thing[key] = value
        
        self.is_modified(True)
        
        
    def set_state(self, event):
        """
        Sets the currently selected thing's property value.
        
        Which thing property to change is determined by the text control's id and the PROPS_VALUES lookup table.
        """
        
        self.undo_add()
        
        window_id = event.GetId()
        window = self.FindWindowById(window_id)
        value = utils.validate_numeric(window)

        thing = self.patch.things[self.selected_index]
        
        # Clamp to valid state indices.
        if value < 0:
            value = 0
        if value >= len(self.patch.states):
            value = len(self.patch.states) - 1
            
        if str(value) != window.GetValue():
            window.ChangeValue(str(value))
        
        key = self.PROPS_STATES[window_id]
        thing['state' + key] = value
        self.__dict__['ThingState' + key + 'Name'].SetLabel(self.patch.get_state_name(value))
        self.is_modified(True)
        
        
    def set_sound(self, event):
        """
        Sets the currently selected thing's sound index.
        
        Which sound to change is determined by the text control's id and the PROPS_SOUNDS lookup table.
        """
        
        self.undo_add()
        
        window_id = event.GetId()
        window = self.FindWindowById(window_id)
        value = utils.validate_numeric(window)
        
        thing = self.patch.things[self.selected_index]
        
        # Clamp to valid sound indices.
        if value < 0:
            value = 0
        if value > len(self.patch.sounds):
            value = len(self.patch.sounds)
            
        if str(value) != window.GetValue():
            window.ChangeValue(str(value))
        
        key = self.PROPS_SOUNDS[window_id]
        thing['sound' + key] = value
        self.__dict__['ThingSound' + key + 'Name'].SetLabel(self.patch.get_sound_name(value))
        self.is_modified(True)


    def set_flags(self, event):
        """
        Sets the currently selected thing's flags value.
        """
        
        self.undo_add()
        
        flags_value = 0
        
        # Iterate over the flags defined in the engine config, mark bits if the flag is set in the list.
        bits = 1
        for flag in range(len(self.patch.engine.things.flags)):
            if self.ThingFlags.IsChecked(flag) == True:
                flags_value |= bits
            bits *= 2
            
        self.patch.things[self.selected_index]['flags'] = flags_value
        self.is_modified(True)
        
        
    def set_flag_tooltip(self, event):
        """
        Updates the tooltip displayed for the flags list when hovering over a flag.
        """
        
        index = self.ThingFlags.HitTest(wx.Point(event.GetX(), event.GetY()))
        if index != wx.NOT_FOUND:
            key = self.patch.engine.things.flags.keys()[index]
            tip = self.patch.engine.things.flags[key]['description']
        else:
            tip = ''
        
        self.ThingFlags.SetToolTipString(tip)
    
    
    def set_state_external(self, event):
        """
        Sets a state property based on the state that is currently selected in the states editor.
        """
        
        self.undo_add()
        
        # Get a reference to the states editor window.
        parent = self.GetParent()
        states_frame = parent.editor_windows[windows.MAIN_TOOL_STATES]

        text_ctrl = self.FindWindowById(self.PROPS_STATESET[event.GetId()])
        text_ctrl.SetValue(str(states_frame.selection_get_state_index()))
    
    
    def thing_select(self, event):
        """
        Called when a thing is selected from the thing names list.
        """
        
        self.selected_index = self.ThingList.GetSelection()
        self.update_properties()
    
        
    def thing_rename(self, event):
        """
        Called when the current thing needs to be renamed.
        """
        
        self.thing_rename_action()


    def thing_rename_action(self):
        """
        Renames the currently selected thing.
        """
        
        thing_name = self.patch.things.names[self.selected_index]
        new_name = wx.GetTextFromUser('Enter a new name for ' + thing_name, caption='Change name', default_value=thing_name, parent=self)
        
        if new_name != '':
            self.undo_add()
            
            self.patch.things.names[self.selected_index] = new_name
            self.ThingList.SetString(self.selected_index, new_name)
            
            self.update_properties()
            self.is_modified(True)
            
    
    def thing_restore(self, event):
        """
        Restores the currently selected thing to the one stored in the engine configuration.
        """
        
        self.undo_add()
        
        self.patch.things[self.selected_index] = copy.deepcopy(self.patch.engine.things[self.selected_index])
        self.patch.things.names[self.selected_index] = copy.copy(self.patch.engine.things.names[self.selected_index])
        
        self.update_properties()
        self.is_modified(True)
        
    
    def goto_state(self, event):
        """
        Changes the selected state in the states editor window to the one of a thing's state property.
        """
        
        key = self.PROPS_STATENAMES[event.GetId()]
        state_index = self.patch.things[self.selected_index]['state' + key]
        
        self.goto_state_index(state_index, statefilter.FILTER_TYPE_THING, self.selected_index)
    
    
    def undo_restore_item(self, item):
        """
        @see EditorMixin.undo_restore_item
        """
        
        index = item['index']

        self.patch.things[index] = item['item']
        self.patch.things.names[index] = item['name']
        
        self.ThingList.SetString(index, item['name'])
        self.update_properties()
        
        self.is_modified(True)
        
        
    def undo_store_item(self):
        """
        @see EditorMixin.undo_store_item
        """
        
        return {
            'item': copy.deepcopy(self.patch.things[self.selected_index]),
            'name': copy.copy(self.patch.things.names[self.selected_index]),
            'index': self.selected_index
        }  