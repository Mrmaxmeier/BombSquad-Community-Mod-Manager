import bs


class RaceTimer:
    """Basicly the onscreen timer from bsRace..."""
    def __init__(self, incTime=1000):
        
        lightY = 150

        self.pos = 0

        self._beep1Sound = bs.getSound('raceBeep1')
        self._beep2Sound = bs.getSound('raceBeep2')

        self.lights = []
        for i in range(4):
            l = bs.newNode('image',
                           attrs={'texture':bs.getTexture('nub'),
                                  'opacity':1.0,
                                  'absoluteScale':True,
                                  'position':(-75+i*50,lightY),
                                  'scale':(50,50),
                                  'attach':'center'})
            self.lights.append(l)

        self.lights[0].color = (0.2,0,0)
        self.lights[1].color = (0.2,0,0)
        self.lights[2].color = (0.2,0.05,0)
        self.lights[3].color = (0.0,0.3,0)


        self.cases = {1: self._doLight1, 2: self._doLight2, 3: self._doLight3, 4: self._doLight4}
        self.incTimer = None
        self.incTime = incTime

    def start(self):
        self.incTimer = bs.Timer(self.incTime, bs.WeakCall(self.increment), timeType="game", repeat=True)

    def _doLight1(self):
        self.lights[0].color = (1.0,0,0)
        bs.playSound(self._beep1Sound)
    def _doLight2(self):
        self.lights[1].color = (1.0,0,0)
        bs.playSound(self._beep1Sound)
    def _doLight3(self):
        self.lights[2].color = (1.0,0.3,0)
        bs.playSound(self._beep1Sound)
    def _doLight4(self):
        self.lights[3].color = (0.0,1.0,0)
        bs.playSound(self._beep2Sound)
        for l in self.lights:
            bs.animate(l,'opacity',{0: 1.0, 1000: 0.0})
            bs.gameTimer(int(1000),l.delete)
        self.incTimer = None
        self.onFinish()
        del self

    def onFinish(self): pass
    def onIncrement(self): pass

    def increment(self):
        self.pos += 1
        if self.pos in self.cases:
            self.cases[self.pos]()
        self.onIncrement()
