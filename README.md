# Turtlesim Safety Controller – Final Report (README)

## 1. Objective of the Assignment
The goal of this assignment was to design and implement a *safety controller for two turtles running in the *turtlesim* environment using ROS2.  
The system had to ensure that:

1. The turtles never collide with each other.  
2. The turtles never cross the map boundaries.  
3. The user is still able to manually control both turtles through a dedicated UI node.  
4. The system must override unsafe user commands whenever a dangerous situation occurs.

This required real-time monitoring, automatic intervention, and smooth integration between user input and safety logic.

---

# 2. Implemented Features

## 2.1 Border Protection
Each turtle’s pose is monitored continuously.  
When a turtle approaches the boundary or slightly crosses it, the controller:

1. Stops the turtle immediately 
2. Computes the overshoot, i.e., how far outside the safe zone the turtle went  
3. Decides whether a rotation is needed, based on the last user command  
   - If the turtle was moving forward → rotate the turtle exactly 180°  
   - If the turtle was moving backward → no rotation
4. Moves the turtle forward by a distance proportional to the overshoot  
   (ensuring it safely re-enters the map)  
5. Stops the turtle again and resumes normal operation

A cooldown mechanism prevents repeated corrections from happening too rapidly.

---

## 2.2 Collision Avoidance
The system constantly computes the distance between the two turtles.

If the turtles come too close (distance < 1.0):

1. Both turtles are immediately stopped  
2. The system performs a short *separation maneuver, pushing them apart  
3. User commands are temporarily blocked until the situation becomes safe again  

This prevents overlap and undesired interactions between turtles.

---

## 2.3 Safe Command Filtering
To remain compatible with the UI:

- The UI publishes velocity commands for exactly 1 second  
- The safety node intercepts all `/cmd_vel` commands  
- Unsafe commands (border violations / collisions) are replaced with safe behaviors  
- The last commanded `linear.x` value is tracked to understand movement direction

This ensures a clean interaction between manual control and automated safety constraints.

# 3. How to Run the System (Using 4 Terminals)

### Terminal 1 – Start the turtlesim environment
```
ros2 run turtlesim turtlesim_node
```

### Terminal 2 – Spawn the second turtle
```
ros2 run assignment1_rt turtle_spawn
```

### Terminal 3 – Start the Safety Controller
```
ros2 run assignment1_rt distance
```

### Terminal 4 – Start the User Interface
```
ros2 run assignment1_rt ui
```

Follow the prompts in the UI to select the turtle and specify linear and angular velocities.

---

# 4. Summary
This project successfully integrates:

- Real-time pose monitoring  
- Automated safety interventions  
- Controlled user interaction  
- Intelligent boundary and collision handling  

The system ensures that both turtles behave safely under all conditions while maintaining full user control when no danger is present.

