import math
import numpy as np
import time
import pygame
from config import format_message

class FloodVisualizer:
    # Resolution of pygame window, can reduce for performance
    RES = 1024
    # RES = 1536
    USEGRAYSCALE = False  # Set true to improve performance
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.RATIO = self.RES // simulator.grid_size
        assert(self.RES % simulator.grid_size == 0)  # Must be divisible
        
        pygame.init()
        self.screen = pygame.display.set_mode([self.RES, self.RES])
        
    def tocolor(self, I, cutoff):
        if self.USEGRAYSCALE:
            Ig = (I * 0.6) + 0.4
            Ig[I < cutoff] = 0.2
            return (255 * np.stack([Ig, Ig, Ig], axis=-1)).astype(np.uint8)
        else: 
            A = -np.sin(I * 2.5 + 0.7)
            B = -np.cos(I * 2.5 + 0.7) 
            A[I < cutoff] = 0.
            B[I < cutoff] = -1.

            X = 0.8 + A / 5.
            Z = 0.8 - B / 2.
            Xif = (X > 0.2069).astype(float)
            Zif = (Z > 0.2069).astype(float)
            X = (X ** 3) * Xif + (0.1284 * (X - 0.1379)) * (1. - Xif)
            Z = (Z ** 3) * Zif + (0.1284 * (Z - 0.1379)) * (1. - Zif)
            Y = np.ones_like(I) * (0.8 ** 3)

            R =  3.2404542*X - 1.5371385*Y - 0.4985314*Z
            G = -0.9692660*X + 1.8760108*Y + 0.0415560*Z
            B =  0.0556434*X - 0.2040259*Y + 1.0572252*Z

            R = np.clip(R, 0, 1)
            G = np.clip(G, 0, 1)
            B = np.clip(B, 0, 1)

            R = np.sqrt(R)
            G = np.sqrt(G)
            B = np.sqrt(B)

            return (255 * np.stack([R, G, B], axis=-1)).astype(np.uint8)
            
    def run(self):
        simulator = self.simulator
        grid_size = simulator.grid_size
        
        VIEW_POS = np.array([0.5,0.5])  # location of center of view
        SCALE = self.RATIO
        INTSCALE = round(SCALE)  # number of pixels per square

        steps = 0
        ticks = 0

        SIM_RATE = 3.
        MOUSE_DRAG = False
        MOUSE_POS = [0, 0]
        active = True  # Whether pygame is running
        ticking = False  # Whether flood is running
        halts = False  # Whether flood halted

        terrain = np.tile(simulator.terrain, [2, 2]) / simulator.max_height

        while active:
            starttime = time.time()
            INTSCALE = round(SCALE) 

            if not halts:
                # Progress program by one day
                if ticks > 1000 / SIM_RATE:
                    ticks = 0
                    steps += 1

                    halts = simulator.step()  # Returns True if simulation should stop

            # handle input
            for event in pygame.event.get():
                if event.type == pygame.MOUSEWHEEL:
                    SCALE *= math.exp(event.y / 10)
                    SCALE = self.RATIO if SCALE < self.RATIO else SCALE
                    SCALE = 20. if SCALE > 20. else SCALE

                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    if key == pygame.K_UP:
                        if SIM_RATE < 60:
                            SIM_RATE *= 2
                    elif key == pygame.K_DOWN:
                        if SIM_RATE > 0.2:
                            SIM_RATE *= 1/2
                    elif key == pygame.K_RIGHT:
                        if not ticking:
                            ticks = 1000 / SIM_RATE + 1
                    elif key == pygame.K_LEFT:
                        ticking = not ticking

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    MOUSE_DRAG = True
                    MOUSE_POS = pygame.mouse.get_pos()
                elif event.type == pygame.MOUSEBUTTONUP:
                    MOUSE_DRAG = False
                elif MOUSE_DRAG and event.type == pygame.MOUSEMOTION:
                    mouse_position = pygame.mouse.get_pos()
                    diffx = mouse_position[0] - MOUSE_POS[0]
                    diffy = mouse_position[1] - MOUSE_POS[1]
                    VIEW_POS += np.array([-diffx , -diffy]) / self.RES / INTSCALE * self.RATIO
                    MOUSE_POS = mouse_position

                elif event.type == pygame.QUIT:
                    exit()

            # Draw terrain
            self.screen.fill((255,255,255))

            centx = (int(VIEW_POS[0] * grid_size) - (grid_size // 2)) % grid_size + (grid_size // 2)
            centy = (int(VIEW_POS[1] * grid_size) - (grid_size // 2)) % grid_size + (grid_size // 2)
            startx = centx - (self.RES // (INTSCALE * 2))
            starty = centy - (self.RES // (INTSCALE * 2))
            length = (self.RES // INTSCALE)

            box = terrain[startx:startx+length, starty:starty+length]
            c = self.tocolor(box, simulator.flood_height / simulator.max_height)
            peak_mask = (box == 1)
            c[peak_mask] = np.array([255, 255, 255], dtype=np.uint8)

            cc = c.repeat(INTSCALE, 0).repeat(INTSCALE, 1)
            padx = max(self.RES - cc.shape[0], 0)
            pady = max(self.RES - cc.shape[1], 0)
            cc = np.pad(cc, [(0,padx),(0,pady),(0,0)])

            pygame.surfarray.blit_array(self.screen, cc)

            # draw bots
            font = pygame.font.Font(None, 2 * INTSCALE)
            for i in range(simulator.num_bots):
                if simulator.is_alive[i]:
                    x, y = simulator.positions[i]
                    m = simulator.messages[i]

                    for shiftx in [0, grid_size]:
                        for shifty in [0, grid_size]:
                            xx = x + shiftx
                            yy = y + shifty

                            screenr = INTSCALE // 2
                            screenx = (xx - startx) * INTSCALE + screenr
                            screeny = (yy - starty) * INTSCALE + screenr

                            # bot location
                            pygame.draw.circle(self.screen, (255, 0, 255), (screenx, screeny), screenr)
                            
                            # message
                            message = format_message(m)
                            text = font.render(message, True, (255,0,255)) 
                            self.screen.blit(text, (screenx - (text.get_rect().width / 2), screeny - 2 * INTSCALE))

                            # area of view
                            xlow = (xx - startx - simulator.view_radius) * INTSCALE
                            xhigh = (xx - startx + simulator.view_radius + 1) * INTSCALE
                            ylow = (yy - starty - simulator.view_radius) * INTSCALE - 1
                            yhigh = (yy - starty + simulator.view_radius + 1) * INTSCALE - 1
                            pygame.draw.line(self.screen,(255,0,255), (xlow, ylow), (xlow, yhigh))
                            pygame.draw.line(self.screen,(255,0,255), (xlow, ylow), (xhigh, ylow))
                            pygame.draw.line(self.screen,(255,0,255), (xhigh, yhigh), (xlow, yhigh))
                            pygame.draw.line(self.screen,(255,0,255), (xhigh, yhigh), (xhigh, ylow))

            font = pygame.font.Font(None, 20)
            text = font.render("Move around with mouse drag and scroll.", True, (255,0,0))
            self.screen.blit(text, (10, 10))
            text = font.render("Pause/play with left key, single step with right key", True, (255,0,0))
            self.screen.blit(text, (10, 30))
            text = font.render("Change speed with up/down keys. ", True, (255, 0, 0))
            self.screen.blit(text, (10, 50))
            text = font.render("Current step %d" % steps, True, (205,0,0))
            self.screen.blit(text, (10, 70))
            text = font.render("Simulation rate = %.1f steps per second" % SIM_RATE, True, (205,0,0))
            self.screen.blit(text, (120, 70))
            text = font.render("Screen center coordinates (%d, %d), zoom %.1fx" % (centx % grid_size, centy % grid_size, INTSCALE / self.RATIO), True, (205,0,0))
            self.screen.blit(text, (10, 90))

            mp = pygame.mouse.get_pos()
            mousex = int(startx + mp[0] / INTSCALE) % grid_size
            mousey = int(starty + mp[1] / INTSCALE) % grid_size
            text = font.render("Mouse coordinates (%d, %d), mouse height %.1f, flood height %.1f, max height %.1f" % (mousex, mousey, simulator.terrain[mousex, mousey], simulator.flood_height, simulator.max_height), True, (205,0,0))
            self.screen.blit(text, (10, 110))

            if halts:
                if simulator.num_alive <= 0:
                    text = font.render("Program has halted, all bots died", True, (205,0,0))
                    self.screen.blit(text, (10, 130))
                else:
                    text = font.render("Program has halted, %d bots lived" % simulator.num_alive, True, (205,0,0))
                    self.screen.blit(text, (10, 130))
            elif ticking:
                text = font.render("Program running", True, (205,0,0))
                self.screen.blit(text, (10, 130))
            else:
                text = font.render("Program paused", True, (205,0,0))
                self.screen.blit(text, (10, 130))

            pygame.display.flip()
            pasttime = (time.time() - starttime) * 1000
            if pasttime > 10:
                if ticking:
                    ticks += pasttime
            else:
                pygame.time.wait(10 - int(pasttime))
                if ticking:
                    ticks += 10
