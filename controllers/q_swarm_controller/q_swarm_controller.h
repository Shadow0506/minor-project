#ifndef Q_SWARM_CONTROLLER_H
#define Q_SWARM_CONTROLLER_H

/*
 * Q-Learning Swarm Controller Header
 * 
 * This controller manages a single FootBot in the swarm.
 * It collects sensor data, communicates with the Python Q-Network,
 * and executes the selected action.
 */

#include <argos3/core/control_interface/ci_controller.h>
#include <argos3/plugins/robots/generic/control_interface/ci_differential_steering_actuator.h>
#include <argos3/plugins/robots/generic/control_interface/ci_positioning_sensor.h>
#include <argos3/plugins/robots/foot-bot/control_interface/ci_footbot_proximity_sensor.h>
#include <argos3/core/utility/math/vector2.h>
#include <argos3/core/utility/logging/argos_log.h>

#include <string>
#include <vector>
#include <memory>

// For socket communication
#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <netinet/in.h>
#endif

namespace argos {

   class QSwarmController : public CCI_Controller {

   public:

      /* Constructor */
      QSwarmController();

      /* Destructor */
      virtual ~QSwarmController();

      /*
       * This function initializes the controller.
       * Called once at the start of the simulation.
       */
      virtual void Init(TConfigurationNode& t_node);

      /*
       * This function is called once every time step.
       * This is the main control loop.
       */
      virtual void ControlStep();

      /*
       * This function resets the controller to its initial state.
       * Called when the experiment is reset.
       */
      virtual void Reset();

      /*
       * Called when the controller is removed from the simulation.
       */
      virtual void Destroy();

   private:

      /* Pointer to the differential steering actuator */
      CCI_DifferentialSteeringActuator* m_pcWheels;

      /* Pointer to the proximity sensor */
      CCI_FootBotProximitySensor* m_pcProximity;

      /* Pointer to the positioning sensor */
      CCI_PositioningSensor* m_pcPositioning;

      /* Robot ID (extracted from robot name) */
      std::string m_strRobotId;
      int m_nRobotIdNum;

      /* Goal position (target to reach) */
      CVector2 m_cGoalPosition;

      /* Current episode number */
      int m_nEpisode;

      /* Steps in current episode */
      int m_nSteps;

      /* Maximum steps per episode */
      int m_nMaxSteps;

      /* Maximum number of episodes */
      int m_nMaxEpisodes;

      /* Socket for communication with Python Q-Network */
      int m_nSocket;
      bool m_bConnected;

      /* Previous position (for collision detection) */
      CVector2 m_cPreviousPosition;

      /* Velocity setting */
      float m_fVelocity;

      /* Collision threshold (if distance moved < this, possible collision) */
      float m_fCollisionThreshold;

      /* Goal reached threshold */
      float m_fGoalThreshold;

      /* Episode done flag */
      bool m_bEpisodeDone;

      /* Accumulated reward for current episode */
      float m_fEpisodeReward;

      /*
       * Connect to the Python Q-Network server
       * Returns true if successful
       */
      bool ConnectToQNetwork();

      /*
       * Send state to Q-Network and receive action
       * State includes: robot position, goal position, proximity readings
       * Returns action ID (0=forward, 1=left, 2=right, 3=stop)
       */
      int GetActionFromQNetwork(const std::vector<float>& state);

      /*
       * Send reward feedback to Q-Network
       */
      void SendReward(float reward, bool done);

      /*
       * Collect current state from sensors
       * Returns: [x, y, goal_x, goal_y, prox_0, ..., prox_23]
       */
      std::vector<float> GetState();

      /*
       * Execute the selected action
       * 0 = move forward
       * 1 = turn left
       * 2 = turn right
       * 3 = stop
       */
      void ExecuteAction(int action);

      /*
       * Calculate reward based on current state
       * +10 for reaching goal
       * -5 for collision
       * -0.1 per step (encourages efficiency)
       */
      float CalculateReward(bool& done);

      /*
       * Check if robot reached the goal
       */
      bool ReachedGoal();

      /*
       * Check if robot collided (stuck or didn't move)
       */
      bool DetectCollision();

      /*
       * Reset episode (move robot to starting position)
       */
      void ResetEpisode();

      /*
       * Send message through socket
       */
      bool SendMessage(const std::string& message);

      /*
       * Receive message from socket
       */
      std::string ReceiveMessage();

      /*
       * Close socket connection
       */
      void CloseConnection();

   };

}

#endif
