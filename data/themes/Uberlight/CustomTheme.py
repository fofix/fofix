from Theme import Theme
class CustomTheme(Theme):
  def __init__(self, path, name, iniFile = False):
    Theme.__init__(self, path, name)
    self.songListDisplay = 3
    self.doNecksRender = False
    self.loadingPhrase = ["Loading"]