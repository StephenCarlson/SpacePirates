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

# Critical Timing Parameters
FPS = 60
NETWORK_PERIOD_MS = 50

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
SHIP_IMAGE_FILE			= 'ship.png'
SHIP2_IMAGE_FILE		= 'ship2.png'
GAME_MUSIC_FILE			= 'backgroundMusic.ogg'
# Music File Source:
# 	Stellardrone - 09 - The Edge of Forever
# 	http://www.archive.org/details/Stellardrone-InventTheUniverse
# 	Converted from MP3 to OGG using VLC

# Program and Network Parameters
SCREEN_SIZE = [1024, 600]
WORLD_SIZE = [10000,10000]
UDP_IP = '<broadcast>' # '255.255.255.255'
UDP_PORT = 27016 # 5800 # 27015


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setblocking(0)
sock.bind(('0.0.0.0', UDP_PORT))

PLAYER_ID = random.randint(0,65535)
print "Player ID:\t",PLAYER_ID

print "Local Host:\t",socket.gethostname() # Returns "Accipiter"

OWN_IP_ADDR = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
print "Local IP:\t",OWN_IP_ADDR[0]
print "Using Port:\t",UDP_PORT


class SpaceObject(pygame.sprite.Sprite):
	def __init__(self,img,w=10,h=10):
		pygame.sprite.Sprite.__init__(self,self.containers)
		#self.SURFACE 	= pygame.Surface([0, 0]) if img is None else pygame.image.load(img)
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

		offset = [int(x) for x in vsub(other.pos,self.pos)]
		overlap = self.mask.overlap_area( other.mask,offset )
		if overlap == 0:
			return
		print overlap #,self.pos,other.pos

		nx = (self.mask.overlap_area(other.mask,(offset[0]+1,offset[1])) - self.mask.overlap_area(other.mask,(offset[0]-1,offset[1])))
		ny = (self.mask.overlap_area(other.mask,(offset[0],offset[1]+1)) - self.mask.overlap_area(other.mask,(offset[0],offset[1]-1)))
		if(nx == 0 and ny == 0):
			return
		n = [nx,ny]
		dv = vsub(other.vel,self.vel)
		J = vdot(dv,n)/(2*vdot(n,n))
		if J > 0:
			J *= 1.9
			self.vel[0] += nx*J
			self.vel[1] += ny*J
			other.vel[0] += -J*nx
			other.vel[1] += -J*ny
		return
	
		

class Ship(SpaceObject):
	# SURFACE = pygame.transform.scale(pygame.image.load(SHIP2_IMAGE_FILE), (PLAYER_SIZE_START, PLAYER_SIZE_START))
	def __init__(self, img=SHIP2_IMAGE_FILE,w=PLAYER_SIZE_START, h=PLAYER_SIZE_START):
		SpaceObject.__init__(self,img,w,h)
		# self.image 		= self.SURFACE if img is None else pygame.transform.scale(pygame.image.load(img), (PLAYER_SIZE_START, PLAYER_SIZE_START))
		# s = 
		#self.SURFACE 	= pygame.transform.scale(pygame.image.load(SHIP2_IMAGE_FILE if img==None else img), (PLAYER_SIZE_START, PLAYER_SIZE_START))
		#self.image 		= self.image
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
		
		attenuation = 0.2 if self.verniers else 1.0
		
		
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

		
'''
class Enemy(SpaceObject):
	SURFACE = pygame.transform.scale(pygame.image.load(SHIP_IMAGE_FILE), (PLAYER_SIZE_START, PLAYER_SIZE_START))
	def __init__(self):
		SpaceObject.__init__(self, self.containers)
		self.image 		= self.SURFACE
		self.rect 		= self.image.get_rect()  # pygame.Rect(0,0,PLAYER_SIZE_START,PLAYER_SIZE_START)
		self.rot 		= 0
		self.pos 		= [400,200]
		self.vel 		= [0,0]
		self.power 		= PLAYER_POWER_MAX
		self.mass 		= PLAYER_MASS_START
		self.shooting 	= False
		self.dampeners 	= A_ON
		self.ID			= PLAYER_ID
		self.lastseen	= 0.0
		
		# self.contrail 	= Contrail()
	
	def update(self):
		self.image, self.rect = rotate(self.SURFACE,self.rect, -self.rot)
		
		self.vel = [clamp(self.vel[0],-FLY_MAX,FLY_MAX),clamp(self.vel[1],-FLY_MAX,FLY_MAX)]		
		
		self.pos[0] += (self.vel[0])
		self.pos[1] += (self.vel[1])

		self.pos[0] = roll(self.pos[0],0,SCREEN_SIZE[0])
		self.pos[1] = roll(self.pos[1],0,SCREEN_SIZE[1])
		
		self.rect.centerx = self.pos[0]
		self.rect.centery = self.pos[1]
		
		self.rot = roll(self.rot,0.0,360.0)
'''

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
	# pygame.display.flip() 				# Needed if using Render Method 1

	
	
	
	pygame.display.set_caption("Space Pirates")
	#pygame.display.set_icon(pygame.image.load('gameicon.png'))
	CLOCK = pygame.time.Clock()
	
	#while done==False:
	while True:
		pygame.mixer.music.load(GAME_MUSIC_FILE)
		pygame.mixer.music.play(-1, 0.0)
		run()
		pygame.mixer.music.stop()


def run():	
	all = pygame.sprite.RenderUpdates()
	ships = pygame.sprite.Group()
	shots = pygame.sprite.Group()
	# enemies = pygame.sprite.Group()
	# contrails = pygame.sprite.Group()
	
	Player.containers = all
	Ship.containers = all,ships
	# Enemy.containers = all
	Contrail.containers = all
	player = Player()
	otherPlayer = Ship()
	# enemy = Enemy()
	# debris = []
	#for i in range(20):
		#s = Ship() # SpaceObject()
		#s.pos = [random.uniform(0,SCREEN.get_width()),random.uniform(0,SCREEN.get_height())]
		
		# debris.append(s)
	
	# player2 = Player()
	# contrail = player.contrail
	
	# ships.add(player)
	
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				if event.key in (K_z,K_t): # == (K_z): # 
					player.dampeners = 0 if player.dampeners else 1
				if event.key == (K_CAPSLOCK): # in (K_z,K_t)
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

		for event in pygame.sprite.spritecollide(player,ships,0):
		# for eventDict in pygame.sprite.groupcollide(ships,ships,0,0):
			# print eventDict # for s in eventDict:
				#print s
				# s.collide(e for e in s.values()) 
			player.collide(event)

				
		all.clear(SCREEN, BACKGROUND)
		all.update()
		
		# Render Method 1, faster but with severe clipping with movement
		# dirty = all.draw(SCREEN)
		# pygame.display.update(dirty)
		
		# Render Method 2, must better graphics for reduced preformance
		all.draw(SCREEN)
		pygame.display.flip()
		
		try:
			str, addr = sock.recvfrom(32)
			if(addr[0] != OWN_IP_ADDR[0]):
				data = struct.unpack_from('Hfffff',str)
				# print addr[0],OWN_IP_ADDR[0]
				
				if(data[0] != PLAYER_ID):
					pass
					otherPlayer.rot    = data[1]
					otherPlayer.pos[0] = data[2]
					otherPlayer.pos[1] = data[3]
					otherPlayer.vel[0] = data[4]
					otherPlayer.vel[1] = data[5]
					# print data
					
		except socket.error:
			pass
			# print enemy.pos
		
		CLOCK.tick(FPS)
		
# def networkCall(player,enemy):
	

def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)
	
def roll(n, minb, maxb):
	return n+maxb-minb if n<minb else n-maxb-minb if n>maxb else n
	
def rotate(image, rect, angle):
	# From pybreak360
	rot_image = pygame.transform.rotate(image, angle)
	# w = math.sqrt(rect.width**2 + rect.height**2)
	# rot_rect = rot_image.get_rect(center=rect.center, size=(w,w))
	
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