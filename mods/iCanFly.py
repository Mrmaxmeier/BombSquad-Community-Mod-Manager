import bs
import bsUtils
import random
import bsDeathMatch as dm
from bsBomb import BombFactory
from bsSpaz import _BombDiedMessage

def bsGetGames():
    return [FloatingDeathMatchGame]

def bsGetAPIVersion():
    return 4

class BallonBomb(bs.Bomb):

    def __init__(self, position=(0,1,0), velocity=(0,0,0), bombType='normal',
                 blastRadius=2.0, sourcePlayer=None, owner=None):
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.shield = None
        
        if bombType == 'ballon':
            self.bombType = bombType
            self.blastRadius = blastRadius
            self._exploded = False
            self._explodeCallbacks = []
            self.sourcePlayer = sourcePlayer # the player this came from
            self.hitType = 'explosion'
            self.hitSubType = self.bombType
            self.owner = owner
            if owner is None: owner = bs.Node(None)
            materials = (factory.bombMaterial,
                         bs.getSharedObject('objectMaterial'))
            self.node = bs.newNode('prop', delegate=self, attrs={
                'position':position,
                'velocity':velocity,
                'body':'sphere',
                'model':bs.getModel('bomb'),
                'shadowSize':0.3,
                'colorTexture':bs.getTexture('bg'),
                'reflection':'powerup',
                'reflectionScale':(random.randint(0, 2),
                                   random.randint(0, 2),
                                   random.randint(0, 2)),
                'materials':materials,
                'extraAcceleration':(0,70,0)})
            return
        else:
            bs.Bomb.__init__(self, position, velocity, bombType,
                             blastRadius, sourcePlayer, owner)
            
    def _handleDropped(self, m):
        if self.bombType == 'ballon':
        	self._delTimer = bs.Timer(5000, bs.WeakCall(self._del))
        	try:
        		self.node.extraAcceleration = (0, 10, 0)
        	except Exception as e:
        		bs.screenMessage(str(e))
        else:
        	bs.Bomb._handleDropped(self, m)
            
    def handleMessage(self, msg):
    	if isinstance(msg, bs.PickedUpMessage):
    		self._delTimer = None
    		self.node.extraAcceleration = (0, 70, 0)
    	bs.Bomb.handleMessage(self, msg)
    
    def _del(self):
        bs.playSound(bs.getSound('corkPop'), position = self.node.position)
        bs.emitBGDynamics(position=self.node.position, velocity=self.node.velocity,
                                          count=int(20.0+random.random()*25),
                                          scale=0.8, spread=1.0,
                                          emitType='tendrils',
                                          tendrilType='ice')
        self.handleMessage(bs.DieMessage())

class FloatingSpaz(bs.PlayerSpaz):

    def dropBomb(self):
        p = self.node.positionForward
        v = self.node.velocity
        droppingBomb = True
        bombType = 'ballon'
        bomb = BallonBomb(position=(p[0], p[1] - 0.0, p[2]),
                       velocity=(v[0], v[1], v[2]),
                       bombType=bombType,
                       blastRadius=self.blastRadius,
                       sourcePlayer=self.sourcePlayer,
                       owner=self.node).autoRetain()
        if droppingBomb:
            self.bombCount -= 1
            bomb.node.addDeathAction(bs.WeakCall(self.handleMessage,
                                                 _BombDiedMessage()))
        self._pickUp(bomb.node)

        for c in self._droppedBombCallbacks: c(self, bomb)
        
        return bomb
        

class FloatingDeathMatchGame(dm.DeathMatchGame):

    @classmethod
    def getName(cls):
        return 'I can fly'

    def setupStandardPowerupDrops(self, enableTNT=True):
        pass # Don't spawn poserups
    

    def spawnPlayerSpaz(self, player, position=(0, 0, 0), angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """
        
        # in teams-mode get our team-start-location
        if isinstance(self.getSession(), bs.TeamsSession):
            position = \
                self.getMap().getStartPosition(player.getTeam().getID())
        else:
            # otherwise do free-for-all spawn locations
            position = self.getMap().getFFAStartPosition(self.players)

        #################################################

        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color, targetIntensity=0.75)
        spaz = FloatingSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)

        # if this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(
                self.getSession(),
                bs.CoopSession) and self.getMap().getName() in[
                'Courtyard', 'Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(
            bs.StandMessage(
                position, angle
                if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor,
                                           'position':position})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)
        return spaz
    
    



