#!/usr/bin/env python
"""
The main game loop, where all components come together.
"""

import curses, random

from builder import builder, manor
from library import viewport, pathfind
from library.coord import *
from library.feature import *
from library.random_util import *
from interface import console, menu
from interface.features import *
from interface.output import *
from suspects import person, randname

screen = console.select()

# The message line.
# Following lines may get used for debugging output.
MSG_LINE  = 22
MSG_START = coord.Coord(0, MSG_LINE)

class Game (object):
    """
    The module to handle the main game loop.
    """
    def __init__ (self, type = None):
        """
        Initialise the manor, viewport and other objects and parameters.

        :``type``: The manor layout type. One of B (base), L, U, H, R (random).
                   *Default random*.
        """
        # First, build the manor.
        self.base_manor = manor.ManorCollection(builder.builder_by_type(type))

        # Add doors and windows, etc.
        self.base_manor.add_features()

        self.add_suspects()

        self.add_alibis()

        self.add_victim_body()

        # Combine the room shapes into a canvas.
        self.canvas = self.base_manor.combine()

        # Draw features on canvas.
        for pos in coord.RectangleIterator(self.canvas.size()):
            feat = self.base_manor.get_feature(pos)
            if feat != NOTHING and feat != WALL and feat != FLOOR:
                self.canvas.__setitem__(pos, feat.glyph())

        # Initialise the view port.
        self.vp = viewport.ViewPort(buffer=self.canvas,
                                    width =min(self.canvas.size().width, 70),
                                    height=min(self.canvas.size().height, 20))

        # Initialise a couple of other variables.
        self.initialise_parameters()

    def add_suspects (self):
        """
        Initialise the suspect list, generate bedrooms.
        """
        self.suspect_list = person.SuspectList(10)

        sl = self.suspect_list
        self.manor_name = sl.get_suspect(0).last
        owner_list = sl.get_id_name_tuples()
        self.base_manor.init_room_names(owner_list)

    def add_alibi_for_suspect(self, sid, rids):
        """
        Generates an alibi for a given suspect in the form of an unoccupied room.

        :``sid``: The suspect id. *Required*.
        :``rids``: Room ids of rooms that are still unoccupied. *Required*.
        """
        # The murderer always picks a room adjacent to one of the corridors,
        # so they don't have to meet any people.
        force_adj_corr = (sid == self.suspect_list.murderer)
        r = self.base_manor.pick_room_for_suspect(rids, sid, None, force_adj_corr)

        if r == None:
            return None

        self.suspect_list.get_suspect(sid).set_alibi(r, self.base_manor.room_props[r].name)
        return r

    def add_alibis (self):
        """
        Picks the murder room and assigns alibis (in the form of a room and,
        sometimes, a witness) for all suspects.
        """
        # Shortcuts for commonly used variables.
        sl = self.suspect_list
        m  = self.base_manor
        rprops = m.room_props

        # Rooms that are not used in an alibi yet. To begin with, all of them.
        rids = m.rooms[:]

        # First, pick the murder room (stored as victim's "alibi").
        r = self.add_alibi_for_suspect(sl.victim, rids)
        if r == None:
            print "Found no murder room! Exit early."
            return False

        print "Murder room: %s (%s, Victim: %s)" % (rprops[r].name, r, sl.get_victim().get_name())
        rids.remove(r)
        for adj in rprops[r].adj_rooms:
            if rprops[adj].is_corridor:
                continue
            print "block adjoining room %s (%s)" % (rprops[adj].name, adj)
            rids.remove(adj)

        r = self.add_alibi_for_suspect(sl.murderer, rids)
        if r != None:
            print "Alibi room for murderer: %s (%s, %s)" % (rprops[r].name, r, sl.get_murderer().get_name())
            sl.get_murderer().set_alibi(r, rprops[r].name)
            rids.remove(r)
        else:
            print "Found no alibi room for murderer (%s)" % sl.get_murderer().get_name()
        murderer_room = r

        # Suspects that don't have an alibi yet.
        sids = range(0, len(sl.suspects))
        sids.remove(sl.victim)
        sids.remove(sl.murderer)

        N = len(sids)
        PAIRS = max(1, random.randint((N+1)/5, (N+1)/3))
        for i in xrange(0, PAIRS):
            idx1 = random.choice(sids)
            sids.remove(idx1)
            p1 = sl.get_suspect(idx1)
            # If this person has relatives, it is highly likely one of them
            # was the witness.
            if coinflip() and len(p1.rel) > 0:
                rel  = random.choice(p1.rel)
                idx2 = rel[0]
                p2   = sl.get_suspect(idx2)
                if idx2 in sids:
                    sids.remove(idx2)
                    r = m.pick_room_for_suspect(rids, idx1, idx2)
                    if r == None:
                        return False
                    print "%s (%s) for %s and %s" % (rprops[r].name, r, sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name())
                    sl.create_paired_alibi(idx1, idx2, r, rprops[r].name)
                    rids.remove(r)
                    continue

            idx2 = random.choice(sids)
            sids.remove(idx2)
            r = m.pick_room_for_suspect(rids, idx1, idx2)
            if r != None:
                print "%s (%s) for %s and %s" % (rprops[r].name, r, sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name())
                rids.remove(r)
                sl.create_paired_alibi(idx1, idx2, r, rprops[r].name)
            else:
                print "Found no alibi room for %s and %s" % (sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name())

        # Shuffle the remaining list.
        random.shuffle(sids)

        # The remaining suspects don't have a witness.
        for s in sids:
            r = self.add_alibi_for_suspect(s, rids)
            if r != None:
                print "%s (%s) for %s" % (rprops[r].name, r, sl.get_suspect(s).get_name())
                rids.remove(r)
                sl.get_suspect(s).set_alibi(r, rprops[r].name)
            else:
                print "Found no alibi room for %s" % sl.get_suspect(s).get_name()

    def add_victim_body (self):
        sl = self.suspect_list
        murder_room = sl.get_victim().alibi.rid
        free_places = self.base_manor.get_pos_list_within_room(murder_room)

        candidates = []
        for c in free_places:
            if feature_is_floor(self.base_manor.get_feature(c)):
                candidates.append(c)

        assert(len(candidates) > 0)

        victim_name = sl.get_victim().get_name()
        feat = BODY
        feat._name = "the mangled body of %s" % victim_name
        feat._has_article = True
        body_pos = random.choice(candidates)
        self.base_manor.features.__setitem__(body_pos, feat)
        rp = self.base_manor.room_props[murder_room]

        features = self.base_manor.get_nearby_interesting_feature(body_pos)

        nearby_feat = ""
        if len(features) > 0:
            if CLOSED_DOOR in features or OPEN_DOOR in features:
                if len(rp.adj_rooms) > 1:
                    nearby_feat = "one of the doors"
                else:
                    nearby_feat = "the door"
            elif WINDOW_V in features or WINDOW_H in features:
                nearby_feat = "the window"
            else:
                nearby_feat = "the %s" % features[0].name(False)
            nearby_feat = " near %s" % nearby_feat

        rp.description += "You see here %s%s." % (feat.name(), nearby_feat)

    def initialise_parameters (self):
        """
        Initialise the simple parameters.
        """
        # Initially place the player in the centre of the entrance hall.
        ehall = self.base_manor.get_room(self.base_manor.entrance_hall)
        self.player_pos = coord.Coord(ehall.pos().x + ehall.size().x/2, ehall.pos().y + ehall.size().y/2)

        self.game_start  = True    # Game just started.
        self.debugging   = False   # debugging mode
        self.message     = None    # A message displayed for one turn.
        self.dir_running = DIR_NOWHERE # Direction we are running (if any).
        self.travel_path = []
        self.init_command_parameters()

    def init_command_parameters (self):
        """
        (Re)initialises parameters pertaining to movement and other commands
        to their default values.
        """
        self.last_move        = DIR_NOWHERE # the last step taken by the player
        self.move_was_blocked = False       # bumped into an obstacle
        self.did_move         = True        # actually took a step
        self.tried_move_feat  = NOTHING     # The feature the player tried to move on.
        self.was_running      = (self.dir_running != DIR_NOWHERE)
        self.did_switch       = False       # switched to debug mode

    def get_welcome_message (self):
        """
        Returns the message that is printed at game start.
        """
        return "Welcome to %s! To view the list of commands, press 'h'." % randname.get_random_manor_name(self.manor_name)

    def draw_feature_grid (self):
        """
        Draws the feature grid onto the screen. (Only in debug mode.)
        """
        for pos in coord.RectangleIterator(self.sect.size()):
            if pos >= self.base_manor.features.size():
                continue
            real_coord = pos + coord.Coord(self.vp._left, self.vp._top)
            char = self.base_manor.get_feature(real_coord).glyph()
            col  = self.base_manor.get_feature(real_coord).colour()
            screen.put(char, pos+1, col)

    def draw_canvas (self):
        """
        Draws the section of the viewport that's currently visible onto the screen.
        """
        for pos, char in self.sect:
            col = Colours.LIGHTGRAY
            if char == None:
                char = " "
            elif char != "#" and char != ".":
                real_coord = pos + coord.Coord(self.vp._left, self.vp._top)
                col = self.base_manor.get_feature(real_coord).colour()
            screen.put(char, pos+1, col)

    def draw_viewport (self):
        """
        Draws the game map, including the player glyph, onto the screen.
        """
        # The currently visible section of the viewport, centered on the player.
        self.vp.centre(self.player_pos, self.canvas.size())
        self.sect = self.vp.sect()

        # Depending on the current toggle state (toggle key 't'), either draw
        # the manor via the feature grid (debugging = true), or via the shape canvas.
        if self.debugging:
            self.draw_feature_grid()
        else:
            self.draw_canvas()

        # Draw the player.
        canvas_pos = coord.Coord(self.player_pos.x - self.vp._left, self.player_pos.y - self.vp._top)
        screen.put("@", canvas_pos + 1, Colours.YELLOW)

    def get_current_room_id (self, pos = None):
        """
        Returns the room id a given position belongs to.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        # Get the current room/corridor id.
        id = self.base_manor.get_room_index(pos)
        if id == None:
            id = self.base_manor.get_corridor_index(pos)
        return id

    def get_current_room (self, pos = None):
        """
        Returns the RoomProps object matching a given position.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        # Get the current room/corridor id.
        id = self.get_current_room_id(pos)
        return self.base_manor.get_roomprop(id)

    def print_message (self, text):
        """
        Prints a message in the customary message line.

        :``text``: The message to be printed.
        """
        print_line(text, MSG_START)

    def print_debugging_messages (self):
        """
        Prints a variety of parameters in the message area. (Only in debug mode.)
        """
        # Get the current room/corridor id.
        id = self.base_manor.get_corridor_index(self.player_pos)
        type = "corridor"
        if id == None:
            id   = self.base_manor.get_room_index(self.player_pos)
            type = "room"
        room_desc = self.base_manor.get_roomprop(id)

        print_line("Sect size : %s, Start coord: %s, Stop coord: %s, %s" % (self.sect.size(), coord.Coord(self.vp._left, self.vp._top), coord.Coord(self.vp._left + self.vp._width, self.vp._top + self.vp._height), room_desc), coord.Coord(0, MSG_LINE+1))

        print_line("Manor size: %s, Player coord: %s, last_move: %s, %s id: %s" % (self.canvas.size(), self.player_pos, self.last_move, type, id), coord.Coord(0, MSG_LINE+2))

    def draw_messages (self):
        """
        Writes game messages into the message area.
        """
        if self.message != None:
            self.print_message(self.message)
            self.message = None
        elif self.game_start:
            self.print_message(self.get_welcome_message())
            self.game_start = False
        elif self.move_was_blocked:
            self.print_message("Ouch! You bump into a %s!" % self.tried_move_feat.name())
        elif self.did_switch:
            mode = "canvas view"
            if self.debugging:
                mode = "debug mode"
            print_line("Switched to %s." % mode, MSG_START)
        elif self.did_move:
            oldrooms = self.base_manor.get_room_indices(self.player_pos - self.last_move)
            newrooms = self.base_manor.get_room_indices(self.player_pos)
            curr_rid = None
            for r in newrooms:
                if r not in oldrooms:
                    curr_rid = r
                    break
            if len(newrooms) == 0:
                curr_rid = self.base_manor.get_corridor_index(self.player_pos)
                old_corr = self.base_manor.get_corridor_index(self.player_pos - self.last_move)
                if len(oldrooms) == 0:
                    curr_rid = None
                else:
                    desc = "You step out into"
            else:
                desc = "You enter"

            oldcorrs = self.base_manor.get_corridor_indices(self.player_pos - self.last_move)
            newcorrs = self.base_manor.get_corridor_indices(self.player_pos)
            # print "oldrooms: %s, newrooms: %s, oldcorrs: %s, newcorrs: %s, curr_rid: %s" % (oldrooms, newrooms, oldcorrs, newcorrs, curr_rid)
            if curr_rid != None:
                self.print_message("%s %s." % (desc, self.base_manor.get_roomprop(curr_rid).room_name(True)))
            else:
                feat = self.base_manor.get_feature(self.player_pos)
                if feature_is_door(feat):
                    self.print_message("You see here a door.")
                elif not feature_is_floor(feat):
                    self.print_message("You see here %s." % feat.name())

        if self.debugging:
            # Debugging information.
            self.print_debugging_messages()
        else:
            curr = self.get_current_room()
            print_line("You are currently %s %s." % (curr.prep, curr.room_name(True)), coord.Coord(0, MSG_LINE+1))

    def update_screen (self):
        """
        Updates game map and message area.
        """
        # Note: Currently the screen gets cleared completely. Splitting that
        #       for map/message area could be useful. (jpeg)
        screen.clear(" ")
        self.draw_viewport()
        self.draw_messages()

    def cmd_describe_room (self, pos = None):
        """
        Describes the room a given position belongs to.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        room = self.get_current_room(pos)
        room.describe()

    def pos_in_room (self, pos):
        """
        A helper method to check whether travel has reached the target room.

        :``pos``: A coordinate along the path. *Required*.
        """
        curr_room = self.get_current_room_id(pos)
        return curr_room == self.travel_target_room

    def start_travel (self, room_id):
        """
        Calculate a path to another room and store it, so travel can then
        follow it.

        :``room_id``: The room id of the target room. *Required*.
        """
        if self.get_current_room_id() == room_id:
            self.message = "You are already here."
            return

        self.travel_target_room = room_id
        path = pathfind.Pathfind(self.base_manor.features, self.player_pos, None, self.pos_in_room).get_path()
        if path != None:
            self.travel_path = path
        else:
            self.message = "The requested path couldn't be found."

    def cmd_travel_menu (self):
        """
        Offers the player a choice of rooms within the manor. Picking one
        of them initialises travel.
        """
        m = menu.ScrollMenu("Travel where?", False)
        rprops  = self.base_manor.room_props
        curr_id = self.get_current_room_id()
        keyval  = ord('a')
        rlist   = self.base_manor.get_room_corridors()[:]
        rlist.sort(cmp=lambda a, b: cmp(rprops[a].name, rprops[b].name))
        for i in rlist:
            key = chr(keyval)
            name = rprops[i].name
            if i == curr_id:
                name += " (current location)"
            e = menu.Entry(key, name, self.start_travel, i)
            m.add_entry(e)

            if key == 'z':
                keyval = ord('A')
            else:
                keyval += 1
        m.do_menu()
        # self.update_screen()

    def get_command_help (self):
        """
        Returns a string of command keys and their explanation.
        """
        help  = "Command help\n\n"
        help += "Use the arrow keys for movement.\n\n"
        help += "r followed by a direction: start running in that direction\n\n"
        help += "d: describe current room\n"
        help += "h: display this screen\n"
        help += "t: travel to another room\n"
        help += "D: toggle between normal and debug mode\n\n"
        help += "Any other key exits the program."
        return help

    def handle_movement_keys (self, ch):
        """
        Checks whether a given keypress matches any of the movement keys
        and, if so, returns the matching directional coordinate.

        :``ch``: The key pressed by the player. *Required*.
        """
        if ch == curses.KEY_UP:
            return DIR_NORTH
        if ch == curses.KEY_DOWN:
            return DIR_SOUTH
        if ch == curses.KEY_LEFT:
            return DIR_WEST
        if ch == curses.KEY_RIGHT:
            return DIR_EAST

        return DIR_NOWHERE

    def cmd_start_running (self):
        """
        Prompts for a direction key and starts moving the player in that
        direction until we run into an obstacle or reach an adjacent door.
        """
        ch = screen.get(block=True)
        self.dir_running = self.handle_movement_keys(ch)
        self.was_running = True
        if self.dir_running != DIR_NOWHERE:
            self.last_move = self.dir_running
            self.did_move  = True

    def handle_movement_commands (self):
        """
        Check whether the planned move is valid. If so, actually move the
        player. Otherwise, change a few parameters.
        """
        curr_pos = self.player_pos
        next_pos = curr_pos + self.last_move
        if (next_pos.x < 0 or next_pos.y < 0
        or next_pos.x >= self.base_manor.size().x or next_pos.y >= self.base_manor.size().y):
            self.move_was_blocked = True
        else:
            self.tried_move_feat = self.base_manor.get_feature(next_pos)
            if not self.debugging and not self.tried_move_feat.traversable():
                self.move_was_blocked = True
            else:
                curr_pos += self.last_move
                if self.dir_running != DIR_NOWHERE:
                    # check whether we need to stop
                    if (feature_is_door(self.base_manor.get_feature(curr_pos))
                    or self.debugging and not self.tried_move_feat.traversable()):
                        self.dir_running = DIR_NOWHERE
                    else:
                        in_corr = (self.base_manor.get_corridor_index(curr_pos) != None)
                        dirs = (DIR_NORTH, DIR_SOUTH, DIR_WEST, DIR_EAST)
                        for d in dirs:
                            if d == self.dir_running or DIR_NOWHERE - d == self.dir_running:
                                continue
                            if (in_corr and self.base_manor.get_feature(curr_pos + d) == FLOOR
                            or feature_is_door(self.base_manor.get_feature(curr_pos + d))):
                                self.dir_running = DIR_NOWHERE
                                break

        if self.move_was_blocked:
            # Reset last_move.
            self.last_move = DIR_NOWHERE
            self.did_move  = False
            if self.was_running or len(self.travel_path) > 0:
                # No running into wall messages.
                self.move_was_blocked = False
                self.dir_running      = DIR_NOWHERE
                self.travel_path      = []
        else:
            self.did_move = True

    def handle_commands (self):
        """
        Wait for a keypress and execute the corresponding action.
        Returns true if the game loop should continue, and false if we
        want to exit the loop.
        """
        curr_pos = self.player_pos
        if len(self.travel_path) > 0:
            # self.player_pos = self.travel_path.pop()
            next_pos = self.travel_path.pop()
            self.last_move = next_pos - curr_pos
        elif self.dir_running == DIR_NOWHERE:
            # Get a key.
            ch = screen.get(block=True)

            if ch > 0 and ch <= 256:
                self.did_move = False
                if chr(ch) == 'd':
                    self.cmd_describe_room()
                elif chr(ch) == 'h':
                    # Print command help.
                    print_screen(self.get_command_help())
                elif chr(ch) == 'r':
                    self.cmd_start_running()
                elif chr(ch) == 't':
                    self.cmd_travel_menu()
                elif chr(ch) == 'D':
                    # Toggle debugging mode on and off.
                    self.debugging  = not self.debugging
                    self.did_switch = True
                else: # exit the game
                    return False
            else:
                # Move the player (@) via the arrow keys.
                # If we haven't reached the manor boundaries yet, scroll in that direction.
                # Otherwise, take a step unless it would make us leave the manor.
                self.last_move = self.handle_movement_keys(ch)
        else:
            self.last_move = self.dir_running

        # Actually move the player, if the new position is valid.
        if self.last_move != DIR_NOWHERE:
            self.handle_movement_commands()

        return True

    def do_loop (self):
        """
        Run the actual game loop. Returns if we encounter an invalid keypress.
        """
        while True:
            if self.dir_running == DIR_NOWHERE and len(self.travel_path) == 0:
                self.update_screen()

            # Reinitialise the relevant variables.
            self.init_command_parameters()

            if not self.handle_commands():
                return
