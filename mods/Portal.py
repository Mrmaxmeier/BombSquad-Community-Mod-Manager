import bs
import random
import bsUtils
import copy
import types

# Following are necessary variables for portal
maxportals = 3
currentnum = 0
lastpos = [(0, 0, 0), (1, 0, 2)]  # initial values for test
defi = [(0, 1, 2), (1, 0, 2)]  # initial values for test


class Portal(bs.Actor):
    def __init__(self, position1=(0, 1, 0), color=(random.random(), random.random(), random.random()), r=1.0,
                 activity=None):
        bs.Actor.__init__(self)

        self.radius = r
        if position1 is None:
            self.position1 = self.getRandomPosition(activity)
        else:
            self.position1 = position1
        self.position2 = self.getRandomPosition(activity)

        self.portal1Material = bs.Material()
        self.portal1Material.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial'))),
                                        actions=(("modifyPartCollision", "collide", True),
                                                 ("modifyPartCollision", "physical", False),
                                                 ("call", "atConnect", self.Portal1)))

        self.portal2Material = bs.Material()
        self.portal2Material.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial'))),
                                        actions=(("modifyPartCollision", "collide", True),
                                                 ("modifyPartCollision", "physical", False),
                                                 ("call", "atConnect", self.Portal2)))
        # uncomment the following lines to teleport objects also
        # self.portal1Material.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('objectMaterial')),'and',('theyDontHaveMaterial', bs.getSharedObject('playerMaterial'))),actions=(("modifyPartCollision","collide",True),
        # ("modifyPartCollision","physical",False),
        # ("call","atConnect", self.objPortal1)))
        # self.portal2Material.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('objectMaterial')),'and',('theyDontHaveMaterial', bs.getSharedObject('playerMaterial'))),actions=(("modifyPartCollision","collide",True),
        # ("modifyPartCollision","physical",False),
        # ("call","atConnect", self.objPortal2)))

        self.node1 = bs.newNode('region',
                                attrs={'position': (self.position1[0], self.position1[1], self.position1[2]),
                                       'scale': (self.radius, self.radius, self.radius),
                                       'type': 'sphere',
                                       'materials': [self.portal1Material]})
        self.visualRadius = bs.newNode('shield', attrs={'position': self.position1, 'color': color, 'radius': 0.1})
        bsUtils.animate(self.visualRadius, "radius", {0: 0, 500: self.radius * 2})
        bsUtils.animateArray(self.node1, "scale", 3, {0: (0, 0, 0), 500: (self.radius, self.radius, self.radius)})

        self.node2 = bs.newNode('region',
                                attrs={'position': (self.position2[0], self.position2[1], self.position2[2]),
                                       'scale': (self.radius, self.radius, self.radius),
                                       'type': 'sphere',
                                       'materials': [self.portal2Material]})
        self.visualRadius2 = bs.newNode('shield', attrs={'position': self.position2, 'color': color, 'radius': 0.1})
        bsUtils.animate(self.visualRadius2, "radius", {0: 0, 500: self.radius * 2})
        bsUtils.animateArray(self.node2, "scale", 3, {0: (0, 0, 0), 500: (self.radius, self.radius, self.radius)})

    def Portal1(self):
        node = bs.getCollisionInfo('opposingNode')
        node.handleMessage(bs.StandMessage(position=self.node2.position))

    def Portal2(self):
        node = bs.getCollisionInfo('opposingNode')
        node.handleMessage(bs.StandMessage(position=self.node1.position))

    def objPortal1(self):
        node = bs.getCollisionInfo('opposingNode')
        node.position = self.position2

    def objPortal2(self):
        node = bs.getCollisionInfo('opposingNode')
        node.position = self.position1

    def delete(self):
        if self.node1.exists() and self.node2.exists():
            self.node1.delete()
            self.node2.delete()
            self.visualRadius.delete()
            self.visualRadius2.delete()
            if self.position1 in lastpos:
                lastpos.remove(self.position1)
            defi.remove(self.node2.position)

    def posn(self, s, act):
        ru = random.uniform
        rc = random.choice
        f = rc([(s[0], s[1], s[2] - ru(0.1, 0.6)), (s[0], s[1], s[2] + ru(0.1, 0.6)), (s[0] - ru(0.1, 0.6), s[1], s[2]),
                (s[0] + ru(0.1, 0.6), s[1], s[2])])
        if f in defi or f in lastpos:
            return self.getRandomPosition(act)
        else:
            defi.append(f)
            return f

    def getRandomPosition(self, activity):

        pts = copy.copy(activity.getMap().ffaSpawnPoints)
        pts2 = activity.getMap().powerupSpawnPoints
        for i in pts2:
            pts.append(i)
        pos = [[999, -999], [999, -999], [999, -999]]
        for pt in pts:
            for i in range(3):
                pos[i][0] = min(pos[i][0], pt[i])
                pos[i][1] = max(pos[i][1], pt[i])
        # The credit of this random position finder goes to Deva but I did some changes too.
        ru = random.uniform
        ps = pos
        t = ru(ps[0][0] - 1.0, ps[0][1] + 1.0), ps[1][1] + ru(0.1, 1.5), ru(ps[2][0] - 1.0, ps[2][1] + 1.0)
        s = (t[0], t[1] - ru(1.0, 1.3), t[2])
        if s in defi or s in lastpos:
            return self.posn(s, activity)
        else:
            defi.append(s)
            return s
