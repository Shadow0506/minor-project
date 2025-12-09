#ifndef Q_SWARM_LOOP_FUNCTIONS_H
#define Q_SWARM_LOOP_FUNCTIONS_H

/*
 * Q-Learning Swarm Loop Functions
 * 
 * This loop function manages episode resets by listening for
 * reset requests from robots and moving them back to their
 * original starting positions.
 */

#include <argos3/core/simulator/loop_functions.h>
#include <argos3/core/simulator/space/space.h>
#include <argos3/core/simulator/entity/floor_entity.h>
#include <argos3/plugins/robots/foot-bot/simulator/footbot_entity.h>
#include <argos3/core/utility/math/vector3.h>
#include <argos3/core/utility/math/quaternion.h>
#include <map>
#include <string>

// For socket server to receive reset requests
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>

namespace argos {

   class QSwarmLoopFunctions : public CLoopFunctions {

   public:

      QSwarmLoopFunctions();
      virtual ~QSwarmLoopFunctions();

      virtual void Init(TConfigurationNode& t_tree);
      virtual void Reset();
      virtual void Destroy();
      virtual void PreStep();
      virtual void PostStep();
      virtual CColor GetFloorColor(const CVector2& c_position_on_plane);

   private:

      /* Structure to store original robot positions */
      struct SRobotStartPosition {
         CVector3 Position;
         CQuaternion Orientation;
         std::string Id;
      };

      /* Map of robot ID to original position */
      std::map<std::string, SRobotStartPosition> m_mapStartPositions;

      /* Map of robot ID to pending reset flag */
      std::map<std::string, bool> m_mapPendingResets;

      /* Socket for receiving reset requests */
      int m_nResetSocket;
      int m_nResetPort;
      bool m_bSocketInitialized;

      /* Dynamic formation boundaries */
      Real m_fFormationSize;  // Size of the square (e.g., 5.0 = 5x5 meter square)
      CVector2 m_cSwarmCenter;  // Current center of the swarm
      
      /* Track if any robot left formation this step */
      bool m_bFormationViolated;
      std::string m_strViolatingRobot;

      /* Initialize socket server for reset requests */
      bool InitializeResetSocket();

      /* Check for reset requests from controllers */
      void CheckForResetRequests();

      /* Calculate the current swarm center (mean position) */
      CVector2 CalculateSwarmCenter();

      /* Check if a position is outside the dynamic formation boundary */
      bool IsOutsideFormation(const CVector2& c_position);

      /* Reset a specific robot to its original position */
      void ResetRobot(const std::string& str_robot_id);

      /* Reset all robots that have pending resets */
      void ProcessPendingResets();

      /* Store initial positions of all robots */
      void StoreInitialPositions();
   };

}

#endif
