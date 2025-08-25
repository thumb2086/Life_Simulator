import sys
if sys.platform == 'win32':
    import winsound
else:
    winsound = None

class SoundManager:
    @staticmethod
    def play_achievement():
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    @staticmethod
    def play_slot_win():
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    @staticmethod
    def play_error():
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONHAND) 