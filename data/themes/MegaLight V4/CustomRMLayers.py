
from Rockmeter import *

class Spinner(ImageLayer):
    def __init__(self, stage, section):
    
        self.stage = stage
        super(Spinner, self).__init__(stage, section, os.path.join("themes", self.stage.themename, "rockmeter", "platinum.png"))
        
        self.xposexpr    = ".80"
        self.yposexpr    = ".80"
        
        self.condition = "True"
        
    def updateLayer(self, playerNum):
        super(ImageLayer, self).updateLayer(playerNum)
        
        self.angle += 2
        
    def render(self, visibility, playerNum):
        
        self.updateLayer(playerNum)
        
        coord      = self.position
        scale      = self.scale
        rot        = self.angle
        color      = self.color
        alignment  = self.alignment
        valignment = self.valignment
        drawing    = self.drawing
        rect       = self.rect
    
        #frameX  = self.frameX
        #frameY  = self.frameY

        if bool(eval(self.condition)):
            self.engine.drawImage(drawing, scale, coord, rot, color, rect, 
                            alignment = alignment, valignment = valignment)        
