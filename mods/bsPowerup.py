import bs
import random
#add for bunny buddy:
import BuddyBunny
import SnoBallz


defaultPowerupInterval = 8000


class PowerupMessage(object):
    """
    category: Message Classes

    Tell something to get a powerup.
    This message is normally recieved by touching
    a bs.Powerup box.
    
    Attributes:
    
       powerupType
          The type of powerup to be granted (a string). See bs.Powerup.powerupType for available type values.

       sourceNode
          The node the powerup game from, or an empty bs.Node ref otherwise.
          If a powerup is accepted, a bs.PowerupAcceptMessage should be sent
          back to the sourceNode to inform it of the fact. This will generally
          cause the powerup box to make a sound and disappear or whatnot.
    """
    def __init__(self,powerupType,sourceNode=bs.Node(None)):
        """
        Instantiate with given values.
        See bs.Powerup.powerupType for available type values.
        """
        self.powerupType = powerupType
        self.sourceNode = sourceNode

class PowerupAcceptMessage(object):
    """
    category: Message Classes

    Inform a bs.Powerup that it was accepted.
    This is generally sent in response to a bs.PowerupMessage
    to inform the box (or whoever granted it) that it can go away.
    """
    pass

class _TouchedMessage(object):
    pass

class PowerupFactory(object):
    """
    category: Game Flow Classes
    
    Wraps up media and other resources used by bs.Powerups.
    A single instance of this is shared between all powerups
    and can be retrieved via bs.Powerup.getFactory().

    Attributes:

       model
          The bs.Model of the powerup box.

       modelSimple
          A simpler bs.Model of the powerup box, for use in shadows, etc.

       texBox
          Triple-bomb powerup bs.Texture.

       texPunch
          Punch powerup bs.Texture.

       texIceBombs
          Ice bomb powerup bs.Texture.

       texStickyBombs
          Sticky bomb powerup bs.Texture.

       texShield
          Shield powerup bs.Texture.

       texImpactBombs
          Impact-bomb powerup bs.Texture.

       texHealth
          Health powerup bs.Texture.

       texLandMines
          Land-mine powerup bs.Texture.

       texCurse
          Curse powerup bs.Texture.

       healthPowerupSound
          bs.Sound played when a health powerup is accepted.

       powerupSound
          bs.Sound played when a powerup is accepted.

       powerdownSound
          bs.Sound that can be used when powerups wear off.

       powerupMaterial
          bs.Material applied to powerup boxes.

       powerupAcceptMaterial
          Powerups will send a bs.PowerupMessage to anything they touch
          that has this bs.Material applied.
    """

    def __init__(self):
        """
        Instantiate a PowerupFactory.
        You shouldn't need to do this; call bs.Powerup.getFactory() to get a shared instance.
        """

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

    def getRandomPowerupType(self,forceType=None,excludeTypes=[]):
        """
        Returns a random powerup type (string).
        See bs.Powerup.powerupType for available type values.

        There are certain non-random aspects to this; a 'curse' powerup, for instance,
        is always followed by a 'health' powerup (to keep things interesting).
        Passing 'forceType' forces a given returned type while still properly interacting
        with the non-random aspects of the system (ie: forcing a 'curse' powerup will result
        in the next powerup being health).
        """
        if forceType:
            t = forceType
        else:
            # if the last one was a curse, make this one a health to provide some hope
            if self._lastPowerupType == 'curse':
                t = 'health'
            else:
                while True:
                    t = self._powerupDist[random.randint(0,len(self._powerupDist)-1)]
                    if t not in excludeTypes:
                        break
        self._lastPowerupType = t
        return t


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

class Powerup(bs.Actor):
    """
    category: Game Flow Classes

    A powerup box.
    This will deliver a bs.PowerupMessage to anything that touches it
    which has the bs.PowerupFactory.powerupAcceptMaterial applied.

    Attributes:

       powerupType
          The string powerup type.  This can be 'tripleBombs', 'punch',
          'iceBombs', 'impactBombs', 'landMines', 'stickyBombs', 'shield',
          'health', or 'curse'.

       node
          The 'prop' bs.Node representing this box.
    """

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

    @classmethod
    def getFactory(cls):
        """
        Returns a shared bs.PowerupFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try: return activity._sharedPowerupFactory
        except Exception:
            f = activity._sharedPowerupFactory = PowerupFactory()
            return f
            
    def _startFlashing(self):
        if self.node.exists(): self.node.flashing = True

        
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
