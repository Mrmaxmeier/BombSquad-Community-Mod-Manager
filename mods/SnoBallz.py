#This is not a minigame mod script.  It's a powerup.
import bs
import bsUtils
import bsVector
import bsBomb
from math import cos
from random import randrange
import weakref



    
class snoMessage(object):
    #Message passed to a snoBall by collision with a spaz
    pass
class otherHitMessage(object):
    #Message passed when we hit some other object.  Lets us poof into thin air.
    pass
class snoBall(bs.Actor):

    def __init__(self, position=(0,1,0), velocity=(5,0,5), sourcePlayer=None, owner=None, explode=False):
        bs.Actor.__init__(self)

        activity = bs.getActivity()
        factory = self.getFactory()
        # spawn at the provided point
        self._spawnPos = (position[0], position[1]+0.1, position[2])
        self.node = bs.newNode("prop",
                               attrs={'model': factory.snoModel,
                                      'body':'sphere',
                                      'colorTexture': factory.texSno,
                                      'reflection':'soft',
                                      'modelScale':0.8,
                                      'bodyScale':0.8,
                                      'density':1,
                                      'reflectionScale':[0.15],
                                      'shadowSize': 0.6,
                                      'position':self._spawnPos,
                                      'velocity':velocity,
                                      'materials': [bs.getSharedObject('objectMaterial'), factory.ballMaterial]
                                      },
                               delegate=self)
        self.sourcePlayer = sourcePlayer
        self.owner = owner
        if factory._ballsMelt: #defaults to True.
            #Snowballs should melt after some time
            bs.gameTimer(1500, bs.WeakCall(self._disappear))
        self._hitNodes = set()
        self._exploded = False
        if factory._ballsBust:
            self.shouldBust = True
        else:
            self.shouldBust = False
        if explode:
            self.shouldExplode = True
        else:
            self.shouldExplode = False
        
    def handleMessage(self,m):
        super(self.__class__, self).handleMessage(m)
        if isinstance(m, otherHitMessage):
            if self._exploded: return #Don't bother with calcs if we've done blowed up or busted.
            if self.shouldBust:
                myVel = self.node.velocity
                #Get the velocity at the instant of impact.  We'll check it after 20ms (after bounce). If it has changed a lot, bust.
                bs.gameTimer(10, bs.WeakCall(self.calcBust,myVel))
            else:
                return
        if isinstance(m,bs.DieMessage):
            self.node.delete()
        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m,bs.HitMessage):
            self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                    m.velocity[0],m.velocity[1],m.velocity[2],
                                    1.0*m.magnitude,1.0*m.velocityMagnitude,m.radius,0,
                                    m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])
        elif isinstance(m, bs.ImpactDamageMessage):
            print [dir(m), m.intensity]
        elif isinstance(m,snoMessage):
            #We should get a snoMessage any time a snowball hits a spaz.
            #We'll either explode (if we're exploding) or calculate like a punch.
            #We have to do this the hard way because the ImpactMessage won't do it for us (no source)
            #Below is modified pretty much from bsSpaz handling of a _punchHitMessage
            #print bsVector.Vector(*self.node.velocity).length()
            if self._exploded: return #Don't do anything if we've already done our damage, or if we've busted already
            if self.shouldExplode:
                """
                Blows up the ball if it has not yet done so.
                """
                if self._exploded: return
                self._exploded = True
                activity = self.getActivity()
                if activity is not None and self.node.exists():
                    blast = bsBomb.Blast(position=self.node.position,velocity=self.node.velocity,
                                  blastRadius=0.7,blastType='impact',sourcePlayer=self.sourcePlayer,hitType='snoBall',hitSubType='explode').autoRetain()
                    
                # we blew up so we need to go away
                bs.gameTimer(1,bs.WeakCall(self.handleMessage,bs.DieMessage()))
            else:
                v = self.node.velocity
                #Only try to damage if the ball is moving at some reasonable rate of speed
                if bs.Vector(*v).length() > 5.0:
                    node = bs.getCollisionInfo("opposingNode")

                    # only allow one hit per node per ball
                    if node is not None and node.exists() and not node in self._hitNodes:

                        t = self.node.position #was punchPosition
                        hitDir = self.node.velocity 

                        self._hitNodes.add(node)
                        node.handleMessage(bs.HitMessage(pos=t,
                                                         velocity=v,
                                                         magnitude=bsVector.Vector(*v).length()*0.5,
                                                         velocityMagnitude=bsVector.Vector(*v).length()*0.5,
                                                         radius=0,
                                                         srcNode=self.node,
                                                         sourcePlayer=self.sourcePlayer,
                                                         forceDirection = hitDir,
                                                         hitType='snoBall',
                                                         hitSubType='default'))

                if self.shouldBust:
                    #Since we hit someone, let's bust:
                    #Add a very short timer to allow one ball to hit more than one spaz if almost simultaneous.
                    bs.gameTimer(50, bs.WeakCall(self.doBust))
        else:
            bs.Actor.handleMessage(self,m)
    def doBust(self):
        if self.exists():
            if not self._exploded:
                self._exploded = True
                bs.emitBGDynamics(position=self.node.position,velocity=[v*0.1 for v in self.node.velocity],count=10,spread=0.1,scale=0.4,chunkType='ice')
                #Do a muffled punch sound
                sound = self.getFactory().impactSound
                bs.playSound(sound,1.0,position=self.node.position)
                scl = self.node.modelScale
                bsUtils.animate(self.node,"modelScale",{0:scl*1.0, 20:scl*0.5, 50:0.0})
                bs.gameTimer(80,bs.WeakCall(self.handleMessage,bs.DieMessage()))
        
    def calcBust(self, oVel):
        #Original speed (magnitude of velocity)
        oSpd = bs.Vector(*oVel).length()
        #Now get the dot product of the original velocity and current velocity.
        dot = sum(x*y for x,y in zip(oVel,self.node.velocity))
        if oSpd*oSpd - dot > 50.0:
            #Basically, the more different the dot product from the square of the original
            #velocity vector, the more the ball trajectory changed when it it something.
            #This is the best way I could figure out how "hard" the ball hit. 
            #A difference value was a pretty arbitrary choice.
            #Add a very short timer to allow just a couple of hits.
            bs.gameTimer(50, bs.WeakCall(self.doBust))
            
    def _disappear(self):
        self._exploded = True #don't try to damage stuff anymore because we should be melting.
        if self.exists():
            scl = self.node.modelScale
            bsUtils.animate(self.node,"modelScale",{0:scl*1.0, 300:scl*0.5, 500:0.0})
            bs.gameTimer(550,bs.WeakCall(self.handleMessage,bs.DieMessage()))
            
    def getFactory(cls):
        """
        Returns a shared SnoBallz.SnoBallFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try: return activity._sharedSnoBallFactory
        except Exception:
            f = activity._sharedSnoBallFactory = SnoBallFactory()
            return f            
            
class SnoBallFactory(object):


    def __init__(self):
        """
        Instantiate a SnoBallFactory.
        You shouldn't need to do this; call snoBallz.snoBall.getFactory() to get a shared instance.
        """

        self.texSno = bs.getTexture("bunnyColor")
        self.snoModel = bs.getModel("frostyPelvis")
        self.ballMaterial = bs.Material()
        self.impactSound = bs.getSound('impactMedium')
        #First condition keeps balls from damaging originating player by preventing collisions immediately after they appear.
        #Time is very short due to balls move fast.
        self.ballMaterial.addActions(
            conditions=((('weAreYoungerThan',5),'or',('theyAreYoungerThan',100)),
                        'and',('theyHaveMaterial',bs.getSharedObject('objectMaterial'))),
            actions=(('modifyNodeCollision','collide',False)))
        # we want pickup materials to always hit us even if we're currently not
        # colliding with their node (generally due to the above rule)
        self.ballMaterial.addActions(
            conditions=('theyHaveMaterial',bs.getSharedObject('pickupMaterial')),
            actions=(('modifyPartCollision','useNodeCollide',False)))
        self.ballMaterial.addActions(actions=('modifyPartCollision','friction',0.3))
        #This action disables default physics when the ball hits a spaz. Sends a snoMessage to 
        #itself so that it can try to damage spazzes.
        self.ballMaterial.addActions(conditions=('theyHaveMaterial', bs.getSharedObject('playerMaterial')), actions=(('modifyPartCollision','physical',False),('message', 'ourNode', 'atConnect', snoMessage())))
        #This message sends a different message to our ball just to see if it should bust or not
        self.ballMaterial.addActions(conditions=(
                                                ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
                                                ('theyHaveMaterial', bs.getSharedObject('objectMaterial')), 'or',
                                                ('theyHaveMaterial', bs.getSharedObject('footingMaterial'))),
                                                actions=('message', 'ourNode', 'atConnect', otherHitMessage()))
        #The below can be changed after the factory is created
        self.defaultBallTimeout = 300
        self._ballsMelt = True
        self._ballsBust = True
        self._powerExpire = True
        self._powerLife = 20000
        
    def giveBallz(self,spaz):
        spaz.punchCallback = self.throwBall
        spaz.lastBallTime = bs.getGameTime()
        if self._powerExpire:
            weakSpaz = weakref.ref(spaz)
            spaz.snoExpireTimer = bs.Timer(self._powerLife, bs.WeakCall(self.takeBallz, weakSpaz))

    def takeBallz(self,weakSpaz):
        if not weakSpaz() is None:
            weakSpaz().punchCallback = None
        
    def throwBall(self, spaz):
        t = bs.getGameTime()
        #Figure bomb timeout based on other owned powerups:
        bTime = self.defaultBallTimeout
        if spaz.bombType == 'impact':
            bTime *= 2
        if spaz.bombCount > 1:
            bTime /= 2
        if t - spaz.lastBallTime > bTime:
            spaz.lastBallTime = t
            #Figure out which way spaz is facing
            p1 = spaz.node.positionCenter
            p2 = spaz.node.positionForward
            direction = [p1[0]-p2[0],p2[1]-p1[1],p1[2]-p2[2]]
            direction[1] = 0.03 #This is the upward throw angle
            #Make a velocity vector for the snowball
            mag = 20.0/bsVector.Vector(*direction).length()
            vel = [v * mag for v in direction]
            #print vel
            if spaz.bombType == 'impact':
                explodeIt = True
            else:
                explodeIt = False
            snoBall(spaz.node.position,vel,spaz.getPlayer(),spaz.getPlayer(),explodeIt).autoRetain()
