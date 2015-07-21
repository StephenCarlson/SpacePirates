# Simply Coding "Space Pirates"
# By Steve Carlson June/July 2015
# Referenced Materials:
# 	http://inventwithpython.com/pygame
# 	https://github.com/BYU-MarsRover/Basestation/blob/master/RoverBase.py
# 	PyGame Example Files from C:\Python27\Lib\site-packages\pygame\examples

# Dependencies:
# 	PyGame Library		-- Get this library at http://www.pygame.org/
# 	ship.png, ship2.png -- Arbitrary Space Pirate ship, 64x64 size
# 	backgroundMusic.ogg -- OGG Music file, PyGame barfs on MP3s

# Imports
import pygame, math, sys, collections, socket, os, struct,random
from pygame.locals import *
from array import *
# from socket import *

# Timing Parameters
FPS 					= 60
NETWORK_PERIOD_MS 		= 50

# Gameplay Parameters
PLAYER_SIZE_START		= 40
PLAYER_POWER_MAX		= 100
PLAYER_MASS_START		= 20
DAMP_ACCEL				= 0.2 # 0.2 0.05
FLY_ACCEL				= 0.2
FLY_MAX					= 10.0
TRAIL_LENGTH			= 300

# Constants
A_ON					= 0
A_OFF					= 1
NETWORK_EVENT 			= USEREVENT+1

# Resource Locations
GAME_ICON_IMAGE			= 'gameicon.png'
SHIP_IMAGE_FILE			= 'ship.png'
SHIP2_IMAGE_FILE		= 'ship2.png'
# SHIP_IMAGE_FILE			= 'test.png' # 'ship.png'
# SHIP2_IMAGE_FILE		= 'test.png' # 'ship2.png'
GAME_MUSIC_FILE			= None # 'backgroundMusic.ogg'
# Music File Source:
# 	Stellardrone - 09 - The Edge of Forever
# 	http://www.archive.org/details/Stellardrone-InventTheUniverse
# 	Converted from MP3 to OGG using VLC

# Program and Network Parameters
SCREEN_SIZE 			= [1024, 600]
WORLD_SIZE 				= [10000,10000]
UDP_IP 					= '<broadcast>' # '255.255.255.255'
UDP_PORT 				= 27016 # 5800 # 27015

try:
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setblocking(0)
	sock.bind(('0.0.0.0', UDP_PORT))

	PLAYER_ID = random.randint(0,65535)
	print "Player ID:\t",PLAYER_ID

	print "Local Host:\t",socket.gethostname() # Returns Machine Name

	OWN_IP_ADDR = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
	print "Local IP:\t",OWN_IP_ADDR[0]
	print "Using Port:\t",UDP_PORT

except Exception, e: print str(e)


class SpaceObject(pygame.sprite.Sprite):
	def __init__(self,img,w=10,h=10):
		pygame.sprite.Sprite.__init__(self,self.containers)
		self.SURFACE 	= pygame.transform.scale(pygame.image.load(img), (w, h))
		self.mask		= pygame.mask.from_surface(self.SURFACE, 127)
		self.image 		= self.SURFACE
		self.rect 		= self.image.get_rect()  # pygame.Rect(0,0,PLAYER_SIZE_START,PLAYER_SIZE_START)
		self.rot 		= 0
		self.pos 		= [0,0]
		self.vel 		= [0,0]
		self.acc		= [0,0]
		self.mass		= self.mask.count()
		
	def update(self):
		self.image, self.rect = rotate(self.SURFACE,self.rect, -self.rot)
		self.rot = roll(self.rot,0.0,360.0)
		
		self.vel[0] += (self.acc[0])
		self.vel[1] += (self.acc[1])
		self.vel = [clamp(self.vel[0],-FLY_MAX,FLY_MAX),clamp(self.vel[1],-FLY_MAX,FLY_MAX)]		
		
		self.pos[0] += (self.vel[0])
		self.pos[1] += (self.vel[1])
		
		self.pos[0] = roll(self.pos[0],0,SCREEN_SIZE[0])
		self.pos[1] = roll(self.pos[1],0,SCREEN_SIZE[1])
		
		self.rect.centerx = self.pos[0]
		self.rect.centery = self.pos[1]
		
	def collide(self,other):
		self.mask = pygame.mask.from_surface(self.image, 127)
		otherMask = pygame.mask.from_surface(other.image, 127)
		
		offset = [int(x) for x in vsub(other.pos,self.pos)]
		overlap = self.mask.overlap_area( otherMask,offset ) # other.mask
		if overlap == 0:
			return
		# print overlap #,self.pos,other.pos
		
		nx = (self.mask.overlap_area(otherMask,(offset[0]+1,offset[1])) - self.mask.overlap_area(otherMask,(offset[0]-1,offset[1])))
		ny = (self.mask.overlap_area(otherMask,(offset[0],offset[1]+1)) - self.mask.overlap_area(otherMask,(offset[0],offset[1]-1)))
		if(nx == 0 and ny == 0):
			return
		n = [nx,ny]
		dv = vsub(other.vel,self.vel)
		J = vdot(dv,n)/(2*vdot(n,n))
		if J > 0:
			J *= 0.8 # 1.9
			self.vel[0] += nx*J
			self.vel[1] += ny*J
			other.vel[0] += -J*nx
			other.vel[1] += -J*ny
		return
	
	
class Ship(SpaceObject):
	def __init__(self, img=SHIP2_IMAGE_FILE,w=PLAYER_SIZE_START, h=PLAYER_SIZE_START):
		SpaceObject.__init__(self,img,w,h)
		self.power 		= PLAYER_POWER_MAX
		self.mass 		= PLAYER_MASS_START
		self.shooting 	= False
		
		self.pos = [random.uniform(0,SCREEN.get_width()),random.uniform(0,SCREEN.get_height())]		
		
		self.ID			= random.randint(0,65535)
		
	def update(self):
		SpaceObject.update(self)
		
		
class Player(Ship):
	def __init__(self):
		Ship.__init__(self, img=SHIP_IMAGE_FILE)
		self.dampeners 	= A_ON
		self.verniers 	= A_OFF
		self.mouseNav	= False
		
		self.pos[0] = SCREEN_SIZE[0]/2
		self.pos[1] = SCREEN_SIZE[1]/2
		
		
		self.ID			= PLAYER_ID
		
	def update(self):
		Ship.update(self)
		
		keystate = pygame.key.get_pressed()
		cmdVec = [(keystate[K_d]-keystate[K_a]),(max(keystate[K_w],keystate[K_UP])-max(keystate[K_s],keystate[K_DOWN]))] # x,y -> [-1.0:1.0]
		# Optional: Normalize to length=1
		
		xComp = cmdVec[0]*math.cos(math.radians(self.rot)) + cmdVec[1]*math.sin(math.radians(self.rot))
		yComp = cmdVec[0]*math.sin(math.radians(self.rot)) - cmdVec[1]*math.cos(math.radians(self.rot))
		
		
		mVec = [xComp,yComp]
		
		attenuation = 0.2 if self.verniers==A_ON else 1.0
		
		
		self.acc[0] = (mVec[0]*FLY_ACCEL*attenuation)
		self.acc[1] = (mVec[1]*FLY_ACCEL*attenuation)
		
		# self.contrail.append(self.rect)
		
		mouseCoords = pygame.mouse.get_pos()
		
		dxx = mouseCoords[0]-self.pos[0]
		dyy = mouseCoords[1]-self.pos[1]
		
		if True in (keystate[K_RIGHT],keystate[K_LEFT],keystate[K_q],keystate[K_e],):
			self.mouseNav = 0
		
		mouseRotation = ( math.degrees( math.atan2(dxx,-dyy) ) )
		keysRotation = self.rot + ((keystate[K_RIGHT]-keystate[K_LEFT]+keystate[K_e]-keystate[K_q])*5.0)
		self.rot = mouseRotation if self.mouseNav else keysRotation
		
		
class Contrail(SpaceObject):
	def __init__(self):
		# Can also use super().__init__()
		SpaceObject.__init__(self, self.containers)
		self.trail = collections.deque(TRAIL_LENGTH*[pygame.Rect(0,0,0,0)],TRAIL_LENGTH) # From http://stackoverflow.com/questions/1931589
		self.image = pygame.draw.circle(SCREEN,(20,20,20),[200,200],10,)
		self.rect = self.image.get_rect()
		# print containers
		
		
	def append(self,inRect):
		# print inRect
		newRect = inRect.inflate(-15,-15)
		self.trail.appendleft(newRect)
		
	def update(self):
		#pygame.draw.lines(SCREEN,(0,0,0),False,trail,)
		print self.trail[0][0] #len(trail)
		# for p in reversed(range(len(trail))):
			# contrailCoord = [0,0] #[trail[p].centerx,trail[p].centery]
			# contrailWidth = int(((TRAIL_LENGTH-p)*10/TRAIL_LENGTH)) if (p>2) else 0
			# contrailColor = (24,24,((TRAIL_LENGTH-p)/4)+24)
			# pygame.draw.circle(SCREEN,contrailColor,contrailCoord,contrailWidth,)
			# pygame.draw.ellipse(SCREEN,(24,24,((TRAIL_LENGTH-p)/4)+24),trail[p])
			
			
# class TargetReticle(SpaceObject):
	# def __init__(self):
		# pygame.sprite.Sprite.__init__(self, self.containers)
		# pygame.draw.line(SCREEN,(0,0,0),(player.pos[0],player.pos[1]),mouseCoords)



'''
class Shot(pygame.sprite.Sprite):
	def __init__(self):
class Explosion(pygame.sprite.Sprite):
	def __init__(self):
class PowerUp(pygame.sprite.Sprite):
	def __init__(self):
class MusicLevel(pygame.sprite.Sprite):
	def __init__(self):
class Status(pygame.sprite.Sprite):
	def __init__(self):

'''



def main():
	global SCREEN, BACKGROUND, CLOCK
	pygame.init()
	pygame.time.set_timer(NETWORK_EVENT, NETWORK_PERIOD_MS)
	SCREEN = pygame.display.set_mode(SCREEN_SIZE)
	BACKGROUND = pygame.Surface(SCREEN.get_size())
	# BACKGROUND = BACKGROUND.convert() 	# Use when displaying images?
	BACKGROUND.fill((24, 24, 24))
	SCREEN.blit(BACKGROUND, (0,0))

	pygame.display.set_caption("Space Pirates")
	pygame.display.set_icon(pygame.image.load(GAME_ICON_IMAGE))
	CLOCK = pygame.time.Clock()
	
	while True:
		# if GAME_MUSIC_FILE is not None:
		try:
			pygame.mixer.music.load(GAME_MUSIC_FILE)
			pygame.mixer.music.play(-1, 0.0)
		except Exception,e: print str(e)
		
		run()


def run():	
	all = pygame.sprite.RenderUpdates()
	objects = pygame.sprite.Group()
	shots = pygame.sprite.Group()
	contrails = pygame.sprite.Group()
	
	Player.containers = all, objects
	Ship.containers = all, objects
	#Shot.containers = all, shots
	Contrail.containers = all, contrails
	
	player = Player()
	otherPlayers = {} #dict() # [] # Ship()
	# debris = []
	
	
	'''
	for i in range(10):
		newShip = Ship()
		newID = random.randint(0,65535)
		newShip.ID = newID
		newShip.pos = [random.uniform(0,SCREEN.get_width()),random.uniform(0,SCREEN.get_height())]
		newShip.rot = random.uniform(0,360)
		otherPlayers[newID] = newShip
	'''
	
	# contrail = player.contrail
	
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				if event.key in (K_z,K_t): # == (K_z): # 
					player.dampeners = A_OFF if player.dampeners else A_ON
				elif event.key == (K_CAPSLOCK): # in (K_z,K_t)
					player.verniers = 0 if player.verniers else 1
				elif event.key == (K_r):
					player.rot = 0
					player.vel = [0,0]
					
				elif event.key == (K_SPACE):
					player.shooting = True
				elif event.key in (K_MINUS,K_EQUALS,K_BACKSPACE): # and useMusic == True
					if event.key == (K_BACKSPACE):
						pygame.mixer.music.stop()
					else:
						playing = pygame.mixer.music.get_busy() # Checks if music is playing
						volume = pygame.mixer.music.get_volume()
						if event.key == (K_EQUALS):
							if not playing:
								pygame.mixer.music.play(-1, 0.0)
							volume = clamp(volume+0.1,0.0,1.0)
						else: # Can only be the K_MINUS key
							volume = clamp(volume-0.1,0.0,1.0)
						pygame.mixer.music.set_volume(volume)
						print volume
			elif event.type == MOUSEBUTTONDOWN:
				#print event.button
				if event.button == (3):
					player.mouseNav = 0 if player.mouseNav else 1  # 0 if player.mouseNav else
			elif event.type == NETWORK_EVENT:
				payload = struct.pack('Hfffff',player.ID,float(player.rot),float(player.pos[0]),float(player.pos[1]),float(player.vel[0]),float(player.vel[1]))
				sock.sendto(payload, (UDP_IP, UDP_PORT))

		for item in objects:
			#print ship.ID
			for encounter in pygame.sprite.spritecollide(item,objects,0):
				# print encounter
				item.collide(encounter)
				

				
		all.clear(SCREEN, BACKGROUND)
		all.update()
		
		all.draw(SCREEN)
		pygame.display.flip()
		
		networkUpdate(otherPlayers);

		CLOCK.tick(FPS)


def networkUpdate(playerDict):
	
	# pass
	# Training / Simulation
	#for i in playerDict:
	#	playerDict[i].vel = [playerDict[i].vel[0]+random.uniform(-0.1,0.1),playerDict[i].vel[1]+random.uniform(-0.1,0.1)]
	#	playerDict[i].rot += random.uniform(-1,1)
		
		# print i,otherPlayers[i]
		
	#print otherPlayers
	
	
	# Actual Code for Network Play
	
	try:
		payload, addr = sock.recvfrom(32)
		if(addr[0] != OWN_IP_ADDR[0]):
			data = struct.unpack_from('Hfffff',payload)
			playerID = data[0]
			# print addr[0],OWN_IP_ADDR[0]
			
			if(playerID != PLAYER_ID):
				# pass
				if(playerDict.has_key(playerID)):
					# playerDict[playerID] = playerDict()
					playerDict[playerID].rot    = data[1]
					playerDict[playerID].pos[0] = data[2]
					playerDict[playerID].pos[1] = data[3]
					playerDict[playerID].vel[0] = data[4]
					playerDict[playerID].vel[1] = data[5]
				else:
					newPlayer = Ship()
					newPlayer.rot    = data[1]
					newPlayer.pos[0] = data[2]
					newPlayer.pos[1] = data[3]
					newPlayer.vel[0] = data[4]
					newPlayer.vel[1] = data[5]
					playerDict.append(newPlayer)
					
	except socket.error,e:
		pass
		# print str(e)
		


def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)
	
def roll(n, minb, maxb):
	return n+maxb-minb if n<minb else n-maxb-minb if n>maxb else n
	
def rotate(image, rect, angle):
	rot_image = pygame.transform.rotate(image, angle)
	rot_rect = rot_image.get_rect(center=rect.center)

	return rot_image,rot_rect

def norm(vect):
	return math.sqrt(vect[0]*vect[0]+vect[1]*vect[1])
	
def vadd(x,y):
    return [x[0]+y[0],x[1]+y[1]]

def vsub(x,y):
    return [x[0]-y[0],x[1]-y[1]]

def vdot(x,y):
    return x[0]*y[0]+x[1]*y[1]
	
if __name__ == '__main__':
    main()