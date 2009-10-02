from sumatra.recordstore import RecordStore
import shelve

class ShelveRecordStore(object):
    
    def __init__(self, shelf_name):
        self._shelf_name = shelf_name
        self.shelf = shelve.open(shelf_name)
        
    def __del__(self):
        self.shelf.close()
        
    def __str__(self):
        return "shelve"
        
    def __getstate__(self):
        return self._shelf_name
    
    def __setstate__(self, state):
        self.__init__(state)

    def save(self, record):
        self.shelf[record.label] = record
        
    def get(self, label):
        return self.shelf[label]
    
    def list(self, groups):
        if groups:
            return [record for record in self.shelf.values() if record.group in groups]
        else:
            returnself.shelf.values()
    
    def delete(self, label):
        del self.shelf[label]