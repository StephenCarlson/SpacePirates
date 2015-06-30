# Simply Coding "Space Pirates"
# By Steve Carlson June/July 2015
# Referenced Materials:
# 	http://inventwithpython.com/pygame
# 	https://github.com/BYU-MarsRover/Basestation/blob/master/RoverBase.py
# 	PyGame Example Files from C:\Python27\Lib\site-packages\pygame\examples

# Dependencies:
# 	PyGame Library		-- Get this library at http://www.pygame.org/
# 	ship.png			-- Arbitrary Space Pirate ship, 64x64 size
# 	backgroundMusic.ogg -- OGG Music file, PyGame barfs on MP3s


import pygame, math, sys, collections, socket, os, struct,random
from pygame.locals import *
from array import *
# from socket import *

FPS = 60

PLAYER_SIZE_START		= 40
PLAYER_POWER_MAX		= 100
PLAYER_MASS_START		= 20
DAMP_OFF				= 0
DAMP_ON					= 1
DAMP_ACCEL				= 0.2 # 0.2 0.05
FLY_ACCEL				= 0.2
FLY_MAX					= 10.0
TRAIL_LENGTH			= 300

SHIP_IMAGE_FILE			= 'ship.png'
GAME_MUSIC_FILE			= 'backgroundMusic.ogg'
# Music File Source:
# 	Stellardrone - 09 - The Edge of Forever
# 	http://www.archive.org/details/Stellardrone-InventTheUniverse
# 	Converted from MP3 to OGG using VLC


SCREEN_SIZE = [1024, 600]
WORLD_SIZE = [10000,10000]
NETWORK_EVENT = USEREVENT+1



UDP_IP = '<broadcast>' # '255.255.255.255'
UDP_PORT = 27016 # 5800 # 27015

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setblocking(0)
# sock.settimeout(0.1)

sock.bind(('0.0.0.0', UDP_PORT))


OFFLINE = 0
HOST 	= 1
CLIENT	= 2

PLAYER_ID = random.randint(0,65535)
print "Player ID:\t",PLAYER_ID

print "Local Host:\t",socket.gethostname() # Returns "Accipiter"
# print([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
# print os.popen("ipconfig").read()
# print socket.gethostbyname_ex(socket.gethostname())[2]
# print [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
OWN_IP_ADDR = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
print "Local IP:\t",OWN_IP_ADDR[0]
print "Using Port:\t",UDP_PORT

class Player(pygame.sprite.Sprite):
	# PLAYER_SHIP_IMG = pygame.image.load(SHIP_IMAGE_FILE)
	SURFACE = pygame.transform.scale(pygame.image.load(SHIP_IMAGE_FILE), (PLAYER_SIZE_START, PLAYER_SIZE_START))
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.image 		= self.SURFACE
		self.rect 		= self.image.get_rect()  # pygame.Rect(0,0,PLAYER_SIZE_START,PLAYER_SIZE_START)
		# self.size 		= PLAYER_SIZE_START
		self.rot 		= 0
		self.pos 		= [200,200]
		self.vel 		= [0,0]
		self.power 		= PLAYER_POWER_MAX
		self.mass 		= PLAYER_MASS_START
		self.shooting 	= False
		self.dampeners 	= DAMP_ON
		self.mouseNav	= False
		
		self.ID			= PLAYER_ID
		
		# self.contrail 	= Contrail()
	
	def update(self):
		self.image, self.rect = rotate(self.SURFACE,self.rect, -self.rot)
		
		keystate = pygame.key.get_pressed()
		cmdVec = [(keystate[K_d]-keystate[K_a]),(max(keystate[K_w],keystate[K_UP])-max(keystate[K_s],keystate[K_DOWN]))] # x,y -> [-1.0:1.0]
		# Optional: Normalize to length=1
				
		xComp = cmdVec[0]*math.cos(math.radians(self.rot)) + cmdVec[1]*math.sin(math.radians(self.rot))
		yComp = cmdVec[0]*math.sin(math.radians(self.rot)) - cmdVec[1]*math.cos(math.radians(self.rot))
		
		
		mVec = [xComp,yComp]
	
		# Not properly scaled for 2D vectors, total ignorant approach
		# if( self['dampeners'] == 1):
			# if math.fabs(self['dx'])<=DAMP_ACCEL: self['dx'] = 0 
			# else: self['dx'] -= math.copysign(DAMP_ACCEL,self['dx'])
			# if math.fabs(self['dy'])<=DAMP_ACCEL: self['dy'] = 0 
			# else: self['dy'] -= math.copysign(DAMP_ACCEL,self['dy'])
			
		#if( self['dampeners'] == 1):
			
		
		
		self.vel = [clamp(self.vel[0],-FLY_MAX,FLY_MAX),clamp(self.vel[1],-FLY_MAX,FLY_MAX)]		
			
		self.vel[0] += (mVec[0]*FLY_ACCEL)
		self.vel[1] += (mVec[1]*FLY_ACCEL)
		
		self.pos[0] += (self.vel[0])
		self.pos[1] += (self.vel[1])
		
		
		# self['x'] += (mVec[0]*FLY_ACCEL)
		# self['y'] += (mVec[1]*FLY_ACCEL)
		
		self.pos[0] = roll(self.pos[0],0,SCREEN_SIZE[0])
		self.pos[1] = roll(self.pos[1],0,SCREEN_SIZE[1])
		
		self.rect.centerx = self.pos[0]
		self.rect.centery = self.pos[1]
		
		# self.contrail.append(self.rect)
		
		mouseCoords = pygame.mouse.get_pos()
		
		dxx = mouseCoords[0]-self.pos[0]
		dyy = mouseCoords[1]-self.pos[1]
		
		if True in (keystate[K_RIGHT],keystate[K_LEFT],keystate[K_q],keystate[K_e],):
			self.mouseNav = 0
		
		mouseRotation = ( math.degrees( math.atan2(dxx,-dyy) ) )
		keysRotation = self.rot + ((keystate[K_RIGHT]-keystate[K_LEFT]+keystate[K_e]-keystate[K_q])*5.0)
		self.rot = mouseRotation if self.mouseNav else keysRotation
		
		self.rot = roll(self.rot,0.0,360.0)
		
class Enemy(pygame.sprite.Sprite):
	SURFACE = pygame.transform.scale(pygame.image.load(SHIP_IMAGE_FILE), (PLAYER_SIZE_START, PLAYER_SIZE_START))
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.image 		= self.SURFACE
		self.rect 		= self.image.get_rect()  # pygame.Rect(0,0,PLAYER_SIZE_START,PLAYER_SIZE_START)
		self.rot 		= 0
		self.pos 		= [400,200]
		self.vel 		= [0,0]
		self.power 		= PLAYER_POWER_MAX
		self.mass 		= PLAYER_MASS_START
		self.shooting 	= False
		self.dampeners 	= DAMP_ON
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
		
		
# class TargetReticle(pygame.sprite.Sprite):
	# def __init__(self):
		# pygame.sprite.Sprite.__init__(self, self.containers)
		# pygame.draw.line(SCREEN,(0,0,0),(player.pos[0],player.pos[1]),mouseCoords)


class Contrail(pygame.sprite.Sprite):
	def __init__(self):
		# Can also use super().__init__()
		pygame.sprite.Sprite.__init__(self, self.containers)
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
	global SCREEN, BACKGROUND, CLOCK, PLAYER_SHIP_IMG
	pygame.init()
	pygame.time.set_timer(NETWORK_EVENT, 100)
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
	gameType = HOST
	
	all = pygame.sprite.RenderUpdates()
	ships = pygame.sprite.Group()
	shots = pygame.sprite.Group()
	contrails = pygame.sprite.Group()
	
	Player.containers = all
	Enemy.containers = all
	Contrail.containers = all
	player = Player()
	enemy = Enemy()
	# player2 = Player()
	# contrail = player.contrail
	
	# ships.add(player)
	
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				if event.key == (K_z):
					player.dampeners = 0 if player.dampeners else 1
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
				payload = array('f') # 'B'

				# for x in [float(player.rot),float(player.vel[0]),float(player.vel[1])]:
				# payload.fromlist([float(player.rot),float(player.vel[0]),float(player.vel[1])])
				payload = struct.pack('Hfffff',player.ID,float(player.rot),float(player.pos[0]),float(player.pos[1]),float(player.vel[0]),float(player.vel[1]))
				sock.sendto(payload, (UDP_IP, UDP_PORT))

				try:
					str, addr = sock.recvfrom(32)
					if(addr[0] != OWN_IP_ADDR[0]):
						data = struct.unpack_from('Hfffff',str)
						# print addr[0],OWN_IP_ADDR[0]
						
						if(data[0] != PLAYER_ID):
							enemy.rot    = data[1]
							enemy.pos[0] = data[2]
							enemy.pos[1] = data[3]
							enemy.vel[0] = data[4]
							enemy.vel[1] = data[5]
							print data
							
				except socket.error:
					pass
					# print enemy.pos

				
		all.clear(SCREEN, BACKGROUND)
		all.update()
		
		# Render Method 1, faster but with severe clipping with movement
		# dirty = all.draw(SCREEN)
		# pygame.display.update(dirty)
		
		# Render Method 2, must better graphics for reduced preformance
		all.draw(SCREEN)
		pygame.display.flip()
		
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
		
if __name__ == '__main__':
    main()