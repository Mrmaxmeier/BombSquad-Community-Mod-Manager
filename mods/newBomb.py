import bs
import bsSpaz
import bsBomb
import bsUtils
from bsBomb import Bomb, ExplodeMessage, ArmMessage, WarnMessage, Blast, BombFactory, \
    ExplodeHitMessage, ImpactMessage, SplatMessage
import random


class AimForOpponent(object):
    def __init__(self, bomb, owner):

        self.bomb = bomb
        self.owner = owner
        self.target = None

        self.aimZoneSpaz = bs.Material()
        self.aimZoneSpaz.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial'))),
                                    actions=(("modifyPartCollision", "collide", True),
                                             ("modifyPartCollision", "physical", False),
                                             ("call", "atConnect", self.touchedSpaz)))

        self.lookForSpaz()

    def lookForSpaz(self):
        # To slow down the movement of the bomb towards the target and put the bomb over the head of the target.
        self.bomb.extraAcceleration = (0, 20, 0)
        self.node = bs.newNode('region',
                               attrs={'position': (self.bomb.position[0], self.bomb.position[1],
                                                   self.bomb.position[2]) if self.bomb.exists() else (
                                   0, 0, 0),
                                      'scale': (0.0, 0.0, 0.0),
                                      'type': 'sphere',
                                      'materials': [self.aimZoneSpaz]})
        self.s = bsUtils.animateArray(self.node, "scale", 3, {0: (0.0, 0.0, 0.0), 50: (60, 60, 60), 100: (90, 90, 90)},
                                      True)

        bs.gameTimer(150, self.node.delete)

        def checkTarget():
            if self.target is not None:
                self.touchedSpaz()

        bs.gameTimer(151, checkTarget)

    def go(self):
        if self.target is not None and self.bomb is not None and self.bomb.exists():
            self.bomb.velocity = (
                self.bomb.velocity[0] + (self.target.position[0] - self.bomb.position[0]),
                self.bomb.velocity[1] + (self.target.position[1] - self.bomb.position[1]),
                self.bomb.velocity[2] + (self.target.position[2] - self.bomb.position[2]))
            bs.gameTimer(1, self.go)

    def touchedSpaz(self):
        try:
            node = bs.getCollisionInfo('opposingNode')
        except AttributeError:
            return
        if not node == self.owner and node.getDelegate().isAlive() \
                and node.getDelegate().getPlayer().getTeam() != self.owner.getDelegate().getPlayer().getTeam():
            self.target = node
            self.s = None
            self.node.delete()
            self.bomb.extraAcceleration = (0, 200, 0)
            self.go()


class AntiGravArea(object):
    """For making the area to give the spaz upward force."""

    def __init__(self, position, radius):
        self.position = (position[0], position[1] + 1, position[2])
        self.radius = radius
        color = (random.random(), random.random(), random.random())
        self.material = bs.Material()
        self.material.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial'))),
                                 actions=(("modifyPartCollision", "collide", True),
                                          ("modifyPartCollision", "physical", False),
                                          ("call", "atConnect", self.touchedSpaz)))
        self.node = bs.newNode('region',
                               attrs={'position': (self.position[0], self.position[1], self.position[2]),
                                      'scale': (self.radius, self.radius, self.radius),
                                      'type': 'sphere',
                                      'materials': [self.material]})
        self.visualRadius = bs.newNode('shield', attrs={'position': self.position, 'color': color, 'radius': 0.1})
        bsUtils.animate(self.visualRadius, "radius", {0: 0, 500: self.radius * 2})
        bsUtils.animateArray(self.node, "scale", 3, {0: (0, 0, 0), 500: (self.radius, self.radius, self.radius)})

    def delete(self):
        if self.node.exists():
            self.node.delete()
        if self.visualRadius.exists():
            self.visualRadius.delete()

    def touchedSpaz(self):
        node = bs.getCollisionInfo('opposingNode')

        def raiseSpaz():
            if node.getDelegate().isAlive():
                node.handleMessage("impulse", node.position[0], node.position[1] + 0.5, node.position[2], 0, 5, 0,
                                   3, 10, 0, 0, 0, 5, 0)
                bs.gameTimer(50, raiseSpaz)
        raiseSpaz()


class NewBombFactory(BombFactory):
    def __init__(self):
        BombFactory.__init__(self)
        self.newTex = bs.getTexture("achievementOnslaught")

        self.newImpactBlastMaterial = bs.Material()
        self.newImpactBlastMaterial.addActions(
            conditions=(('weAreOlderThan', 200),
                        'and', ('theyAreOlderThan', 200),
                        'and', ('evalColliding',),
                        'and', ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')),
                        'and', ('theyHaveMaterial', self.bombMaterial),
                        'and', ('theyDontHaveMaterial', self.newImpactBlastMaterial)),
            actions=(('message', 'ourNode', 'atConnect', ImpactMessage())))


class NewBlast(Blast):
    def __init__(self, position=(0, 1, 0), velocity=(0, 0, 0), blastRadius=2.0,
                 blastType="normal", sourcePlayer=None, hitType='explosion',
                 hitSubType='normal'):
        bs.Actor.__init__(self)

        factory = Bomb.getFactory()

        self.blastType = blastType
        self.sourcePlayer = sourcePlayer

        self.hitType = hitType;
        self.hitSubType = hitSubType;

        # blast radius
        self.radius = blastRadius

        # set our position a bit lower so we throw more things upward
        self.node = bs.newNode('region', delegate=self, attrs={
            'position': (position[0], position[1] - 0.1, position[2]),
            'scale': (self.radius, self.radius, self.radius),
            'type': 'sphere',
            'materials': (factory.blastMaterial,
                          bs.getSharedObject('attackMaterial'))})

        bs.gameTimer(50, self.node.delete)

        # throw in an explosion and flash
        explosion = bs.newNode("explosion", attrs={
            'position': position,
            'velocity': (velocity[0], max(-1.0, velocity[1]), velocity[2]),
            'radius': self.radius,
            'big': (self.blastType == 'tnt')})
        if self.blastType == "ice":
            explosion.color = (0, 0.05, 0.4)

        bs.gameTimer(1000, explosion.delete)

        if self.blastType != 'ice':
            bs.emitBGDynamics(position=position, velocity=velocity,
                              count=int(1.0 + random.random() * 4),
                              emitType='tendrils', tendrilType='thinSmoke')
        bs.emitBGDynamics(
            position=position, velocity=velocity,
            count=int(4.0 + random.random() * 4), emitType='tendrils',
            tendrilType='ice' if self.blastType == 'ice' else 'smoke')
        bs.emitBGDynamics(
            position=position, emitType='distortion',
            spread=1.0 if self.blastType == 'tnt' else 2.0)

        # and emit some shrapnel..
        if self.blastType == 'ice':
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=30, spread=2.0, scale=0.4,
                                  chunkType='ice', emitType='stickers');

            bs.gameTimer(50, _doEmit)  # looks better if we delay a bit

        elif self.blastType == 'sticky':
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8),
                                  spread=0.7, chunkType='slime');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8), scale=0.5,
                                  spread=0.7, chunkType='slime');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=15, scale=0.6, chunkType='slime',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=20, scale=0.7, chunkType='spark',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(6.0 + random.random() * 12),
                                  scale=0.8, spread=1.5, chunkType='spark');

            bs.gameTimer(50, _doEmit)  # looks better if we delay a bit

        elif self.blastType == 'impact':  # regular bomb shrapnel
            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8), scale=0.8,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8), scale=0.4,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=20, scale=0.7, chunkType='spark',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(8.0 + random.random() * 15), scale=0.8,
                                  spread=1.5, chunkType='spark');

            bs.gameTimer(50, _doEmit)  # looks better if we delay a bit

        elif self.blastType == 'headache':  # regular bomb shrapnel

            def _doEmit():
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8), scale=0.8,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(4.0 + random.random() * 8), scale=0.4,
                                  chunkType='metal');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=20, scale=0.7, chunkType='spark',
                                  emitType='stickers');
                bs.emitBGDynamics(position=position, velocity=velocity,
                                  count=int(8.0 + random.random() * 15), scale=0.8,
                                  spread=1.5, chunkType='spark');

            bs.gameTimer(50, _doEmit)  # looks better if we delay a bit


        else:  # regular or land mine bomb shrapnel

            def _doEmit():

                if self.blastType != 'tnt':
                    bs.emitBGDynamics(position=position, velocity=velocity,

                                      count=int(4.0 + random.random() * 8),

                                      chunkType='rock');

                    bs.emitBGDynamics(position=position, velocity=velocity,

                                      count=int(4.0 + random.random() * 8),

                                      scale=0.5, chunkType='rock');

                bs.emitBGDynamics(position=position, velocity=velocity,

                                  count=30,

                                  scale=1.0 if self.blastType == 'tnt' else 0.7,

                                  chunkType='spark', emitType='stickers');

                bs.emitBGDynamics(position=position, velocity=velocity,

                                  count=int(18.0 + random.random() * 20),

                                  scale=1.0 if self.blastType == 'tnt' else 0.8,

                                  spread=1.5, chunkType='spark');

                # tnt throws splintery chunks

                if self.blastType == 'tnt':
                    def _emitSplinters():
                        bs.emitBGDynamics(position=position, velocity=velocity,

                                          count=int(20.0 + random.random() * 25),

                                          scale=0.8, spread=1.0,

                                          chunkType='splinter');

                    bs.gameTimer(10, _emitSplinters)

                # every now and then do a sparky one

                if self.blastType == 'tnt' or random.random() < 0.1:
                    def _emitExtraSparks():
                        bs.emitBGDynamics(position=position, velocity=velocity,

                                          count=int(10.0 + random.random() * 20),

                                          scale=0.8, spread=1.5,

                                          chunkType='spark');

                    bs.gameTimer(20, _emitExtraSparks)

            bs.gameTimer(50, _doEmit)  # looks better if we delay a bit

        light = bs.newNode('light', attrs={

            'position': position,

            'volumeIntensityScale': 10.0,

            'color': ((0.6, 0.6, 1.0) if self.blastType == 'ice'

                      else (1, 0.3, 0.1))})

        s = random.uniform(0.6, 0.9)

        scorchRadius = lightRadius = self.radius

        if self.blastType == 'tnt':
            lightRadius *= 1.4

            scorchRadius *= 1.15

            s *= 3.0

        iScale = 1.6

        bsUtils.animate(light, "intensity", {

            0: 2.0 * iScale, int(s * 20): 0.1 * iScale,

            int(s * 25): 0.2 * iScale, int(s * 50): 17.0 * iScale, int(s * 60): 5.0 * iScale,

            int(s * 80): 4.0 * iScale, int(s * 200): 0.6 * iScale,

            int(s * 2000): 0.00 * iScale, int(s * 3000): 0.0})

        bsUtils.animate(light, "radius", {

            0: lightRadius * 0.2, int(s * 50): lightRadius * 0.55,

            int(s * 100): lightRadius * 0.3, int(s * 300): lightRadius * 0.15,

            int(s * 1000): lightRadius * 0.05})

        bs.gameTimer(int(s * 3000), light.delete)

        # make a scorch that fades over time

        scorch = bs.newNode('scorch', attrs={

            'position': position,

            'size': scorchRadius * 0.5,

            'big': (self.blastType == 'tnt')})

        scorch.color = (random.random(), random.random(), random.random())
        if self.blastType == 'ice':
            scorch.color = (1, 1, 1.5)

        bsUtils.animate(scorch, "presence", {3000: 1, 13000: 0})

        bs.gameTimer(13000, scorch.delete)

        if self.blastType == 'ice':
            bs.playSound(factory.hissSound, position=light.position)

        p = light.position

        bs.playSound(factory.getRandomExplodeSound(), position=p)

        bs.playSound(factory.debrisFallSound, position=p)

        bs.shakeCamera(intensity=5.0 if self.blastType == 'tnt' else 1.0)

        # tnt is more epic..

        if self.blastType == 'tnt':
            bs.playSound(factory.getRandomExplodeSound(), position=p)

            def _extraBoom():
                bs.playSound(factory.getRandomExplodeSound(), position=p)

            bs.gameTimer(250, _extraBoom)

            def _extraDebrisSound():
                bs.playSound(factory.debrisFallSound, position=p)

                bs.playSound(factory.woodDebrisFallSound, position=p)

            bs.gameTimer(400, _extraDebrisSound)

    def handleMessage(self, msg):
        self._handleMessageSanityCheck()

        if isinstance(msg, bs.DieMessage):
            self.node.delete()

        elif isinstance(msg, ExplodeHitMessage):
            node = bs.getCollisionInfo("opposingNode")
            if node is not None and node.exists():
                t = self.node.position

                # new
                mag = 2000.0
                if self.blastType == 'ice': mag *= 0.5
                elif self.blastType == 'landMine': mag *= 2.5
                elif self.blastType == 'tnt': mag *= 2.0
                elif self.blastType == 'antiGrav': mag *= 0.1

                node.handleMessage(bs.HitMessage(
                    pos=t,
                    velocity=(0,0,0),
                    magnitude=mag,
                    hitType=self.hitType,
                    hitSubType=self.hitSubType,
                    radius=self.radius,
                    sourcePlayer=self.sourcePlayer))
                if self.blastType == "ice":
                    bs.playSound(Bomb.getFactory().freezeSound, 10, position=t)
                    node.handleMessage(bs.FreezeMessage())

        else:
            bs.Actor.handleMessage(self, msg)


class NewBomb(Bomb):
    def __init__(self, position=(0, 1, 0), velocity=(0, 0, 0), bombType='normal',
                 blastRadius=2.0, sourcePlayer=None, owner=None):
        bs.Actor.__init__(self)

        factory = self.getFactory()

        if not bombType in ('headache', 'ice', 'impact', 'landMine', 'normal', 'sticky', 'tnt', 'antiGrav'):
            raise Exception("invalid bomb type: " + bombType)
        self.bombType = bombType

        self._exploded = False

        if self.bombType == 'sticky': self._lastStickySoundTime = 0

        self.blastRadius = blastRadius
        if self.bombType == 'ice':
            self.blastRadius *= 1.2
        elif self.bombType == 'impact':
            self.blastRadius *= 0.7
        elif self.bombType == 'landMine':
            self.blastRadius *= 0.7
        elif self.bombType == 'tnt':
            self.blastRadius *= 1.45

        self._explodeCallbacks = []

        # the player this came from
        self.sourcePlayer = sourcePlayer

        # by default our hit type/subtype is our own, but we pick up types of
        # whoever sets us off so we know what caused a chain reaction
        self.hitType = 'explosion'
        self.hitSubType = self.bombType

        # if no owner was provided, use an unconnected node ref
        if owner is None: owner = bs.Node(None)

        # the node this came from
        self.owner = owner

        # adding footing-materials to things can screw up jumping and flying
        # since players carrying those things
        # and thus touching footing objects will think they're on solid ground..
        # perhaps we don't wanna add this even in the tnt case?..
        if self.bombType == 'tnt':
            materials = (factory.bombMaterial,
                         bs.getSharedObject('footingMaterial'),
                         bs.getSharedObject('objectMaterial'))
        else:
            materials = (factory.bombMaterial,
                         bs.getSharedObject('objectMaterial'))

        if self.bombType == 'impact':
            materials = materials + (factory.impactBlastMaterial,)
        elif self.bombType == 'headache':
            materials = materials + (factory.newImpactBlastMaterial,)
        elif self.bombType == 'landMine':
            materials = materials + (factory.landMineNoExplodeMaterial,)
        elif self.bombType == 'antiGrav':
            materials = materials + (factory.impactBlastMaterial,)

        if self.bombType == 'sticky':
            materials = materials + (factory.stickyMaterial,)
        else:
            materials = materials + (factory.normalSoundMaterial,)

        if self.bombType == 'landMine':
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position': position,
                'velocity': velocity,
                'model': factory.landMineModel,
                'lightModel': factory.landMineModel,
                'body': 'landMine',
                'shadowSize': 0.44,
                'colorTexture': factory.landMineTex,
                'reflection': 'powerup',
                'reflectionScale': [1.0],
                'materials': materials})

        elif self.bombType == 'tnt':
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position': position,
                'velocity': velocity,
                'model': factory.tntModel,
                'lightModel': factory.tntModel,
                'body': 'crate',
                'shadowSize': 0.5,
                'colorTexture': factory.tntTex,
                'reflection': 'soft',
                'reflectionScale': [0.23],
                'materials': materials})

        elif self.bombType == 'impact':
            fuseTime = 20000
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position': position,
                'velocity': velocity,
                'body': 'sphere',
                'model': factory.impactBombModel,
                'shadowSize': 0.3,
                'colorTexture': factory.impactTex,
                'reflection': 'powerup',
                'reflectionScale': [1.5],
                'materials': materials})

        elif self.bombType == 'antiGrav':
            fuseTime = 30000
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position': position,
                'velocity': velocity,
                'body': 'sphere',
                'model': factory.impactBombModel,
                'shadowSize': 0.3,
                'colorTexture': factory.newTex,
                'reflection': 'powerup',
                'reflectionScale': [1.5],
                'materials': materials})

        else:
            fuseTime = 3000
            if self.bombType == 'sticky':
                sticky = True
                model = factory.stickyBombModel
                rType = 'sharper'
                rScale = 1.8
            else:
                sticky = False
                model = factory.bombModel
                rType = 'sharper'
                rScale = 1.8
            if self.bombType == 'ice':
                tex = factory.iceTex
            elif self.bombType == 'sticky':
                tex = factory.stickyTex
            elif self.bombType == 'headache':
                fuseTime = 13000
                tex = factory.newTex
                model = factory.impactBombModel
            else:
                tex = factory.regularTex
            self.node = bs.newNode('bomb', delegate=self, attrs={
                'position': position,
                'velocity': velocity,
                'model': model,
                'shadowSize': 0.3,
                'colorTexture': tex,
                'sticky': sticky,
                'owner': owner,
                'reflection': rType,
                'reflectionScale': [rScale],
                'materials': materials})

            sound = bs.newNode('sound', owner=self.node, attrs={
                'sound': factory.fuseSound,
                'volume': 0.25})
            self.node.connectAttr('position', sound, 'position')
            bsUtils.animate(self.node, 'fuseLength', {0: 1.0, fuseTime: 0.0})

        # light the fuse!!!
        if self.bombType not in ('landMine', 'tnt'):
            bs.gameTimer(fuseTime,
                         bs.WeakCall(self.handleMessage, ExplodeMessage()))

        bsUtils.animate(self.node, "modelScale", {0: 0, 200: 1.3, 260: 1})

    def _handleDropped(self, m):
        if self.bombType == 'landMine':
            self.armTimer = \
                bs.Timer(1250, bs.WeakCall(self.handleMessage, ArmMessage()))

        # once we've thrown a sticky bomb we can stick to it..
        elif self.bombType == 'sticky':
            def _safeSetAttr(node, attr, value):
                if node.exists(): setattr(node, attr, value)

            bs.gameTimer(
                250, lambda: _safeSetAttr(self.node, 'stickToOwner', True))

        elif self.bombType == 'headache':
            AimForOpponent(self.node, self.owner)

    def _handleHit(self, msg):
        if self.bombType == 'headache' and msg.hitType == 'punch':
            self.handleMessage(ExplodeMessage())
        isPunch = (msg.srcNode.exists() and msg.srcNode.getNodeType() == 'spaz')

        # normal bombs are triggered by non-punch impacts..
        # impact-bombs by all impacts

        if (not self._exploded and not isPunch
                or self.bombType in ['impact', "antiGrav", 'landMine']):
            # also lets change the owner of the bomb to whoever is setting
            # us off.. (this way points for big chain reactions go to the
            # person causing them)
            if msg.sourcePlayer not in [None]:
                self.sourcePlayer = msg.sourcePlayer

                # also inherit the hit type (if a landmine sets off by a bomb,
                # the credit should go to the mine)
                # the exception is TNT.  TNT always gets credit.
                if self.bombType != 'tnt':
                    self.hitType = msg.hitType
                    self.hitSubType = msg.hitSubType

            bs.gameTimer(100 + int(random.random() * 100),
                         bs.WeakCall(self.handleMessage, ExplodeMessage()))
        self.node.handleMessage(
            "impulse", msg.pos[0], msg.pos[1], msg.pos[2],
            msg.velocity[0], msg.velocity[1], msg.velocity[2],
            msg.magnitude, msg.velocityMagnitude, msg.radius, 0,
            msg.velocity[0], msg.velocity[1], msg.velocity[2])

        if msg.srcNode.exists():
            pass

    def _handleImpact(self, m):
        node, body = bs.getCollisionInfo("opposingNode", "opposingBody")
        # if we're an impact bomb or anti-gravity bomb and we came from this node, don't explode...
        # alternately if we're hitting another impact-bomb from the same source,
        # don't explode...
        try:
            nodeDelegate = node.getDelegate()
        except Exception:
            nodeDelegate = None
        if node is not None and node.exists():
            if (self.bombType == 'impact' and
                    (node is self.owner
                     or (isinstance(nodeDelegate, Bomb)
                         and nodeDelegate.bombType == 'impact'
                         and nodeDelegate.owner is self.owner))):
                return
            elif (self.bombType == 'antiGrav' and
                  (node is self.owner
                   or (isinstance(nodeDelegate, Bomb)
                       and nodeDelegate.bombType == 'antiGrav'
                       and nodeDelegate.owner is self.owner))):
                return
            else:
                self.handleMessage(ExplodeMessage())

    def _handleDie(self, msg):
        if self.bombType == "antiGrav" and self.node.exists():
            aga = AntiGravArea(position=self.node.position, radius=self.blastRadius)
            bs.gameTimer(7000, aga.delete)
        self.node.delete()

    def handleMessage(self, msg):
        if isinstance(msg, ExplodeMessage):
            self.explode()
        elif isinstance(msg, ImpactMessage):
            self._handleImpact(msg)
        elif isinstance(msg, bs.PickedUpMessage):
            # change our source to whoever just picked us up *only* if its None
            # this way we can get points for killing bots with their own bombs
            # hmm would there be a downside to this?...
            if self.sourcePlayer is not None:
                self.sourcePlayer = msg.node.sourcePlayer
        elif isinstance(msg, SplatMessage):
            self._handleSplat(msg)
        elif isinstance(msg, bs.DroppedMessage):
            self._handleDropped(msg)
        elif isinstance(msg, bs.HitMessage):
            self._handleHit(msg)
        elif isinstance(msg, bs.DieMessage):
            self._handleDie(msg)
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self._handleOOB(msg)
        elif isinstance(msg, ArmMessage):
            self.arm()
        elif isinstance(msg, WarnMessage):
            self._handleWarn(msg)
        else:
            bs.Actor.handleMessage(self, msg)


bsBomb.Bomb = NewBomb
bs.Bomb = NewBomb
bsBomb.Blast = NewBlast
bs.Blast = NewBlast
bsBomb.BombFactory = NewBombFactory
bs.BombFactory = NewBombFactory
