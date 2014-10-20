# from Phramework.phramework import gameloop
# from Phramework.gameobj import *
from thinkbayes2 import Suite, EvalNormalPdf
import random, pygame, time
from util import *

OCEAN_SIZE = (50, 50)
SCALE_FACTOR = 30


class Boat:
    _fire_radius = 15.0   # Nodes
    _max_speed = 1     # Nodes/sec
    _max_accel = .2     # Nodes/sec^2
    _turn_speed = 60.0    # Degrees/sec

    def __init__(self, pos=None, heading=None, speed=None, center=None, image_path=None):
        if not pos and not pos == 0:
            pos = tuple(random.random() * OCEAN_SIZE[i] for i in range(2))

        if not heading and not heading == 0:
            heading = random.random() * 360.0

        self.pos = pos
        self.heading = heading
        if not speed == 0:
            speed = Boat._max_speed

        self.dir = 1
        self.speed = speed

        if center:
            self.center = center

        if image_path:
            self.image = pygame.image.load(image_path + ".png")

    def update(self, dt, delSpeed, delHeading):
        # Update position
        vel = vectorMul(calcVel(self.speed, self.heading), dt)
        new_pos = vectorAdd(self.pos, vel)

        if inBounds(new_pos, OCEAN_SIZE):
            self.pos = new_pos
        else:
            # This will stutter right now. Needs fix.
            self.dir = - self.dir

        # Update speed
        new_speed = self.speed + delSpeed * dt
        if inBounds(new_speed, Boat._max_speed):
            self.speed = new_speed

        # Update heading
        self.heading += delHeading * dt

    def input(self):
        delSpeed = self.dir * Boat._max_accel
        delHeading = (random.random() - .5) * 2 * Boat._turn_speed
        return delSpeed, delHeading

    def getPos(self):
        return self.pos

    def __str__(self):
        return "Position: {}, Heading: {}, Speed: {}".format(self.pos, self.heading, self.speed)

class PlayerBoat(Boat):
    def fire(self, shot_pos, enemy):
        shot_pos = (shot_pos[0] + self.pos[0], shot_pos[1] + self.pos[1])
        if distance(shot_pos, self.pos) < Boat._fire_radius:
                enemy_pos = enemy.getPos()
                error = distance(shot_pos, self.pos) + distance(enemy_pos, shot_pos)
                dist_mean = distance(enemy_pos, shot_pos)
                return shot_pos, random.gauss(dist_mean, error), error

    def input(self):
        delSpeed = 0
        delHeading = 0

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            delSpeed += Boat._max_accel
        if keys[pygame.K_s]:
            delSpeed -= Boat._max_accel

        if keys[pygame.K_a]:
            delHeading -= Boat._turn_speed
        if keys[pygame.K_d]:
            delHeading += Boat._turn_speed

        return delSpeed, delHeading

    def getRenderData(self):
        img = pygame.transform.rotate(self.image, -self.heading)
        size = img.get_size()
        return [(img, vectorSub(self.center, vectorMul(size, .5)))]


class Sonar:
    def __init__(self, image_path, position):
        self.image = pygame.image.load(image_path + ".png")
        self.position = position
        w, h = self.image.get_size()
        self.render_pos = (position[0]-w/2, position[1]-w/2)

    def getRenderData(self):
        return [(self.image, self.render_pos)]

    def getRadius(self):
        return min(self.image.get_size())/2 - 30


class PingField(Suite):
    def __init__(self, image_path, center, radius):
        locations = [(x, y) for x in xrange(OCEAN_SIZE[0]) for y in xrange(OCEAN_SIZE[1])]
        super(PingField, self).__init__(locations)
        self.image = pygame.image.load(image_path + ".png")
        self.center = center
        self.radius = radius

        w, h = self.image.get_size()
        m_size = (2*w/3, 2*h/3)
        s_size = (w/3, h/3)

        self.lrg_img = self.image
        self.med_img = pygame.transform.smoothscale(self.image, m_size)
        self.sml_img = pygame.transform.smoothscale(self.image, s_size)

    def Likelihood(self, data, hypo):
        # Unpack Variables
        ship_location = hypo
        shot_location, mean_distance, error = data

        # Calculate Distance from Hypo Point
        d = distance(shot_location, ship_location)

        # Evaluate Normal Distribution near Ship
        return EvalNormalPdf(d, mean_distance, error)

    def getRenderData(self, local_center):
        render_data = []
        m = self.Prob(self.MaximumLikelihood())
        for loc, prob in self.Items():
            # Center around ship
            loc = (local_center[0]-loc[0], local_center[1]-loc[1])

            # Convert model location to screen location
            loc = (loc[0]*SCALE_FACTOR + self.center[0], loc[1]*SCALE_FACTOR + self.center[1])

            if distance(loc, self.center) < self.radius:
                img = pygame.transform.smoothscale(self.image, (int(prob*SCALE_FACTOR/(2*m)), int(prob*SCALE_FACTOR/(2*m))))

                if img:
                    render_data.append((img, loc))

        return render_data


def render(screen, data):
    screen.fill((150, 150, 150))

    for datum in data:
        screen.blit(datum[0], datum[1])

    pygame.display.flip()


if __name__ == "__main__":
    SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    S_WIDTH, S_HEIGHT = SCREEN.get_size()
    S_CENTER = (S_WIDTH/2, S_HEIGHT/2)
    KEYMAP = {pygame.K_ESCAPE: exit}

    enemy_boat = Boat()
    player_boat = PlayerBoat((24.0, 24.0), 0.0, 0.0, S_CENTER, "boat_icon")
    sonar_dial = Sonar("sonar_base", S_CENTER)
    dial_radius = sonar_dial.getRadius()
    ping_field = PingField("ping", S_CENTER, dial_radius)

    t = 0.0
    dt = 0.01

    current_time = time.clock()
    accumulator = 0.0

    while True:
        # Update clock
        new_time = time.clock()
        frame_time = new_time - current_time
        # Cut losses at 1/4 second
        if frame_time > 0.25:
            frame_time = 0.25
        current_time = new_time
        accumulator += frame_time

        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in KEYMAP:
                    KEYMAP[event.key]()
            if event.type == pygame.MOUSEBUTTONDOWN:
                model_pos = ((event.pos[0]-S_WIDTH/2)/SCALE_FACTOR, (event.pos[1] - S_HEIGHT/2)/SCALE_FACTOR)
                shot_data = player_boat.fire(model_pos, enemy_boat)
                if shot_data:
                    ping_field.Update(shot_data)

        # Update Model
        while accumulator >= dt:
            player_boat.update(dt, *player_boat.input())
            enemy_boat.update(dt, *enemy_boat.input())
            t += dt
            accumulator -= dt

        alpha = accumulator / dt

        render(SCREEN, sonar_dial.getRenderData() + player_boat.getRenderData() + ping_field.getRenderData(player_boat.getPos()))
