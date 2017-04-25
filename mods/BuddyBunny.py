import bsSpaz
import bs
import bsUtils
import weakref
import random

class BunnyBuddyBot(bsSpaz.SpazBot):
    """
    category: Bot Classes
    
    A speedy attacking melee bot.
    """

    color=(1,1,1)
    highlight=(1.0,0.5,0.5)
    character = 'Easter Bunny'
    punchiness = 1.0
    run = True
    bouncy = True
    defaultBoxingGloves = True
    chargeDistMin = 1.0
    chargeDistMax = 9999.0
    chargeSpeedMin = 1.0
    chargeSpeedMax = 1.0
    throwDistMin = 3
    throwDistMax = 6
    pointsMult = 2
    
    def __init__(self,player):
        """
        Instantiate a spaz-bot.
        """
        self.color = player.color
        self.highlight = player.highlight
        bsSpaz.Spaz.__init__(self,color=self.color,highlight=self.highlight,character=self.character,
                      sourcePlayer=None,startInvincible=False,canAcceptPowerups=False)

        # if you need to add custom behavior to a bot, set this to a callable which takes one
        # arg (the bot) and returns False if the bot's normal update should be run and True if not
        self.updateCallback = None
        self._map = weakref.ref(bs.getActivity().getMap())

        self.lastPlayerAttackedBy = None # FIXME - should use empty player-refs
        self.lastAttackedTime = 0
        self.lastAttackedType = None
        self.targetPointDefault = None
        self.heldCount = 0
        self.lastPlayerHeldBy = None # FIXME - should use empty player-refs here
        self.targetFlag = None
        self._chargeSpeed = 0.5*(self.chargeSpeedMin+self.chargeSpeedMax)
        self._leadAmount = 0.5
        self._mode = 'wait'
        self._chargeClosingIn = False
        self._lastChargeDist = 0.0
        self._running = False
        self._lastJumpTime = 0    
        
class BunnyBotSet(bsSpaz.BotSet):
    """
    category: Bot Classes
    
    A container/controller for one or more bs.SpazBots.
    """
    def __init__(self, sourcePlayer):
        """
        Create a bot-set.
        """
        # we spread our bots out over a few lists so we can update them in a staggered fashion
        self._botListCount = 5
        self._botAddList = 0
        self._botUpdateList = 0
        self._botLists = [[] for i in range(self._botListCount)]
        self._spawnSound = bs.getSound('spawn')
        self._spawningCount = 0
        self.startMovingBunnies()
        self.sourcePlayer = sourcePlayer
        

    def doBunny(self):
        self.spawnBot(BunnyBuddyBot, self.sourcePlayer.actor.node.position, 2000, self.setupBunny)
        
    def startMovingBunnies(self):
        self._botUpdateTimer = bs.Timer(50,bs.WeakCall(self._bUpdate),repeat=True)
        
    def _spawnBot(self,botType,pos,onSpawnCall):
        spaz = botType(self.sourcePlayer)
        bs.playSound(self._spawnSound,position=pos)
        spaz.node.handleMessage("flash")
        spaz.node.isAreaOfInterest = 0
        spaz.handleMessage(bs.StandMessage(pos,random.uniform(0,360)))
        self.addBot(spaz)
        self._spawningCount -= 1
        if onSpawnCall is not None: onSpawnCall(spaz)
        
    def _bUpdate(self):

        # update one of our bot lists each time through..
        # first off, remove dead bots from the list
        # (we check exists() here instead of dead.. we want to keep them around even if they're just a corpse)

        try:
            botList = self._botLists[self._botUpdateList] = [b for b in self._botLists[self._botUpdateList] if b.exists()]
        except Exception:
            bs.printException("error updating bot list: "+str(self._botLists[self._botUpdateList]))
        self._botUpdateList = (self._botUpdateList+1)%self._botListCount

        # update our list of player points for the bots to use
        playerPts = []

        try:
            #if player.isAlive() and not (player is self.sourcePlayer):
            #    playerPts.append((bs.Vector(*player.actor.node.position),
            #                     bs.Vector(*player.actor.node.velocity)))
            for n in bs.getNodes():
                if n.getNodeType() == 'spaz':
                    s = n.getDelegate()
                    if isinstance(s,bsSpaz.SpazBot):
                        if not s in self.getLivingBots():
                            if hasattr(s, 'sourcePlayer'):
                                if not s.sourcePlayer is self.sourcePlayer:
                                    playerPts.append((bs.Vector(*n.position), bs.Vector(*n.velocity)))
                            else:
                                playerPts.append((bs.Vector(*n.position), bs.Vector(*n.velocity)))
                    elif isinstance(s, bsSpaz.PlayerSpaz):
                        if not (s.getPlayer() is self.sourcePlayer):
                            playerPts.append((bs.Vector(*n.position), bs.Vector(*n.velocity)))
        except Exception:
            bs.printException('error on bot-set _update')

        for b in botList:
            b._setPlayerPts(playerPts)
            b._updateAI()
    def setupBunny(self, spaz):
        spaz.sourcePlayer = self.sourcePlayer
        spaz.color = self.sourcePlayer.color
        spaz.highlight = self.sourcePlayer.highlight
        self.setBunnyText(spaz)
    def setBunnyText(self, spaz):
        m = bs.newNode('math', owner=spaz.node, attrs={'input1': (0, 0.7, 0), 'operation': 'add'})
        spaz.node.connectAttr('position', m, 'input2')
        spaz._bunnyText = bs.newNode('text',
                                      owner=spaz.node,
                                      attrs={'text':self.sourcePlayer.getName(),
                                             'inWorld':True,
                                             'shadow':1.0,
                                             'flatness':1.0,
                                             'color':self.sourcePlayer.color,
                                             'scale':0.0,
                                             'hAlign':'center'})
        m.connectAttr('output', spaz._bunnyText, 'position')
        bs.animate(spaz._bunnyText, 'scale', {0: 0.0, 1000: 0.01})

