# ======================================================================
# FILE:        MyAI.py
#
# AUTHOR:      Abdullah Younis
#
# DESCRIPTION: This file contains your agent class, which you will
#              implement. You are responsible for implementing the
#              'getAction' function and any helper methods you feel you
#              need.
#
# NOTES:       - If you are having trouble understanding how the shell
#                works, look at the other parts of the code, as well as
#                the documentation.
#
#              - You are only allowed to make changes to this portion of
#                the code. Any changes to other portions of the code will
#                be lost when the tournament runs your code.
# ======================================================================

from Agent import Agent

class MyAI ( Agent ):

    def __init__ ( self ):
        self.got_gold = False
        self.facing = "Right"
        self.last_action = False
        self.current_location = [1,1]
        self.x_boundary = 7
        self.y_boundary = 7
        self.go_back_home = False 
        self.is_wumpus_alive = True
        self.is_wumpus_located = False
        self.shot_arrow = False
        self.next_locations = []
        self.dangerous_locations = []
        self.visited_locations = []
        self.current_trail = []
        self.go_back_one = False
        self.started = False

    # ======================================================================
    # YOUR CODE BEGINS
    # ======================================================================   
    def getAction( self, stench, breeze, glitter, bump, scream ):
        ''' This is the main function that analyzes all of the percepts (stench, breeze, glitter, bump, scream)
            and decides what the agent's next action will be. '''
        #Go back if the gold was found or if there isn't any available moves left
        if self.go_back_home:
            return self.goingBackHome()
        #If the current location has the gold grab it
        elif glitter:
            self.go_back_home = True
            return Agent.Action.GRAB
        #Actions made differ if its the first move on the first cell [1,1]
        elif self.started == False and self.current_location == [1,1]:
            return self.startingDecisions(stench, breeze, scream)
        else:
            self.visited_locations.append(self.current_location)
            if bump:
                return self.ranIntoBump()
            elif stench and self.is_wumpus_located == False:
                return self.ranIntoDanger()
            elif breeze:
                return self.ranIntoDanger()
            #No dangerous percepts on current cell
            else:
                #If previous surrounding cells were marked as dangerous unmark them
                #Thats Becuase if the current cell has no percept that means the surrounding cells arent actually dangerous
                self.removeDangerousLocations()
                #Dont generate locations if last action was LEFT Turn or Right Turn because the agent is in the same cell
                if self.last_action == Agent.Action.FORWARD:
                    self.generateNextLocations()
                #If there are no new generated locations or remaining locations to visited, go back home
                if len(self.next_locations) == 0:
                    self.go_back_home = True
                    return self.goingBackHome()
                #If none of the next_locations are within 1 cell of distance than go back 1 previous cell
                elif self.areNextLocationsNearby() == False:
                    return self.goingBackOne()
                #Everything was normal so choose the next location and return an action
                else: 
                    next_location = self.chooseNextLocation()
                    # self.printInfo() 
                    action = self.takeAction(next_location[0],next_location[1])
                    self.last_action = action
                    return action
            
    def startingDecisions(self, stench, breeze, scream) -> Agent.Action:
        ''' The decisions the agent makes in the first cell are different than the ones it makes
            in other cells. If the first cell has a Breeze percept that means that their is a 50%
            the next cell, up or right, is a Pit which will result in loss, so its better to just CLIMB.
            If the percept is a Stench then there is a 50% chance the agent will kill the Wumpus if it shoots
            the arrow straight. If there is no Scream then we know for sure the Wumpus is in cell [2,1]. 
            If there are no percepts than just move forward and begin the search for gold. '''
        if breeze:
            return Agent.Action.CLIMB
        elif stench:
            if self.shot_arrow == False:
                self.shot_arrow = True
                return Agent.Action.SHOOT
            else:
                if scream:
                    self.is_wumpus_located = True
                    self.is_wumpus_alive = False
                else: 
                    self.is_wumpus_located = True
                    self.dangerous_locations.append([1,2])
        self.started = True
        self.visited_locations.append(self.current_location)
        self.current_trail.append(self.current_location)
        self.generateNextLocations()
        # self.printInfo()
        self.current_location = [2,1]
        self.next_locations.remove(self.current_location)
        self.last_action = Agent.Action.FORWARD
        return Agent.Action.FORWARD

    def ranIntoBump(self) -> Agent.Action:
        ''' When the agent is traveling it doesnt know how big the "cave" is, so if it tries
            to go forward and the percept results in a Bump that means it has reached a wall.
            The adjent will want to readjust its current location, set a new out of bounds variable,
            remove any generated out of bounds locations, and finally decide on a new location. ''' 
        self.current_location = self.current_trail[-1]
        self.current_trail.pop()
        self.removeOutOfBoundsLocations()
        if len(self.next_locations) == 0:
            self.go_back_home = True
            return self.goingBackHome()
        next_location = self.chooseNextLocation()
        # self.printInfo() 
        action = self.takeAction(next_location[0],next_location[1])
        self.last_action = action
        return action

    def removeOutOfBoundsLocations(self):
        ''' This function is called upon when the agent runs into a Bump and new out of bounds
            parameters have been set. Any previously generated locations with the old out bounds
            have to be removed from next_locations so that the agent does not visit them. '''
        if self.facing == "Right":
            self.x_boundary = self.current_location[0]
            for location in self.next_locations:
                if location[0] > self.x_boundary:
                    self.next_locations.remove(location)
        if self.facing == "Up":
            self.y_boundary = self.current_location[1]
            for location in self.next_locations:
                if location[1] > self.y_boundary:
                    self.next_locations.remove(location)

    def ranIntoDanger(self):
        ''' This function is envoked when the agent runs into Stench or a Breeze.
            It will call another function to mark the surrounding locations as dangerous
            and will then go back to the most previously visited location. '''
        if self.go_back_one == False:
            self.markDangerousLocations()
        return self.goingBackOne()

    def markDangerousLocations(self):
        ''' This function marks any surrounding locations as dangerous so that the agent will
            avoid them when generating new locations to visit. Before marking any locations as 
            dangerous, first we check that the location is within bounds to avoid adding any
            unecessary locations. Then we check that the location isnt already a visited location
            because then that would indicate that it isnt dangerous and its actually safe. Finally
            we remove any of the dangerous locations from next locations so the agent wont visit them. '''
        dangerous_locations = []
        #Left
        if self.isWithinBounds(self.current_location[0]-1,self.current_location[1]):
            if([self.current_location[0]-1,self.current_location[1]] not in self.visited_locations):
                dangerous_locations.append([self.current_location[0]-1,self.current_location[1]])
        #Up
        if self.isWithinBounds(self.current_location[0],self.current_location[1]+1):
            if([self.current_location[0],self.current_location[1]+1] not in self.visited_locations):
                dangerous_locations.append([self.current_location[0],self.current_location[1]+1])
        #Right
        if self.isWithinBounds(self.current_location[0]+1,self.current_location[1]):
            if([self.current_location[0]+1,self.current_location[1]] not in self.visited_locations):
                dangerous_locations.append([self.current_location[0]+1,self.current_location[1]])
        #Down
        if self.isWithinBounds(self.current_location[0],self.current_location[1]-1):
            if([self.current_location[0],self.current_location[1]-1] not in self.visited_locations):
                dangerous_locations.append([self.current_location[0],self.current_location[1]-1])

        for location in dangerous_locations:
            if location in self.next_locations:
                self.next_locations.remove(location)
            self.dangerous_locations.append(location)

    def removeDangerousLocations(self):
        ''' When the agent moves into a new cell and it contains a percept, that means that one
            of the surrounding cells is POSSIBLY dangerous, either containing the wumpus or a pit, 
            but the agent is unsure. When the agent moves into a different cell that doesnt contain 
            a percept and is adjacent to a previously marked dangerous location, this confirms that
            the possibly marked dangerous location isnt actually dangerous or else the current location
            would have a percept. As a result the current surrounding cells should be unmarked.'''
        up_location = [self.current_location[0],self.current_location[1]+1]
        left_location = [self.current_location[0]-1,self.current_location[1]]
        right_location = [self.current_location[0]+1,self.current_location[1]]
        if up_location in self.dangerous_locations:
            self.dangerous_locations.remove(up_location)
        if left_location in self.dangerous_locations:
            self.dangerous_locations.remove(left_location)
        if right_location in self.dangerous_locations:
            self.dangerous_locations.remove(right_location)

    def generateNextLocations(self):
        ''' When the agent moves to a new location we can generate new locations for the agent
            to move to based off of the current location. Any surrounding location in the directions
            of up,down,left,right are added to the next locations as long as they are within bounds,
            are not dangerous, have not been visited and are not already in next locations. '''
        #Up
        if self.isWithinBounds(self.current_location[0],self.current_location[1]+1):
            if [self.current_location[0],self.current_location[1]+1] not in self.dangerous_locations:
                if [self.current_location[0],self.current_location[1]+1] not in self.visited_locations:
                    if [self.current_location[0],self.current_location[1]+1] not in self.next_locations:
                        self.next_locations.append([self.current_location[0],self.current_location[1]+1])
        #Right
        if self.isWithinBounds(self.current_location[0]+1,self.current_location[1]):
            if [self.current_location[0]+1,self.current_location[1]] not in self.dangerous_locations:
                if [self.current_location[0]+1,self.current_location[1]] not in self.visited_locations:
                    if [self.current_location[0]+1,self.current_location[1]] not in self.next_locations:
                        self.next_locations.append([self.current_location[0]+1,self.current_location[1]])
        #Down
        if self.isWithinBounds(self.current_location[0],self.current_location[1]-1):
            if [self.current_location[0],self.current_location[1]-1] not in self.dangerous_locations:
                if [self.current_location[0],self.current_location[1]-1] not in self.visited_locations:
                    if [self.current_location[0],self.current_location[1]-1] not in self.next_locations:
                        self.next_locations.append([self.current_location[0],self.current_location[1]-1])
        #Left
        if self.isWithinBounds(self.current_location[0]-1,self.current_location[1]):
            if [self.current_location[0]-1,self.current_location[1]] not in self.dangerous_locations:
                if [self.current_location[0]-1,self.current_location[1]] not in self.visited_locations:
                    if [self.current_location[0]-1,self.current_location[1]] not in self.next_locations:
                        self.next_locations.append([self.current_location[0]-1,self.current_location[1]])

    def areNextLocationsNearby(self) -> bool:
        ''' The agent has locations that it should visit next, however if none of the next locations
            are nearby the agent will have to goBackOne until it reaches a location that can be within
            one cell of a next location. '''
        nearby_locations = []
        #Left
        if self.isWithinBounds(self.current_location[0]-1,self.current_location[1]):
            nearby_locations.append([self.current_location[0]-1,self.current_location[1]])
        #Up
        if self.isWithinBounds(self.current_location[0],self.current_location[1]+1):
            nearby_locations.append([self.current_location[0],self.current_location[1]+1])
        #Right
        if self.isWithinBounds(self.current_location[0]+1,self.current_location[1]):
            nearby_locations.append([self.current_location[0]+1,self.current_location[1]])
        #Down
        if self.isWithinBounds(self.current_location[0],self.current_location[1]-1):
            nearby_locations.append([self.current_location[0],self.current_location[1]-1])
        for location in nearby_locations:
            if location in self.next_locations:
                return True
        return False

    def chooseNextLocation(self) -> [int,int]:
        ''' The agent has to choose the next location to travel to from the array of next_locations.
            The next location is chosen by calculating which location cost the least to travel to. '''
        least_cost_location = {"location": self.next_locations[0],"cost": abs(self.current_location[0]-self.next_locations[0][0]) + abs(self.current_location[1]-self.next_locations[0][1])}
        least_cost_location["cost"] += self.calculateFacingCost(self.next_locations[0][0],self.next_locations[0][1])
        #Loop thorugh the array in reverse order so that the most recently added locations have priority
        for location in reversed(self.next_locations):
            cost =  abs(self.current_location[0]-location[0]) + abs(self.current_location[1]-location[1])
            cost += self.calculateFacingCost(location[0],location[1])
            if cost < least_cost_location["cost"]:
                least_cost_location["location"] = location
                least_cost_location["cost"] = cost 
        return least_cost_location["location"]
    
    def calculateFacingCost(self,x,y) -> int:
        ''' The cost of a next location is calculated by counting the amount of actions needed to 
            reach the next location relative to the current location and the current facing of the agent.
            e.g. The current facing is Left and the next location on the Right, the agent will have to
            turn Right to face Up, then right to face Right If the agent is facing left and the next location is on the right side of the current location.
            The agent will have to make 3 actions: turn Right to face Up, turn Right to face Right and then 
            move Forward to reach the next location. '''
        if self.facing == "Left":
            if x < self.current_location[0]:
                #Left Up
                if y > self.current_location[1]:
                    return 3
                #Left
                elif y == self.current_location[1]:
                    return 1
                #Left Down
                elif y < self.current_location[1]:
                    return 3
            elif x > self.current_location[0]:
                #Right Up
                if y > self.current_location[1]:
                    return 4
                #Right
                elif y == self.current_location[1]:
                    return 3
                #Right Down
                elif y < self.current_location[1]:
                    return 4
            else:
                #Up
                if y > self.current_location[1]:
                    return 2
                #Down
                elif y < self.current_location[1]:
                    return 2
        if self.facing == "Up":
            if x < self.current_location[0]:
                #Left Up
                if y > self.current_location[1]:
                    return 3
                #Left
                elif y == self.current_location[1]:
                    return 2
                #Left Down
                elif y < self.current_location[1]:
                    return 4
            elif x > self.current_location[0]:
                #Right Up
                if y > self.current_location[1]:
                    return 3
                #Right
                elif y == self.current_location[1]:
                    return 2
                #Right Down
                elif y < self.current_location[1]:
                    return 4
            else:
                #Up
                if y > self.current_location[1]:
                    return 1
                #Down
                elif y < self.current_location[1]:
                    return 3
        if self.facing == "Right":
            if x < self.current_location[0]:
                #Left Up
                if y > self.current_location[1]:
                    return 4
                #Left
                elif y == self.current_location[1]:
                    return 3
                #Left Down
                elif y < self.current_location[1]:
                    return 4
            elif x > self.current_location[0]:
                #Right Up
                if y > self.current_location[1]:
                    return 3
                #Right
                elif y == self.current_location[1]:
                    return 1
                #Right Down
                elif y < self.current_location[1]:
                    return 3
            else:
                #Up
                if y > self.current_location[1]:
                    return 2
                #Down
                elif y < self.current_location[1]:
                    return 2
        if self.facing == "Down":
            if x < self.current_location[0]:
                #Left Up
                if y > self.current_location[1]:
                    return 4
                #Left
                elif y == self.current_location[1]:
                    return 2
                #Left Down
                elif y < self.current_location[1]:
                    return 3
            elif x > self.current_location[0]:
                #Right Up
                if y > self.current_location[1]:
                    return 4
                #Right
                elif y == self.current_location[1]:
                    return 2
                #Right Down
                elif y < self.current_location[1]:
                    return 3
            else:
                #Up
                if y > self.current_location[1]:
                    return 3
                #Down
                elif y < self.current_location[1]:
                    return 1
 
    def takeAction(self,x,y) -> Agent.Action:
        ''' Once the agent has decided the next location it wants to visit, it has to decide what
            actions it will make in order to reach that location. Depending on the direction of the
            next location relative to the current location the agent might have to make a few turns
            before moving Forward to reach the next location.
            e.g. If the current facing is Left and the next location is on the Right, the agent will 
            have to Turn_Right to face Up, then Turn_Right to face Right, and finally move Forward 
            to reach the location. ''' 
        if self.facing == "Left":
            if x < self.current_location[0]:
                #Left
                if y == self.current_location[1]:
                    return self.takeActionHelper(x,y)
            elif x > self.current_location[0]:
                #Right
                if y == self.current_location[1]:
                    self.facing = "Up"
                    return Agent.Action.TURN_RIGHT
            else:
                #Up
                if y > self.current_location[1]:
                    self.facing = "Up"
                    return Agent.Action.TURN_RIGHT
                #Down
                elif y < self.current_location[1]:
                    self.facing = "Down"
                    return Agent.Action.TURN_LEFT
        if self.facing == "Up":
            if x < self.current_location[0]:
                #Left
                if y == self.current_location[1]:
                    self.facing = "Left"
                    return Agent.Action.TURN_LEFT
            elif x > self.current_location[0]:
                #Right
                if y == self.current_location[1]:
                    self.facing = "Right"
                    return Agent.Action.TURN_RIGHT
            else:
                #Up
                if y > self.current_location[1]:
                    return self.takeActionHelper(x,y)
                #Down
                elif y < self.current_location[1]:
                    self.facing = "Right"
                    return Agent.Action.TURN_RIGHT

        if self.facing == "Right":
            if x < self.current_location[0]:
                #Left
                if y == self.current_location[1]:
                    self.facing = "Down"
                    return Agent.Action.TURN_RIGHT
            elif x > self.current_location[0]:
                #Right
                if y == self.current_location[1]:
                    return self.takeActionHelper(x,y)
            else:
                #Up
                if y > self.current_location[1]:
                    self.facing = "Up"
                    return Agent.Action.TURN_LEFT
                #Down
                elif y < self.current_location[1]:
                    self.facing = "Down"
                    return Agent.Action.TURN_RIGHT
        if self.facing == "Down":
            if x < self.current_location[0]:
                #Left
                if y == self.current_location[1]:
                    self.facing = "Left"
                    return Agent.Action.TURN_RIGHT
            elif x > self.current_location[0]:
                #Right
                if y == self.current_location[1]:
                    self.facing = "Right"
                    return Agent.Action.TURN_LEFT
            else:
                #Up
                if y > self.current_location[1]:
                    self.facing = "Left"
                    return Agent.Action.TURN_RIGHT
                #Down
                elif y < self.current_location[1]: 
                    return self.takeActionHelper(x,y)

    def takeActionHelper(self,x,y):
        ''' This is a helper function for when the agent wants to move Forward. Normally if the
            agent wants to move Forward it will have to add its previous location to the trail 
            and remove its new location from the next_locations. However, when the agent is moving
            Forward due to having to go back one, we want to avoid including these steps. ''' 
        if self.go_back_one:
            self.current_location = [x,y]
            return Agent.Action.FORWARD
        self.current_trail.append(self.current_location)
        self.current_location = [x,y]
        self.next_locations.remove(self.current_location)
        return Agent.Action.FORWARD

    def isWithinBounds(self, x:int, y:int) -> bool:
        ''' This function takes in the x and y axis of a new location and checks to see if 
            it is within the boundaries of the map. If either one of the axis is not within the 
            boundaries that means that the location is not one which the agent should visit. '''
        if 0 < x and x <= self.x_boundary:
            if 0 < y and y <= self.y_boundary:
                return True 
            else:
                return False 
        return False

    def goingBackOne(self) -> Agent.Action:
        ''' The agent needs to go back one previous location when it encounters a Stench, a Breeze,
            a Bump, or when there are no next locations nearby. The agent will turn on going_back_one
            when its the first time goingBackOne is being invoked. goingBackOne will keep being called 
            until the agent turns into a direction in which it can go Forward, then it will turn off going_back_one. '''
        if self.go_back_one == False:
            self.go_back_one = True 
        # self.printInfo() 
        next_location = self.current_trail[-1]
        action = self.takeAction(next_location[0],next_location[1])
        if action == Agent.Action.FORWARD:
            self.go_back_one = False
            self.current_trail.pop()
        return action

    def goingBackHome(self) -> Agent.Action:
        ''' This function will always run once go_back_home has been activated; that is because
            the agent has either found the gold or has run out of available locations to visit.
            This function avoids generating new locations and focuses on back tracking to previously
            visited locations which will lead to the home location [1,1] ''' 
        if self.current_location == [1,1]:
            return  Agent.Action.CLIMB
        next_location = self.returnSmartLocation()
        self.removeUnsmartLocations(next_location[1])
        return self.goingBackOne()

    def returnSmartLocation(self) -> [[int],int]: 
        ''' When back tracking the agent looks at the trail that it has been on from the starting
            home location up until the current location. To back track the agent will move to the last 
            location that it has visited. However, to avoid moving in a circle when trying to move to a location
            that is just one cell down, the agent can check if that location is within the trail and just
            automatically move to that cell and remove the other cells.
            e.g. The current facing is Left and the next location on the Right, the agent will have to
            turn Right to face Up, then right to face Right the trail: [[1,1],[1,2],[2,2]] current location: [2,1] destination: [1,1]
            Instead of going through all the cells, the agent can just move to [1,1] because its within reach. '''
        #Only need to check left and down locations because the home location is in the bottom left corner of the map
        left_location = [self.current_location[0]-1,self.current_location[1]]
        down_location = [self.current_location[0],self.current_location[1]-1]
        for location in self.current_trail:
            #Return the location and its index in current_trail to remove the other cells after the index 
            if location == left_location:
                return [location,self.current_trail.index(location)]
            elif location == down_location:
                return [location,self.current_trail.index(location)]
        #If a left or down location was not within reach, move to previous location visited
        return [self.current_trail[-1],0]

    def removeUnsmartLocations(self,location_index):
        ''' When the agent is back tracking it looks at the current trail it has been on, from the starting home
            location up until the last location visited. To avoid moving in a circle when the agent can just 
            shortcut into a left or down location, we can move directly to that location and remove the rest of
            the locations from the trail. '''
        if location_index != 0:
            size = len(self.current_trail) - (location_index+1) 
            for i in range(size):
                self.current_trail.pop()

    def printInfo(self):
        ''' Useful information for the user to see when the agent is traveling. '''
        print("Current Location: ", self.current_location)
        print("Facing: ", self.facing)
        print("Next Locations: ",self.next_locations)
        print("Current Trail: ", self.current_trail)
        print("#"*40)
    # ======================================================================
    # YOUR CODE ENDS
    # ======================================================================

