# coding=utf-8
import bs
import bsUtils
import bsVector
import bsBomb
from math import cos
from random import randrange
import weakref
import types
import random
import copy


class doorHitSpazMessage():
    def __init__(self):
        pass


class doorStartUseMessage():
    def __init__(self):
        pass


class randomDoor(bs.Actor):
    def __init__(self, position=(0, 1, 0), velocity=(5, 0, 5), sourcePlayer=None, owner=None):
        bs.Actor.__init__(self)

        activity = bs.getActivity()
        factory = self.getFactory()
        # spawn at the provided point
        self._spawnPos = (position[0], position[1] + 0.1, position[2])
        self.node = bs.newNode("prop",
                               attrs={'model': factory.doorModel,
                                      'body': 'sphere',
                                      'colorTexture': factory.texColor,
                                      'reflection': 'soft',
                                      'modelScale': 1,
                                      'bodyScale': 1,
                                      'density': 1,
                                      'reflectionScale': [0.8],
                                      'shadowSize': 0.1,
                                      'position': self._spawnPos,
                                      'velocity': velocity,
                                      'materials': [bs.getSharedObject('objectMaterial'), factory.ballMaterial]
                                      },
                               delegate=self)
        self.sourcePlayer = sourcePlayer
        self.owner = owner
        if factory._autoDisappear:  # defaults to True.
            # Snowballs should melt after some time
            bs.gameTimer(6500, bs.WeakCall(self._disappear))
        self._hitNodes = set()
        self._used = False
        self.canUse = False

    def _disappear(self):
        self._used = True
        if self.exists():
            scl = self.node.modelScale
            bsUtils.animate(self.node, "modelScale", {0: scl * 1.0, 300: scl * 0.5, 500: 0.0})
            bs.gameTimer(550, bs.WeakCall(self.handleMessage, bs.DieMessage()))

    def handleMessage(self, m):
        super(self.__class__, self).handleMessage(m)

        if isinstance(m, bs.DieMessage):
            self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m, bs.DroppedMessage):
            bs.gameTimer(200, bs.WeakCall(self.handleMessage, doorStartUseMessage()))
        elif isinstance(m, doorStartUseMessage):
            self.canUse = True
        elif isinstance(m, doorHitSpazMessage):
            if not self.canUse:
                return
            if self._used:
                return
            oppoNode = bs.getCollisionInfo("opposingNode")
            if oppoNode is not None and oppoNode.exists():
                activity = self._activity()
                pos = self.getFactory().getRandomPosition(activity)
                oppoNode.handleMessage(bs.StandMessage(pos))
                bs.Blast(position=pos, blastRadius=1.0, blastType='smoke').autoRetain()
                bs.playSound(bs.getSound('shieldDown'))

            self._disappear()

    @classmethod
    def getFactory(cls):
        """
        Returns a shared randomDoorFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try:
            return activity._sharedRandomDoorFactory
        except Exception:
            f = activity._sharedRandomDoorFactory = randomDoorFactory()
            return f


def dropRandomDoor(self):
    # print 'Test drop'
    if self.bombCount > 0:
        self.bombCount -= 1
        self.setRandomDoorCount()

        p = self.node.positionForward
        v = self.node.velocity

        door = randomDoor(position=(p[0], p[1] - 0.0, p[2]),
                          velocity=(v[0], v[1], v[2]),
                          sourcePlayer=self.sourcePlayer,
                          owner=self.node).autoRetain()

        self._pickUp(door.node)
        return door

    f = types.MethodType(self.__class__.dropBomb, self, self.__class__)
    self.dropBomb = f
    self.bombCount = 1
    return self.dropBomb()


def setRandomDoorCount(self):
    if self.node.exists():
        if self.bombCount != 0:
            self.node.counterText = 'x' + str(self.bombCount)
            self.node.counterTexture = bs.Powerup.getFactory().texDoor
        else:
            self.node.counterText = ''


class randomDoorFactory(object):
    def __init__(self):

        self.texColor = bs.getTexture("cyborgColor")
        self.doorModel = bs.getModel("frostyPelvis")
        self.ballMaterial = bs.Material()
        self.impactSound = bs.getSound('impactMedium')
        self.ballMaterial.addActions(
            conditions=((('weAreYoungerThan', 5), 'or', ('theyAreYoungerThan', 100)),
                        'and', ('theyHaveMaterial', bs.getSharedObject('objectMaterial'))),
            actions=(('modifyNodeCollision', 'collide', False)))
        self.ballMaterial.addActions(
            conditions=('theyHaveMaterial', bs.getSharedObject('pickupMaterial')),
            actions=(('modifyPartCollision', 'useNodeCollide', False)))
        self.ballMaterial.addActions(actions=('modifyPartCollision', 'friction', 0.3))
        self.ballMaterial.addActions(conditions=('theyHaveMaterial', bs.getSharedObject('playerMaterial')), actions=(
            ('modifyPartCollision', 'physical', False), ('message', 'ourNode', 'atConnect', doorHitSpazMessage())))

        self.defaultBallTimeout = 300
        self._autoDisappear = True
        self.positionSpan = None

    def giveRD(self, spaz):
        f = types.MethodType(dropRandomDoor, spaz, spaz.__class__)
        spaz.dropBomb = f
        spaz.bombCount = 3  # give 3 random doors
        f2 = types.MethodType(setRandomDoorCount, spaz, spaz.__class__)
        spaz.setRandomDoorCount = f2
        spaz.setRandomDoorCount()

    def setpositionSpan(self, positionSpan):
        self.positionSpan = positionSpan

    def getRandomPosition(self, activity):
        if self.positionSpan is not None:
            ru = random.uniform
            ps = self.positionSpan
            return (ru(ps[0][0] - 1.0, ps[0][1] + 1.0), ps[1][1] + ru(0.1, 1.5), ru(ps[2][0] - 1.0, ps[2][1] + 1.0))

        pts = copy.copy(activity.getMap().ffaSpawnPoints)
        pts2 = activity.getMap().powerupSpawnPoints
        for i in pts2:
            pts.append(i)
        pos = [[999, -999], [999, -999], [999, -999]]
        for pt in pts:
            for i in range(3):
                pos[i][0] = min(pos[i][0], pt[i])
                pos[i][1] = max(pos[i][1], pt[i])

        self.setpositionSpan(pos)
        # print repr(pos)
        return self.getRandomPosition(activity)
