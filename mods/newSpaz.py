import copy
import bs
import bsSpaz

default_dropBomb = copy.deepcopy(bsSpaz.Spaz.dropBomb)


def onJumpPress(self):
    """
    Called to 'press jump' on this spaz;
    used by player or AI connections.
    """
    if not self.node.exists(): return
    t = bs.getGameTime()
    if self.jumpTo3DFly or (hasattr(self.getActivity()._map, "fly") and self.getActivity()._map.fly):
        if not self.node.exists() or self.node.knockout > 0.0:
            return
        self.node.handleMessage(
            "impulse", self.node.position[0], self.node.position[1], self.node.position[2],
            self.node.moveLeftRight * 10, self.node.position[1] + 32, self.node.moveUpDown * -10,
            5, 5, 0, 0,
            self.node.moveLeftRight * 10, self.node.position[1] + 32, self.node.moveUpDown * -10)
    else:
        if t - self.lastJumpTime >= self._jumpCooldown:
            self.node.jumpPressed = True
            self.lastJumpTime = t
        self._turboFilterAddPress('jump')


def dropBomb(self):
    """
    Tell the spaz to drop one of his bombs, and returns
    the resulting bomb object.
    If the spaz has no bombs or is otherwise unable to
    drop a bomb, returns None.
    """
    if (self.headacheCount <= 0 and self.bombCount <= 0) or self.frozen:
        return
    if (self.antiGravCount <= 0 and self.bombCount <= 0) or self.frozen:
        return
    p = self.node.positionForward
    v = self.node.velocity

    if self.headacheCount > 0:
        droppingBomb = False
        self.setHeadacheCount(self.headacheCount - 1)
        bombType = 'headache'
    elif self.antiGravCount > 0:
        droppingBomb = False
        self.setAntiGravCount(self.antiGravCount - 1)
        bombType = 'antiGrav'
    else:
        return default_dropBomb(self)

    bomb = bs.Bomb(position=(p[0], p[1] - 0.0, p[2]),
                   velocity=(v[0], v[1], v[2]),
                   bombType=bombType,
                   blastRadius=self.blastRadius,
                   sourcePlayer=self.sourcePlayer,
                   owner=self.node).autoRetain()

    if droppingBomb:
        self.bombCount -= 1
        bomb.node.addDeathAction(bs.WeakCall(self.handleMessage,
                                             bsSpaz._BombDiedMessage()))
    self._pickUp(bomb.node)

    for c in self._droppedBombCallbacks: c(self, bomb)

    return bomb


def setHeadacheCount(self, count):
    """
    Set the number of land-mines this spaz is carrying.
    """
    self.headacheCount = count
    if self.node.exists():
        if self.headacheCount != 0:
            self.node.counterText = 'x' + str(self.headacheCount)
            self.node.counterTexture = bs.Powerup.getFactory().texAche
        else:
            self.node.counterText = ''


def setAntiGravCount(self, count):
    """
    Set the number of land-mines this spaz is carrying.
    """
    self.antiGravCount = count
    if self.node.exists():
        if self.antiGravCount != 0:
            self.node.counterText = 'x' + str(self.antiGravCount)
            self.node.counterTexture = bs.Powerup.getFactory().texAntiGrav
        else:
            self.node.counterText = ''


bsSpaz.Spaz.jumpTo3DFly = False
bsSpaz.Spaz.headacheCount = 0
bsSpaz.Spaz.antiGravCount = 0
bsSpaz.Spaz.onJumpPress = onJumpPress
bsSpaz.Spaz.dropBomb = dropBomb
setattr(bsSpaz.Spaz, "setHeadacheCount", setHeadacheCount)
setattr(bsSpaz.Spaz, "setAntiGravCount", setAntiGravCount)

bs.Spaz = bsSpaz.Spaz
