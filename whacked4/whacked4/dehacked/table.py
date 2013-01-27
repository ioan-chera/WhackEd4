#!/usr/bin/env python
#coding=utf8

class Table:
    """
    A table containing Dehacked entry objects.
    """

    def __init__(self, cls):
        self.entries = []
        self.cls = cls
        self.offset = 0
        
        
    def read_from_executable(self, count, f):
        """
        Reads a number of entries from an executable.
        """
        
        for _ in range(count):
            self.entries.append(self.cls().read_from_executable(f))
            
            
    def read_from_json(self, json):
        """
        Reads this table's entries from a JSON object.
        """
        
        for entry in json:
            self.entries.append(self.cls().from_json(entry))
       
        
    def write_patch_data(self, source_table, f, use_filter):
        """
        Writes this table's entry to a Dehacked patch file.
        """
        
        for index in range(len(self.entries)):
            entry = self.entries[index]
            source_entry = source_table.entries[index]
            
            # Write the current entry index if it returns any data to be written.
            patch_str = entry.get_patch_string(source_entry, self, use_filter)
            if patch_str is not None:
                f.write(entry.get_patch_header(index, source_entry, self, offset=self.offset))
                f.write(patch_str)
                
    
    def __getitem__(self, index):
        return self.entries[index]
    
    def __setitem__(self, index, value):
        self.entries[index] = value
    
    def __len__(self):
        return len(self.entries)
    
    def __iter__(self):
        return iter(self.entries)