import bs
import random
#add for bunny buddy:
import BuddyBunny
import SnoBallz
import bsPowerup
from bsPowerup import PowerupMessage, PowerupAcceptMessage, _TouchedMessage, PowerupFactory, Powerup


defaultPowerupInterval = 8000

class NewPowerupFactory(PowerupFactory):
    def __init__(self):
        self._lastPowerupType = None

        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        #Add for Bunnybot:
        self.eggModel = bs.getModel('egg')
        self.texEgg = bs.getTexture('eggTex1')
        #Add for snoBalls:
        self.texSno = bs.getTexture("bunnyColor") #Bunny is most uniform plain white color.
        self.snoModel = bs.getModel("frostyPelvis") #Frosty pelvis is very nice and round...
        self.healthPowerupSound = bs.getSound("healthPowerup")
        self.powerupSound = bs.getSound("powerup01")
        self.powerdownSound = bs.getSound("powerdown01")
        self.dropSound = bs.getSound("boxDrop")

        # material for powerups
        self.powerupMaterial = bs.Material()

        # material for anyone wanting to accept powerups
        self.powerupAcceptMaterial = bs.Material()

        # pass a powerup-touched message to applicable stuff
        self.powerupMaterial.addActions(
            conditions=(("theyHaveMaterial",self.powerupAcceptMaterial)),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message","ourNode","atConnect",_TouchedMessage())))

        # we dont wanna be picked up
        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
            actions=( ("modifyPartCollision","collide",False)))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",bs.getSharedObject('footingMaterial')),
            actions=(("impactSound",self.dropSound,0.5,0.1)))

        self._powerupDist = []
        for p,freq in getDefaultPowerupDistribution():
            for i in range(int(freq)):
                self._powerupDist.append(p)

    def getRandomPowerupType(self, forceType=None, excludeTypes=None):
        if excludeTypes:
            # exclude custom powerups if there is some custom powerup logic
            # example: bsFootball.py:456
            excludeTypes.append('snoball')
            excludeTypes.append('bunny')
        else:
            excludeTypes = []
        return PowerupFactory.getRandomPowerupType(self, forceType, excludeTypes)


def getDefaultPowerupDistribution():
    return (('tripleBombs',3),
            ('iceBombs',3),
            ('punch',3),
            ('impactBombs',3),
            ('landMines',2),
            ('stickyBombs',3),
            ('shield',2),
            ('health',1),
            ('bunny',2),
            ('curse',1),
            ('snoball',3))

class NewPowerup(Powerup):
    def __init__(self,position=(0,1,0),powerupType='tripleBombs',expire=True):
        """
        Create a powerup-box of the requested type at the requested position.

        see bs.Powerup.powerupType for valid type strings.
        """
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.powerupType = powerupType;
        self._powersGiven = False

        mod = factory.model
        mScl = 1
        if powerupType == 'tripleBombs': tex = factory.texBomb
        elif powerupType == 'punch': tex = factory.texPunch
        elif powerupType == 'iceBombs': tex = factory.texIceBombs
        elif powerupType == 'impactBombs': tex = factory.texImpactBombs
        elif powerupType == 'landMines': tex = factory.texLandMines
        elif powerupType == 'stickyBombs': tex = factory.texStickyBombs
        elif powerupType == 'shield': tex = factory.texShield
        elif powerupType == 'health': tex = factory.texHealth
        elif powerupType == 'curse': tex = factory.texCurse
        elif powerupType == 'bunny': 
            tex = factory.texEgg
            mod = factory.eggModel
            mScl = 0.7
        elif powerupType == 'snoball': 
            tex = factory.texSno
            mod = factory.snoModel
        else: raise Exception("invalid powerupType: "+str(powerupType))

        if len(position) != 3: raise Exception("expected 3 floats for position")
        
        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body':'box',
                                      'position':position,
                                      'model':mod,
                                      'lightModel':factory.modelSimple,
                                      'shadowSize':0.5,
                                      'colorTexture':tex,
                                      'reflection':'powerup',
                                      'reflectionScale':[1.0],
                                      'materials':(factory.powerupMaterial,bs.getSharedObject('objectMaterial'))})

        # animate in..
        curve = bs.animate(self.node,"modelScale",{0:0,140:1.6,200:mScl})
        bs.gameTimer(200,curve.delete)

        if expire:
            bs.gameTimer(defaultPowerupInterval-2500,bs.WeakCall(self._startFlashing))
            bs.gameTimer(defaultPowerupInterval-1000,bs.WeakCall(self.handleMessage,bs.DieMessage()))

    def handleMessage(self,m):
        self._handleMessageSanityCheck()

        if isinstance(m,PowerupAcceptMessage):
            factory = self.getFactory()
            if self.powerupType == 'health':
                bs.playSound(factory.healthPowerupSound,3,position=self.node.position)
            bs.playSound(factory.powerupSound,3,position=self.node.position)
            self._powersGiven = True
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,_TouchedMessage):
            if not self._powersGiven:
                node = bs.getCollisionInfo("opposingNode")
                if node is not None and node.exists():
                    #We won't tell the spaz about the bunny.  It'll just happen.
                    if self.powerupType == 'bunny':
                        p=node.getDelegate().getPlayer()
                        if not 'bunnies' in p.gameData:
                            p.gameData['bunnies'] = BuddyBunny.BunnyBotSet(p)
                        p.gameData['bunnies'].doBunny()
                        self._powersGiven = True
                        self.handleMessage(bs.DieMessage())
                    #a Spaz doesn't know what to do with a snoball powerup. All the snowball functionality
                    #is handled through SnoBallz.py to minimize modifications to the original game files
                    elif self.powerupType == 'snoball':
                        spaz=node.getDelegate()
                        SnoBallz.snoBall().getFactory().giveBallz(spaz)
                        self._powersGiven = True
                        self.handleMessage(bs.DieMessage())
                    else:
                        node.handleMessage(PowerupMessage(self.powerupType,sourceNode=self.node))
                        
        elif isinstance(m,bs.DieMessage):
            if self.node.exists():
                if (m.immediate):
                    self.node.delete()
                else:
                    curve = bs.animate(self.node,"modelScale",{0:1,100:0})
                    bs.gameTimer(100,self.node.delete)

        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,bs.HitMessage):
            # dont die on punches (thats annoying)
            if m.hitType != 'punch':
                self.handleMessage(bs.DieMessage())
        else:
            bs.Actor.handleMessage(self,m)

bsPowerup.PowerupFactory = NewPowerupFactory
bsPowerup.Powerup = NewPowerup
