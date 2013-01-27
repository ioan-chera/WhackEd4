#!/usr/bin/env python
#coding=utf8

from collections import OrderedDict
from whacked4 import config, utils
from whacked4.dehacked import statefilter
from whacked4.ui import editormixin, windows
from whacked4.ui.dialogs import spritesdialog
import copy
import wx


class StatesFrame(editormixin.EditorMixin, windows.StatesFrameBase):
    """
    States editor window.
    """
    
    # Maps window ids to state property keys.
    PROPS_STATE = {
        windows.STATES_DURATION: 'duration',
        windows.STATES_NEXT: 'nextState',
        windows.STATES_PARM1: 'parameter1',
        windows.STATES_PARM2: 'parameter2',
        windows.STATES_SPRITE: 'sprite'
    }
        
    # The colours used for color-coding sprite indices.
    SPRITE_COLOURS = [
        wx.Colour(red=255, green=48, blue=0),
        wx.Colour(red=255, green=255, blue=255),
    ]
    
    # Doom lit flag. Frame indices with this flag set are always lit by Doom's rendering engine.
    FRAMEFLAG_LIT = 0x8000
    
    
    def __init__(self, params):
        windows.StatesFrameBase.__init__(self, params)
        editormixin.EditorMixin.__init__(self)
        
        self.SetIcon(wx.Icon('res/editor-states.ico'))
                
        # A list of all tool windows for simple mass operations.
        self.WINDOWS_TOOLS = [
            self.SpriteIndex,
            self.SpriteSelect,
            self.FrameIndex,
            self.FrameIndexSpinner,
            self.AlwaysLit,
            self.NextStateIndex,
            self.Duration,
            self.Action,
            self.Parameter1,
            self.Parameter2,
            self.Restore,
            self.NextStateName,
            self.SpriteName
        ]
        
        # Mix sprite color coding colours with the default system colours.
        self.mix_colours()


    def build(self, patch):
        """
        @see: EditorMixin.build
        """
        
        self.patch = patch
        self.pwads = self.GetParent().pwads
        self.clipboard = None

        self.sprites_dialog = spritesdialog.SpritesDialog(self.GetParent())
        
        # Setup sprite preview control.
        self.SpritePreview.set_source(self.pwads)
        self.SpritePreview.set_baseline_factor(0.9)
                
        # List of selected list indices.
        self.selected = []
        
        # Initialize filter.
        self.filter = statefilter.StateFilter(patch)
        self.build_filterlist()
        self.filter_update(0)
        
        self.build_statelist()
        self.build_actionlist()
                
        
    def mix_colours(self):
        """
        Mixes sprite index colour coding with the system's window background color.
        """
        
        sys_colour = self.StateList.GetBackgroundColour()
        for index, colour in enumerate(self.SPRITE_COLOURS):
            self.SPRITE_COLOURS[index] = utils.mix_colours(colour, sys_colour, 0.92)
            
        
    def undo_restore_item(self, item):
        """
        @see: EditorMixin.undo_restore_item
        """
        
        for state_index, state in item.iteritems():
            self.patch.states[state_index] = state

            # Restore all state indices in the undo item.            
            if state_index in self.filter.state_indices:
                list_index = self.filter.state_indices.index(state_index)
                self.filter.states[list_index] = state
                self.update_row(list_index)
        
        self.tools_update()
        self.update_sprite_preview()
        
        
    def undo_store_item(self):
        """
        @see: EditorMixin.undo_store_item
        """
        
        # Store all currently selected states.
        items = OrderedDict()
        for list_index in self.selected:
            state_index = self.filter.state_indices[list_index]
            state = copy.deepcopy(self.filter.states[list_index])
            
            items[state_index] = state
            
        return items
            
    
    def edit_copy(self):
        """
        Copies all currently selected states to the clipboard.
        
        The states are stored in sequence, without non-selected states in between.
        """
        
        self.clipboard = []
        
        for list_index in self.selected:
            dup = copy.deepcopy(self.filter.states[list_index])
            self.clipboard.append(dup)
        
        
    def edit_paste(self):
        """
        Pastes the current clipboard, starting at the first selected state.
        """
        
        if self.clipboard is None:
            return
        if len(self.selected) == 0:
            return
        
        # Do not paste over state 0.
        list_index = self.selected[0]
        if self.filter.state_indices[list_index] == 0:
            return
        
        self.undo_add()
         
        for state in self.clipboard:
            # Ignore states that are not currently visible because of filters.
            if list_index in self.selected:
                dup = copy.deepcopy(state)
                state_index = self.filter.state_indices[list_index]
                self.patch.states[state_index] = dup
                self.update_row(list_index)
            
            list_index += 1
            if list_index >= len(self.patch.states):
                break
        
        self.tools_update()
        self.is_modified(True)
    
    
    def tools_set_state(self, enabled):
        """
        Sets the state of all tool controls.
        """
        
        for window in self.WINDOWS_TOOLS:
            window.Enable(enabled)
                
                
    def state_restore(self, event):
        """
        Restores all currently selected states to the way they are in the engine configuration.
        """
        
        self.undo_add()
        
        for list_index in self.selected:
            state_index = self.filter.state_indices[list_index]
            self.patch.states[state_index] = copy.deepcopy(self.patch.engine.states[state_index])
            self.filter.states[list_index] = self.patch.states[state_index]
        
        self.tools_update()
        self.update_selected_rows()
        self.update_colours()
        self.is_modified(True)
        
    
    def state_link(self, event):
        """
        Connects the currently selected state's next state property to the state being clicked, while the alt key
        is held down.
        """
        
        # Set the current state's next state if the alt key is held down.
        connect = wx.GetKeyState(wx.WXK_ALT)
        if connect == True:
            x = event.GetX()
            y = event.GetY()
            list_index = self.StateList.HitTest(wx.Point(x, y))[0]
            if list_index == wx.NOT_FOUND:
                return
            
            state_index = self.filter.state_indices[list_index]
            self.NextStateIndex.ChangeValue(str(state_index))
            self.set_selected_property('nextState', state_index)
            self.update_selected_rows()
        
        else:
            event.Skip()
            

    def build_filterlist(self):
        """
        Build the list of available filters.
        """
        
        list_items = []
        for filter_data in self.filter.filters:
            list_items.append(filter_data['name'])
        self.Filter.SetItems(list_items)
                
        self.Filter.Select(0)
    
            
    def build_actionlist(self):
        """
        Builds the list of available state actions.
        """
        
        action_items = []
        
        if self.patch.engine.extended == True:
            for name in self.patch.engine.actions.iterkeys():
                if name == 'NULL':
                    name = ''
                action_items.append(name)
        
        else:
            for action in self.patch.engine.actions.itervalues():
                if action['name'] == 'NULL':
                    action_items.append('')
                else:
                    action_items.append(action['name'])
                    
        self.Action.SetItems(action_items)
        
        
    def build_statelist(self):
        """
        Builds the list of currently filtered states.
        """
        
        wx.BeginBusyCursor()
        
        self.StateList.Freeze()
        self.StateList.ClearAll()
        self.selected = []
        
        # Add list column headers if needed.
        if self.StateList.GetColumnCount() == 0:
            self.StateList.InsertColumn(0, '', width=29)
            self.StateList.InsertColumn(1, 'Name', width=47)
            self.StateList.InsertColumn(2, 'Spr', width=33)
            self.StateList.InsertColumn(3, 'Frm', width=34)
            self.StateList.InsertColumn(4, 'Lit', width=25)
            self.StateList.InsertColumn(5, 'Next', width=36)
            self.StateList.InsertColumn(6, 'Dur', width=40)
            self.StateList.InsertColumn(7, 'Action', width=103)
            self.StateList.InsertColumn(8, 'Parameters', width=77)
        
        # Add all items in the filtered list.
        list_index = 0
        for state_index in self.filter.state_indices:
            self.StateList.InsertStringItem(list_index, str(state_index))
            self.StateList.SetItemFont(list_index, config.FONT_MONOSPACED)
            
            self.update_row(list_index)
            
            list_index += 1
        
        self.update_colours()
        
        # Select the first row if it is not state 0.
        if self.filter.state_indices[0] == 0 and len(self.filter.state_indices) > 1:
            self.StateList.Select(1, True)
        elif len(self.filter.state_indices) > 0:
            self.StateList.Select(0, True)
            
        self.StateList.Thaw()
        
        wx.EndBusyCursor()
        
        
    def filter_update(self, index):
        """
        Updates the current state filter and rebuilds the state list accordingly.
        """
        
        self.filter.update(index)
        self.build_statelist()
        self.tools_update()
        
    
    def set_selected_property(self, key, value):
        """
        Sets a property of all currently selected states.
        
        @param key: the state property key to set.
        @param value: the new value of the state property.  
        """
        
        self.undo_add()
        
        for list_index in self.selected:
            state_index = self.filter.state_indices[list_index]
            if state_index == 0:
                continue
            
            state = self.filter.states[list_index]
            state[key] = value
            self.is_modified(True)
        
        
    def update_selected_rows(self):
        """
        Updates the contents of every selecte state list row.
        """
        
        for list_index in self.selected:
            self.update_row(list_index)


    def tools_update(self):
        """
        Updates the tool controls with the properties of the currently selected state(s).
        """
        
        # If only one state is selected, fill the tools with that state's properties.
        if len(self.selected) == 1:
            state = self.filter.states[self.selected[0]]
            state_index = self.filter.state_indices[self.selected[0]] 
            
            if state_index == 0:
                sprite_name = '-'
            else:
                sprite_name = self.patch.sprite_names[state['sprite']]
            sprite_frame = state['spriteFrame'] & ~self.FRAMEFLAG_LIT
            
            self.SpriteIndex.ChangeValue(str(state['sprite']))
            self.SpriteName.SetLabel(sprite_name)
            self.FrameIndex.ChangeValue(str(sprite_frame))
            self.NextStateIndex.ChangeValue(str(state['nextState']))
            self.NextStateName.SetLabel(self.patch.get_state_name(state['nextState']))
            self.Duration.ChangeValue(str(state['duration']))
            self.Parameter1.ChangeValue(str(state['parameter1']))
            self.Parameter2.ChangeValue(str(state['parameter2']))
            
            self.set_selected_action(state['action'])
            
            if state['spriteFrame'] & self.FRAMEFLAG_LIT != 0:
                self.AlwaysLit.SetValue(True)
            else:
                self.AlwaysLit.SetValue(False)
            
            # Do not allow state 0 to be edited.
            if state_index == 0:
                self.tools_set_state(False)
            else:
                self.tools_set_state(True)
            
            # Do not allow editing an action on a state that has none for non-extended patches.
            if self.patch.engine.extended == False:
                if state['action'] == 0:
                    self.Action.Disable()
                else:
                    self.Action.Enable()

        # If multiple states are selected, empty out all tools.
        else:
            self.SpriteIndex.ChangeValue('')
            self.SpriteName.SetLabel('')
            self.FrameIndex.ChangeValue('')
            self.NextStateIndex.ChangeValue('')
            self.NextStateName.SetLabel('')
            self.Duration.ChangeValue('')
            self.Action.Select(0)
            self.Parameter1.ChangeValue('')
            self.Parameter2.ChangeValue('')
            self.AlwaysLit.SetValue(False)
            self.Action.Enable()
            self.tools_set_state(True)
        
        self.update_sprite_preview()
        
        
    def update_sprite_preview(self):
        """
        Updates the sprite preview control with the currently selected state's sprite.
        """
        
        if len(self.selected) == 1:
            state_index = self.filter.state_indices[self.selected[0]]
            
            # Find a valid sprite name and frame index.
            if state_index != 0:
                sprite_index = self.SpriteIndex.GetValue()
                if sprite_index != '':
                    sprite_index = int(sprite_index)
                    sprite_name = self.patch.sprite_names[sprite_index]
                        
                    sprite_frame = self.FrameIndex.GetValue()
                    if sprite_frame != '':
                        sprite_frame = int(sprite_frame)
                    else:
                        sprite_frame = 0
                    
                    self.SpritePreview.show_sprite(sprite_name, sprite_frame)
                    return
        
        self.SpritePreview.clear()
                
    
    def select_sprite(self, event):
        """
        Shows the sprite select dialog to replace the currently selected state's sprites.
        """
        
        # Only use the first selected state's sprite as the default selected value.
        if len(self.selected) == 1:
            sprite_index = int(self.SpriteIndex.GetValue())
            frame_index = int(self.FrameIndex.GetValue())
            
        elif len(self.selected) > 1:
            state = self.filter.states[self.selected[0]]
            sprite_index = state['sprite']
            frame_index = None
            
        self.sprites_dialog.set_state(self.patch, self.pwads, sprite_index=sprite_index, frame_index=frame_index)
        self.sprites_dialog.ShowModal()
        
        if self.sprites_dialog.selected_sprite != -1:
            sprite_index = self.sprites_dialog.selected_sprite
            frame_index = self.sprites_dialog.selected_frame
            
            self.SpriteIndex.ChangeValue(str(sprite_index))
            self.set_selected_property('sprite', sprite_index)
            
            # Change the frame index if it was altered.
            if frame_index != -1:
                self.FrameIndex.ChangeValue(str(frame_index))
                
                # Update sprite frames separately to mix in lit flag.
                for list_index in self.selected:
                    state = self.filter.states[list_index]
                    state['spriteFrame'] = frame_index | (state['spriteFrame'] & self.FRAMEFLAG_LIT)
            
            self.update_selected_rows()
            self.update_colours()
            self.update_sprite_preview()
    
    
    def set_value(self, event):
        """
        Validates and sets a property of all currently selected states. 
        """
                
        window_id = event.GetId() 
        window = self.FindWindowById(window_id)
        value = utils.validate_numeric(window)
        
        # Clamp sprite index and update sprite name.
        if window_id == windows.STATES_SPRITE:
            if value < 0:
                value = 0
            elif value >= len(self.patch.sprite_names):
                value = len(self.patch.sprite_names) - 1
            self.SpriteName.SetLabel(self.patch.sprite_names[value])
            window.ChangeValue(str(value))
        
        # Clamp next state index and update state name.
        elif window_id == windows.STATES_NEXT:
            if value < 0:
                value = 0
            elif value >= len(self.patch.states):
                value = len(self.patch.states) - 1
            self.NextStateName.SetLabel(self.patch.get_state_name(value))
            window.ChangeValue(str(value))
            
        # Clamp duration.
        elif window_id == windows.STATES_DURATION:
            if value < -1:
                value = 0
            window.ChangeValue(str(value))

        key = self.PROPS_STATE[window_id]
        self.set_selected_property(key, value)
        
        self.update_selected_rows()
        self.update_sprite_preview()
        self.is_modified(True)
        
        # Update sprite index colour coding.
        if window_id == windows.STATES_SPRITE:
            self.update_colours()
        

    def set_lit(self, event):
        """
        Sets the lit property of all currently selected states.
        """
        
        self.undo_add()
        
        checked = self.AlwaysLit.GetValue()
         
        for list_index in self.selected:
            state = self.filter.states[list_index]
            
            # Remove lit flag, then set it only if it needs to be.
            frame_index = state['spriteFrame'] & ~self.FRAMEFLAG_LIT
            if checked == True:
                frame_index |= self.FRAMEFLAG_LIT
            
            state['spriteFrame'] = frame_index
    
        self.update_selected_rows()
        self.is_modified(True)
        
    
    def set_action(self, event):
        """
        Sets the action property of all currently selected states.
        """
        
        self.undo_add()
        
        value = self.Action.GetStringSelection()
        action_value = self.get_action_value_from_name(value)
        
        for list_index in self.selected:
            state = self.filter.states[list_index]
            
            # Only allow modifying a state's action if the engine is extended, or if the state already has an action.
            if self.patch.engine.extended == True or state['action'] != 0:
                state['action'] = action_value
            
        self.update_selected_rows()
        self.is_modified(True)
            
    
    def set_frame(self, event):
        """
        Sets the frame index property of all currently selected states.
        """
        
        self.undo_add()
        
        window = self.FindWindowById(event.GetId())
        value = utils.validate_numeric(window)
        
        # Clamp to a valid index.
        if value < 0:
            value = 0
        elif value > config.MAX_SPRITE_FRAME:
            value = config.MAX_SPRITE_FRAME
        
        if window.GetValue() != str(value):
            window.ChangeValue(str(value))
        
        # Manually update all selected states so that the lit frame index flag can be retained.
        for list_index in self.selected:
            state = self.filter.states[list_index]
            state['spriteFrame'] = value | (state['spriteFrame'] & self.FRAMEFLAG_LIT)
            
        self.update_selected_rows()
        self.update_sprite_preview()
        self.is_modified(True)
        
        
    def get_action_value_from_name(self, action_name):
        """
        Returns an action value for an action name.
        
        'NULL'\0 is displayed as an empty string. Other action values depend on the type of patch.
        """
        
        if action_name == '':
            if self.patch.engine.extended == True:
                return 'NULL'
            else:
                return 0
        
        return self.patch.engine.get_action_from_name(action_name)
    
    
    def get_action_name_from_value(self, action_value):
        """
        Returns an action name for an action value.
        
        'NULL'\0 is displayed as an empty string. Other action names depend on the type of patch.
        """
        
        if self.patch.engine.extended == True:
            if action_value == 'NULL':
                return ''
            else:
                return str(action_value)
            
        else:
            if action_value == 0:
                return ''
            else:
                return self.patch.engine.actions[str(action_value)]['name']
        
        return None
    
    
    def set_selected_action(self, action_value):
        """
        Sets the action choice box' index to reflect the specified action value.
        """
        
        action_name = self.get_action_name_from_value(action_value)
        for index in range(self.Action.GetCount()):
            if self.Action.GetString(index) == action_name:
                self.Action.Select(index)
                return 
        
    
    def update_row(self, list_index):
        """
        Updates the list row with information of the state that it displays.
        """
        
        state_index = self.filter.state_indices[list_index]
        state = self.filter.states[list_index]

        if (state['spriteFrame'] & self.FRAMEFLAG_LIT) != 0:
            lit = 'X'
        else:
            lit = ''
        parameters = str(state['parameter1']) + ', ' + str(state['parameter2'])
        action = self.get_action_name_from_value(state['action'])
        
        # Fill out column strings.
        self.StateList.SetStringItem(list_index, 1, self.patch.get_state_name(state_index))
        self.StateList.SetStringItem(list_index, 2, str(state['sprite']))
        self.StateList.SetStringItem(list_index, 3, str(state['spriteFrame'] & ~self.FRAMEFLAG_LIT))
        self.StateList.SetStringItem(list_index, 4, lit)
        self.StateList.SetStringItem(list_index, 5, str(state['nextState']))
        self.StateList.SetStringItem(list_index, 6, str(state['duration']))
        self.StateList.SetStringItem(list_index, 7, action)
        self.StateList.SetStringItem(list_index, 8, parameters)
    
    
    def update_colours(self):
        """
        Updates all the state list row background colours.
        
        State list rows are colour-coded by their sprite index.
        """
        
        self.StateList.Freeze()
        
        colour_index = 0
        previous_sprite = 0
        list_index = 0
        for state in self.filter.states:
            # Advance in the colour list.
            if state['sprite'] != previous_sprite:
                colour_index += 1
                if colour_index == len(self.SPRITE_COLOURS):
                    colour_index = 0
            
            self.StateList.SetItemBackgroundColour(list_index, self.SPRITE_COLOURS[colour_index])
            
            list_index += 1
            previous_sprite = state['sprite']
            
        self.StateList.Thaw()
    
    
    def selection_clear(self):
        """
        Clears the list of selected states.
        """
        
        self.StateList.Freeze()
        
        for list_index in self.selected:
            self.StateList.Select(list_index, False)    
        
        self.StateList.Thaw()
        
        
    def selection_get_state_index(self):
        """
        Returns the first selected state index.
        """
        
        return self.filter.state_indices[self.selected[0]]
    
    
    def frame_set(self, modifier):
        """
        Modifies the state frame index value by a specified amount.
        """ 
        
        if self.FrameIndex.GetValue() == '':
            self.FrameIndex.SetValue('0')
        else:    
            index = int(self.FrameIndex.GetValue())
            self.FrameIndex.SetValue(str(index + modifier))
    
        
    def goto_next_state(self, event):
        """
        Select the currently selected state's next state.
        """
        
        if len(self.selected) == 0:
            return
        
        state = self.filter.states[self.selected[0]]
        self.goto_state_index(state['nextState'])
        
    
    def goto_state_index(self, state_index, filter_type=None, filter_index=None):
        """
        Selects a state and applies a filter.
        
        @param state_index: the index of the state to select.
        @param filter_type: the type of filter to enable. @see dehacked.statefilter.
        @param filter_index: the index of the item to filter for. @see dehacked.statefilter.  
        """
        
        # Enable the specified filter.
        if filter_type is not None:
            index = self.filter.find_index(filter_type, filter_index)
            self.filter_update(index)
            self.Filter.Select(index)
            
        # Disable all filtering otherwise.
        else:
            if not state_index in self.filter.state_indices:
                self.filter_update(0)
                self.Filter.Select(0)
            
        filter_index = self.filter.state_indices.index(state_index)
        
        # Select only the specified state and make sure it is visible.
        self.selection_clear()
        self.StateList.Select(filter_index, True)
        self.StateList.EnsureVisible(filter_index)
        self.StateList.SetFocus()
        
    
    def state_select(self, event):
        self.selected.append(event.GetIndex())
        self.tools_update()
            
    def state_deselect(self, event):
        self.selected.remove(event.GetIndex())
        self.tools_update()
    
    def filter_select(self, event):
        self.filter_update(self.Filter.GetSelection())
        
    def frame_spin_up(self, event):
        self.frame_set(1)
        
    def frame_spin_down(self, event):
        self.frame_set(-1)