/*
 * Q-Learning Swarm Controller Implementation
 * 
 * This controller implements the robot-side logic for Deep Q-Learning.
 * Each FootBot collects sensor data, communicates with the Python Q-Network
 * via socket, executes actions, and sends reward feedback.
 */

#include "q_swarm_controller.h"
#include <argos3/core/utility/configuration/argos_configuration.h>
#include <argos3/core/utility/logging/argos_log.h>
#include <sstream>
#include <cmath>
#include <algorithm>

namespace argos {

   /****************************************/
   /****************************************/

   QSwarmController::QSwarmController() :
      m_pcWheels(NULL),
      m_pcProximity(NULL),
      m_pcPositioning(NULL),
      m_nEpisode(0),
      m_nSteps(0),
      m_nMaxSteps(500),
      m_nMaxEpisodes(1000),
      m_nSocket(-1),
      m_bConnected(false),
      m_fVelocity(0.1f),
      m_fCollisionThreshold(0.001f),  // 1mm - much lower to avoid false positives
      m_fGoalThreshold(0.5f),
      m_bEpisodeDone(false),
      m_fEpisodeReward(0.0f),
      m_nRobotIdNum(0) {
   }

   /****************************************/
   /****************************************/

   QSwarmController::~QSwarmController() {
      CloseConnection();
   }

   /****************************************/
   /****************************************/

   void QSwarmController::Init(TConfigurationNode& t_node) {
      // Get actuators and sensors
      m_pcWheels = GetActuator<CCI_DifferentialSteeringActuator>("differential_steering");
      m_pcProximity = GetSensor<CCI_FootBotProximitySensor>("footbot_proximity");
      m_pcPositioning = GetSensor<CCI_PositioningSensor>("positioning");

      // Get robot ID from robot name (e.g., "fb0" -> 0)
      m_strRobotId = GetId();
      size_t pos = m_strRobotId.find_last_of("0123456789");
      if (pos != std::string::npos) {
         m_nRobotIdNum = std::stoi(m_strRobotId.substr(pos));
      }

      // Read goal position from configuration (default to 18, 18)
      Real fGoalX = 18.0f;
      Real fGoalY = 18.0f;
      GetNodeAttributeOrDefault(t_node, "goal_x", fGoalX, fGoalX);
      GetNodeAttributeOrDefault(t_node, "goal_y", fGoalY, fGoalY);
      m_cGoalPosition.SetX(fGoalX);
      m_cGoalPosition.SetY(fGoalY);

      // Read other parameters
      GetNodeAttributeOrDefault(t_node, "velocity", m_fVelocity, m_fVelocity);
      GetNodeAttributeOrDefault(t_node, "max_steps", m_nMaxSteps, m_nMaxSteps);
      GetNodeAttributeOrDefault(t_node, "max_episodes", m_nMaxEpisodes, m_nMaxEpisodes);

      LOG << "[Robot " << m_strRobotId << "] Initialized. Goal: (" 
          << m_cGoalPosition.GetX() << ", " << m_cGoalPosition.GetY() << ")" << std::endl;
      LOG << "[Robot " << m_strRobotId << "] Velocity: " << m_fVelocity 
          << " cm/s, Max steps: " << m_nMaxSteps << std::endl;

      // Initialize previous position
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      m_cPreviousPosition.Set(sReading.Position.GetX(), sReading.Position.GetY());

      // Connect to Q-Network server
      ConnectToQNetwork();
   }

   /****************************************/
   /****************************************/

   void QSwarmController::ControlStep() {
      // If we've completed all episodes, stop
      if (m_nEpisode >= m_nMaxEpisodes) {
         m_pcWheels->SetLinearVelocity(0.0f, 0.0f);
         return;
      }

      // If episode is done, reset
      if (m_bEpisodeDone) {
         ResetEpisode();
         return;
      }

      // Increment step counter
      m_nSteps++;

      // Get current state from sensors
      std::vector<float> state = GetState();

      // Get action from Q-Network
      int action = GetActionFromQNetwork(state);

      // Execute the action
      ExecuteAction(action);

      // Calculate reward and check if done
      bool done = false;
      float reward = CalculateReward(done);
      m_fEpisodeReward += reward;

      // Send reward to Q-Network for learning
      SendReward(reward, done);

      // Check if episode should end
      if (done || m_nSteps >= m_nMaxSteps) {
         m_bEpisodeDone = true;
         LOG << "[Robot " << m_strRobotId << "] Episode " << m_nEpisode 
             << " ended. Steps: " << m_nSteps 
             << ", Reward: " << m_fEpisodeReward << std::endl;
      }
   }

   /****************************************/
   /****************************************/

   void QSwarmController::Reset() {
      // Reset all state variables
      m_nEpisode = 0;
      m_nSteps = 0;
      m_bEpisodeDone = false;
      m_fEpisodeReward = 0.0f;

      // Stop the robot
      m_pcWheels->SetLinearVelocity(0.0f, 0.0f);

      // Update previous position
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      m_cPreviousPosition.Set(sReading.Position.GetX(), sReading.Position.GetY());
   }

   /****************************************/
   /****************************************/

   void QSwarmController::Destroy() {
      CloseConnection();
   }

   /****************************************/
   /****************************************/

   bool QSwarmController::ConnectToQNetwork() {
      #ifdef _WIN32
         WSADATA wsaData;
         if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            LOGERR << "[Robot " << m_strRobotId << "] WSAStartup failed" << std::endl;
            return false;
         }
      #endif

      // Create socket
      m_nSocket = socket(AF_INET, SOCK_STREAM, 0);
      if (m_nSocket < 0) {
         LOGERR << "[Robot " << m_strRobotId << "] Socket creation failed" << std::endl;
         return false;
      }

      // Setup server address
      struct sockaddr_in serverAddr;
      serverAddr.sin_family = AF_INET;
      serverAddr.sin_port = htons(5555);  // Port 5555
      
      #ifdef _WIN32
         serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
      #else
         inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);
      #endif

      // Connect to server (with retry logic)
      int maxRetries = 10;
      for (int i = 0; i < maxRetries; i++) {
         if (connect(m_nSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == 0) {
            m_bConnected = true;
            LOG << "[Robot " << m_strRobotId << "] Connected to Q-Network server" << std::endl;
            return true;
         }
         
         // Wait before retry
         #ifdef _WIN32
            Sleep(1000);  // 1 second
         #else
            sleep(1);
         #endif
      }

      LOGERR << "[Robot " << m_strRobotId << "] Failed to connect to Q-Network server after " 
             << maxRetries << " attempts" << std::endl;
      return false;
   }

   /****************************************/
   /****************************************/

   std::vector<float> QSwarmController::GetState() {
      std::vector<float> state;

      // Get current position
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      float x = sReading.Position.GetX();
      float y = sReading.Position.GetY();

      // Add position and goal to state
      state.push_back(x);
      state.push_back(y);
      state.push_back(m_cGoalPosition.GetX());
      state.push_back(m_cGoalPosition.GetY());

      // Add proximity sensor readings (24 sensors on FootBot)
      const CCI_FootBotProximitySensor::TReadings& tReadings = m_pcProximity->GetReadings();
      for (size_t i = 0; i < tReadings.size(); ++i) {
         state.push_back(tReadings[i].Value);
      }

      return state;
   }

   /****************************************/
   /****************************************/

   int QSwarmController::GetActionFromQNetwork(const std::vector<float>& state) {
      if (!m_bConnected) {
         // Fallback: random action
         return rand() % 4;
      }

      // Build state message: "STATE|robot_id|x|y|goal_x|goal_y|prox0|...|prox23"
      std::ostringstream oss;
      oss << "STATE|" << m_nRobotIdNum;
      for (float val : state) {
         oss << "|" << val;
      }

      // Send state
      if (!SendMessage(oss.str())) {
         LOGERR << "[Robot " << m_strRobotId << "] Failed to send state" << std::endl;
         return 0;  // Default action: move forward
      }

      // Receive action: "ACTION|action_id"
      std::string response = ReceiveMessage();
      if (response.empty()) {
         LOGERR << "[Robot " << m_strRobotId << "] No response from Q-Network" << std::endl;
         return 0;
      }

      // Parse action
      size_t pos = response.find('|');
      if (pos != std::string::npos) {
         std::string actionStr = response.substr(pos + 1);
         return std::stoi(actionStr);
      }

      return 0;  // Default action
   }

   /****************************************/
   /****************************************/

   void QSwarmController::ExecuteAction(int action) {
      float leftSpeed = 0.0f;
      float rightSpeed = 0.0f;

      switch (action) {
         case 0:  // Move forward
            leftSpeed = m_fVelocity;
            rightSpeed = m_fVelocity;
            break;
         case 1:  // Turn left
            leftSpeed = -m_fVelocity * 0.5f;
            rightSpeed = m_fVelocity * 0.5f;
            break;
         case 2:  // Turn right
            leftSpeed = m_fVelocity * 0.5f;
            rightSpeed = -m_fVelocity * 0.5f;
            break;
         case 3:  // Stop
            leftSpeed = 0.0f;
            rightSpeed = 0.0f;
            break;
         default:
            leftSpeed = m_fVelocity;
            rightSpeed = m_fVelocity;
      }

      // Debug: Log action and velocities
      if (m_nSteps < 3) {
         LOG << "[Robot " << m_strRobotId << "] Action: " << action 
             << ", Left: " << leftSpeed << ", Right: " << rightSpeed << std::endl;
      }

      m_pcWheels->SetLinearVelocity(leftSpeed, rightSpeed);
   }

   /****************************************/
   /****************************************/

   float QSwarmController::CalculateReward(bool& done) {
      float reward = 0.0f;
      done = false;

      // Get current position
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      CVector2 currentPos(sReading.Position.GetX(), sReading.Position.GetY());
      
      // Calculate distance to goal
      float currentDistance = (currentPos - m_cGoalPosition).Length();
      
      // DYNAMIC SWARM COHESION CHECK
      // The swarm center moves along the path from start (4,4) to goal (18,18)
      // This encourages robots to move together toward the goal
      CVector2 startPosition(4.0f, 4.0f);
      CVector2 pathDirection = m_cGoalPosition - startPosition;
      pathDirection.Normalize();
      
      // Expected swarm center based on average progress (simplified: use this robot's progress)
      float totalPathLength = (m_cGoalPosition - startPosition).Length();
      float currentProgress = totalPathLength - currentDistance;  // How far along path
      CVector2 expectedSwarmCenter = startPosition + (pathDirection * currentProgress);
      
      // Allow some deviation from the moving swarm center
      float maxSwarmDeviation = 5.0f;  // Robots can be 5m apart from each other
      float deviationFromSwarm = (currentPos - expectedSwarmCenter).Length();
      
      if (deviationFromSwarm > maxSwarmDeviation && m_nSteps > 10) {
         // Penalty for straying too far from swarm formation
         reward = -2.0f;
         done = true;
         LOG << "[Robot " << m_strRobotId << "] STRAYED FROM SWARM! Deviation: " 
             << deviationFromSwarm << "m" << std::endl;
         return reward;
      }
      
      // BOUNDARY CHECK - Penalize going out of bounds
      if (currentPos.GetX() < 1.0f || currentPos.GetX() > 19.0f ||
          currentPos.GetY() < 1.0f || currentPos.GetY() > 19.0f) {
         reward = -5.0f;
         done = true;
         LOG << "[Robot " << m_strRobotId << "] OUT OF BOUNDS!" << std::endl;
         return reward;
      }
      
      // Check if reached goal (HIGHEST PRIORITY)
      if (ReachedGoal()) {
         reward = 100.0f;  // HUGE reward for reaching goal
         done = true;
         LOG << "[Robot " << m_strRobotId << "] *** GOAL REACHED! ***" << std::endl;
         return reward;
      }
      
      // Check for collision (NEGATIVE OUTCOME) - but only after a few steps
      if (m_nSteps > 3 && DetectCollision()) {
         reward = -10.0f;  // Strong penalty for collision
         done = true;
         LOG << "[Robot " << m_strRobotId << "] COLLISION DETECTED!" << std::endl;
         return reward;
      }

      // STRATEGIC MOVEMENT REWARDS:
      
      // 1. STRONG Progress toward goal (PRIMARY OBJECTIVE)
      float previousDistance = (m_cPreviousPosition - m_cGoalPosition).Length();
      float progressReward = (previousDistance - currentDistance) * 5.0f;  // INCREASED: Strong incentive to move toward goal
      reward += progressReward;
      
      // 2. Swarm cohesion bonus (reward staying together while progressing)
      float cohesionBonus = 0.0f;
      if (deviationFromSwarm < 2.0f) {
         cohesionBonus = 0.4f;  // Tight formation
      } else if (deviationFromSwarm < 4.0f) {
         cohesionBonus = 0.2f;  // Good formation
      }
      reward += cohesionBonus;
      
      // 3. Proximity bonus (encourage getting closer to goal)
      float proximityBonus = 0.0f;
      if (currentDistance < 5.0f) {
         proximityBonus = 1.0f;  // Very close to goal - INCREASED
      } else if (currentDistance < 10.0f) {
         proximityBonus = 0.5f;  // Medium distance - INCREASED
      } else if (currentDistance < 15.0f) {
         proximityBonus = 0.2f;  // Making progress
      }
      reward += proximityBonus;
      
      // 4. Forward movement bonus (encourage any movement toward goal)
      if (progressReward > 0.01f) {
         reward += 0.3f;  // Bonus for making forward progress
      }
      
      // 5. Very small time penalty (don't discourage exploration)
      reward -= 0.005f;
      
      // 6. Obstacle avoidance bonus (reward safe navigation)
      const CCI_FootBotProximitySensor::TReadings& tReadings = m_pcProximity->GetReadings();
      bool nearObstacle = false;
      for (size_t i = 0; i < tReadings.size(); ++i) {
         if (tReadings[i].Value > 0.5f) {
            nearObstacle = true;
            break;
         }
      }
      
      // Reward for safely navigating near obstacles while making progress
      if (nearObstacle && progressReward > 0) {
         reward += 0.2f;  // Bonus for making progress while avoiding obstacles
      }

      return reward;
   }

   /****************************************/
   /****************************************/

   bool QSwarmController::ReachedGoal() {
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      CVector2 currentPos(sReading.Position.GetX(), sReading.Position.GetY());
      
      float distance = (currentPos - m_cGoalPosition).Length();
      return distance < m_fGoalThreshold;
   }

   /****************************************/
   /****************************************/

   bool QSwarmController::DetectCollision() {
      // Check proximity sensors for collisions
      // This is the primary and only collision detection method
      // We rely on proximity sensors rather than movement because:
      // - Robots can legitimately stop (action 3)
      // - Robots can turn in place (actions 1, 2) with minimal forward movement
      const CCI_FootBotProximitySensor::TReadings& tReadings = m_pcProximity->GetReadings();
      for (size_t i = 0; i < tReadings.size(); ++i) {
         // Value > 0.9 indicates very close proximity or contact
         if (tReadings[i].Value > 0.9f) {
            return true;
         }
      }

      return false;
   }

   /****************************************/
   /****************************************/

   void QSwarmController::SendReward(float reward, bool done) {
      if (!m_bConnected) return;

      // Build reward message: "REWARD|robot_id|reward|done"
      std::ostringstream oss;
      oss << "REWARD|" << m_nRobotIdNum << "|" << reward << "|" << (done ? "1" : "0");

      SendMessage(oss.str());

      // No acknowledgment needed - server processes asynchronously
   }

   /****************************************/
   /****************************************/

   void QSwarmController::ResetEpisode() {
      // Increment episode counter
      m_nEpisode++;
      m_nSteps = 0;
      m_bEpisodeDone = false;
      m_fEpisodeReward = 0.0f;

      // Stop the robot
      m_pcWheels->SetLinearVelocity(0.0f, 0.0f);

      // Note: ARGoS will reset robot positions via the experiment file
      // Update previous position
      const CCI_PositioningSensor::SReading& sReading = m_pcPositioning->GetReading();
      m_cPreviousPosition.Set(sReading.Position.GetX(), sReading.Position.GetY());

      LOG << "[Robot " << m_strRobotId << "] Starting episode " << m_nEpisode << std::endl;
   }

   /****************************************/
   /****************************************/

   bool QSwarmController::SendMessage(const std::string& message) {
      if (m_nSocket < 0 || !m_bConnected) return false;

      std::string msg = message + "\n";  // Add newline delimiter
      int sent = send(m_nSocket, msg.c_str(), msg.length(), 0);
      
      return sent > 0;
   }

   /****************************************/
   /****************************************/

   std::string QSwarmController::ReceiveMessage() {
      if (m_nSocket < 0 || !m_bConnected) return "";

      char buffer[4096];
      int received = recv(m_nSocket, buffer, sizeof(buffer) - 1, 0);
      
      if (received > 0) {
         buffer[received] = '\0';
         std::string msg(buffer);
         
         // Remove newline if present
         if (!msg.empty() && msg.back() == '\n') {
            msg.pop_back();
         }
         
         return msg;
      }

      return "";
   }

   /****************************************/
   /****************************************/

   void QSwarmController::CloseConnection() {
      if (m_nSocket >= 0) {
         #ifdef _WIN32
            closesocket(m_nSocket);
            WSACleanup();
         #else
            close(m_nSocket);
         #endif
         m_nSocket = -1;
         m_bConnected = false;
      }
   }

   /****************************************/
   /****************************************/

   /*
    * This statement notifies ARGoS of the existence of the controller.
    * It binds the class passed as first argument to the string passed as
    * second argument.
    */
   REGISTER_CONTROLLER(QSwarmController, "q_swarm_controller")

}
