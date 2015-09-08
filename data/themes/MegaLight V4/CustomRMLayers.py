
from Rockmeter import *

class CoOpMeter(Group):
    def __init__(self, stage, section):

        super(CoOpMeter, self).__init__(stage, section)

        self.ySpacingExpr = self.getexpr("yspacing", "0.0")
        self.ySpacing = 0.0
        self.condition = "True"

        print self.layers.values()

    def updateLayer(self, playerNum):
        super(CoOpMeter, self).updateLayer(playerNum)

        self.ySpacing = eval(self.ySpacingExpr)

    def render(self, visibility, playerNum):
        w, h, = self.engine.view.geometry[2:4]

        self.updateLayer(playerNum)
        for effect in self.effects:
            effect.update()

        self.engine.view.setViewportHalf(1,0)
        i = playerNum
        scale = (.75*(len(self.stage.scene.players)/2))

        for layer in self.layers.values():
            layer.updateLayer(playerNum)
            for effect in layer.effects:
                effect.update()
            layer.position = [p*scale for p in layer.position]
            layer.scale = [s*scale for s in layer.scale]
            if isinstance(layer, FontLayer):
                layer.position = [layer.position[0] + (self.position[0]/w), layer.position[1] - (self.position[1]/h)*.75]
                layer.position[1] -= (self.ySpacing*scale/h)*.75*(i/2)
            else:
                layer.position = [layer.position[n] + self.position[n] for n in range(2)]
                layer.position[1] -= (self.ySpacing*scale/h)*(i/2)

            #flips across screen for every other player
            if i % 2 == 1:
                layer.position[0] = w - layer.position[0]
                layer.scale[0] *= -1
                layer.angle *= -1

            #layer.scale = [s/(2.0*(len(self.stage.scene.players)/2)) for s in layer.scale]
            layer.render(visibility, playerNum)
