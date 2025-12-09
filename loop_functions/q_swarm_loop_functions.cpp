/*
 * Q-Learning Swarm Loop Functions Implementation
 */

#include "q_swarm_loop_functions.h"
#include <argos3/core/simulator/simulator.h>
#include <argos3/core/utility/configuration/argos_configuration.h>
#include <argos3/plugins/simulator/entities/box_entity.h>
#include <cstring>
#include <errno.h>

namespace argos {

   /****************************************/
   /****************************************/

   QSwarmLoopFunctions::QSwarmLoopFunctions() :
      m_nResetSocket(-1),
      m_nResetPort(5556),  // Different port from Q-Network server (5555)
      m_bSocketInitialized(false),
      m_fFormationSize(5.0f),  // 5x5 meter square around swarm center
      m_cSwarmCenter(0.0f, 0.0f),
      m_bFormationViolated(false),
      m_strViolatingRobot("") {
   }

   /****************************************/
   /****************************************/

   QSwarmLoopFunctions::~QSwarmLoopFunctions() {
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::Init(TConfigurationNode& t_tree) {
      // Store initial positions of all foot-bots
      StoreInitialPositions();

      // Read formation size from config (if provided)
      GetNodeAttributeOrDefault(t_tree, "formation_size", m_fFormationSize, m_fFormationSize);

      // Calculate initial swarm center
      m_cSwarmCenter = CalculateSwarmCenter();
      
      LOG << "[LoopFunction] Initialized with " << m_mapStartPositions.size() 
          << " robots" << std::endl;
      LOG << "[LoopFunction] Dynamic formation size: " << m_fFormationSize 
          << "m x " << m_fFormationSize << "m square" << std::endl;
      LOG << "[LoopFunction] Initial swarm center: (" << m_cSwarmCenter.GetX() 
          << ", " << m_cSwarmCenter.GetY() << ")" << std::endl;
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::Reset() {
      // Reset all robots to initial positions
      for (auto& pair : m_mapStartPositions) {
         ResetRobot(pair.first);
      }
      
      // Clear pending resets
      m_mapPendingResets.clear();
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::Destroy() {
      if (m_nResetSocket >= 0) {
         close(m_nResetSocket);
         m_nResetSocket = -1;
      }
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::PreStep() {
      // Update swarm center based on current robot positions
      m_cSwarmCenter = CalculateSwarmCenter();
      
      // Check if any robots are outside the dynamic formation boundary
      CSpace::TMapPerType& tFootBotMap = GetSpace().GetEntitiesByType("foot-bot");
      
      for (auto it = tFootBotMap.begin(); it != tFootBotMap.end(); ++it) {
         CFootBotEntity& cFootBot = *any_cast<CFootBotEntity*>(it->second);
         std::string strId = cFootBot.GetId();
         
         // Get current position
         const CVector3& cPosition = cFootBot.GetEmbodiedEntity().GetOriginAnchor().Position;
         CVector2 cPos2D(cPosition.GetX(), cPosition.GetY());
         
         // Check if outside dynamic formation boundary
         if (IsOutsideFormation(cPos2D)) {
            // Check if this is a new violation (not already pending)
            if (m_mapPendingResets.find(strId) == m_mapPendingResets.end() ||
                !m_mapPendingResets[strId]) {
                
                // Mark ALL robots for reset (entire swarm resets together)
                m_bFormationViolated = true;
                m_strViolatingRobot = strId;
                
                LOG << "[LoopFunction] Robot " << strId << " left formation at (" 
                    << cPos2D.GetX() << ", " << cPos2D.GetY() 
                    << ") - Swarm center: (" << m_cSwarmCenter.GetX() 
                    << ", " << m_cSwarmCenter.GetY() << ")" << std::endl;
                LOG << "[LoopFunction] Distance from center: " 
                    << (cPos2D - m_cSwarmCenter).Length() << "m (max: " 
                    << m_fFormationSize/2.0f << "m)" << std::endl;
                
                // Mark all robots for reset
                for (auto& pair : m_mapStartPositions) {
                    m_mapPendingResets[pair.first] = true;
                }
                
                break;  // No need to check other robots
            }
         }
      }
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::PostStep() {
      // Process any pending resets after physics update
      if (m_bFormationViolated) {
         LOG << "[LoopFunction] === FORMATION VIOLATED - RESETTING ALL ROBOTS ===" << std::endl;
         LOG << "[LoopFunction] Robots will continue with learned Q-Network parameters" << std::endl;
         ProcessPendingResets();
         m_bFormationViolated = false;
      }
   }

   /****************************************/
   /****************************************/

   CColor QSwarmLoopFunctions::GetFloorColor(const CVector2& c_position_on_plane) {
      // Draw only the boundary line of the dynamic formation square
      
      Real halfSize = m_fFormationSize / 2.0f;
      Real lineWidth = 0.1f;  // Width of the boundary line in meters
      
      // Calculate boundaries around swarm center
      Real minX = m_cSwarmCenter.GetX() - halfSize;
      Real maxX = m_cSwarmCenter.GetX() + halfSize;
      Real minY = m_cSwarmCenter.GetY() - halfSize;
      Real maxY = m_cSwarmCenter.GetY() + halfSize;
      
      // Check if position is on any of the four boundary lines
      bool onLeftEdge = (c_position_on_plane.GetX() >= minX - lineWidth && 
                         c_position_on_plane.GetX() <= minX + lineWidth &&
                         c_position_on_plane.GetY() >= minY - lineWidth && 
                         c_position_on_plane.GetY() <= maxY + lineWidth);
      
      bool onRightEdge = (c_position_on_plane.GetX() >= maxX - lineWidth && 
                          c_position_on_plane.GetX() <= maxX + lineWidth &&
                          c_position_on_plane.GetY() >= minY - lineWidth && 
                          c_position_on_plane.GetY() <= maxY + lineWidth);
      
      bool onTopEdge = (c_position_on_plane.GetY() >= maxY - lineWidth && 
                        c_position_on_plane.GetY() <= maxY + lineWidth &&
                        c_position_on_plane.GetX() >= minX - lineWidth && 
                        c_position_on_plane.GetX() <= maxX + lineWidth);
      
      bool onBottomEdge = (c_position_on_plane.GetY() >= minY - lineWidth && 
                           c_position_on_plane.GetY() <= minY + lineWidth &&
                           c_position_on_plane.GetX() >= minX - lineWidth && 
                           c_position_on_plane.GetX() <= maxX + lineWidth);
      
      // Draw boundary line in bright green
      if (onLeftEdge || onRightEdge || onTopEdge || onBottomEdge) {
         return CColor(0, 255, 0);  // Bright green boundary
      }
      
      // Draw a small marker at swarm center (for debugging)
      if ((c_position_on_plane - m_cSwarmCenter).Length() < 0.15f) {
         return CColor(255, 255, 0);  // Yellow center marker
      }
      
      // Goal area marker - small circle (not filled)
      CVector2 goalPos(18.0f, 18.0f);
      Real distToGoal = (c_position_on_plane - goalPos).Length();
      if (distToGoal >= 0.45f && distToGoal <= 0.65f) {
         return CColor(0, 180, 255);  // Cyan goal marker
      }
      
      // Default floor - light gray
      return CColor(220, 220, 220);
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::StoreInitialPositions() {
      // Get all foot-bots in the simulation
      CSpace::TMapPerType& tFootBotMap = GetSpace().GetEntitiesByType("foot-bot");
      
      for (auto it = tFootBotMap.begin(); it != tFootBotMap.end(); ++it) {
         CFootBotEntity& cFootBot = *any_cast<CFootBotEntity*>(it->second);
         
         SRobotStartPosition sPos;
         sPos.Id = cFootBot.GetId();
         sPos.Position = cFootBot.GetEmbodiedEntity().GetOriginAnchor().Position;
         sPos.Orientation = cFootBot.GetEmbodiedEntity().GetOriginAnchor().Orientation;
         
         m_mapStartPositions[sPos.Id] = sPos;
         
         LOG << "[LoopFunction] Stored initial position for " << sPos.Id 
             << ": (" << sPos.Position.GetX() << ", " << sPos.Position.GetY() << ")" 
             << std::endl;
      }
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::ResetRobot(const std::string& str_robot_id) {
      // Find the robot entity
      CFootBotEntity* pcFootBot = nullptr;
      
      try {
         pcFootBot = &dynamic_cast<CFootBotEntity&>(
            GetSpace().GetEntity(str_robot_id));
      } catch (CARGoSException& ex) {
         LOGERR << "[LoopFunction] Error getting robot " << str_robot_id 
                << ": " << ex.what() << std::endl;
         return;
      }
      
      // Get original position
      auto it = m_mapStartPositions.find(str_robot_id);
      if (it == m_mapStartPositions.end()) {
         LOGERR << "[LoopFunction] No initial position found for " << str_robot_id 
                << std::endl;
         return;
      }
      
      const SRobotStartPosition& sPos = it->second;
      
      // Reset position and orientation
      // Important: We need to move the entire embodied entity
      bool bSuccess = MoveEntity(
         pcFootBot->GetEmbodiedEntity(),  // Entity to move
         sPos.Position,                    // New position
         sPos.Orientation,                 // New orientation
         false                             // Check for collisions
      );
      
      if (bSuccess) {
         LOG << "[LoopFunction] ✓ Reset robot " << str_robot_id 
             << " to (" << sPos.Position.GetX() << ", " << sPos.Position.GetY() << ")" 
             << std::endl;
      } else {
         LOGERR << "[LoopFunction] ✗ Failed to reset robot " << str_robot_id 
                << " (collision detected)" << std::endl;
      }
   }

   /****************************************/
   /****************************************/

   CVector2 QSwarmLoopFunctions::CalculateSwarmCenter() {
      CSpace::TMapPerType& tFootBotMap = GetSpace().GetEntitiesByType("foot-bot");
      
      if (tFootBotMap.empty()) {
         return CVector2(0.0f, 0.0f);
      }
      
      Real sumX = 0.0f;
      Real sumY = 0.0f;
      int count = 0;
      
      for (auto it = tFootBotMap.begin(); it != tFootBotMap.end(); ++it) {
         CFootBotEntity& cFootBot = *any_cast<CFootBotEntity*>(it->second);
         const CVector3& cPosition = cFootBot.GetEmbodiedEntity().GetOriginAnchor().Position;
         
         sumX += cPosition.GetX();
         sumY += cPosition.GetY();
         count++;
      }
      
      return CVector2(sumX / count, sumY / count);
   }

   /****************************************/
   /****************************************/

   bool QSwarmLoopFunctions::IsOutsideFormation(const CVector2& c_position) {
      // Check if position is outside the square boundary centered on swarm
      Real halfSize = m_fFormationSize / 2.0f;
      
      Real distX = std::abs(c_position.GetX() - m_cSwarmCenter.GetX());
      Real distY = std::abs(c_position.GetY() - m_cSwarmCenter.GetY());
      
      // Robot is outside if it's beyond half the square size in either direction
      return (distX > halfSize || distY > halfSize);
   }

   /****************************************/
   /****************************************/

   void QSwarmLoopFunctions::ProcessPendingResets() {
      // Reset all robots that are marked for reset
      int resetCount = 0;
      for (auto& pair : m_mapPendingResets) {
         if (pair.second) {  // If reset is pending
            ResetRobot(pair.first);
            pair.second = false;  // Clear the flag
            resetCount++;
         }
      }
      
      if (resetCount > 0) {
         LOG << "[LoopFunction] Reset " << resetCount << " robots to original positions" << std::endl;
         LOG << "[LoopFunction] Episode continues with learned Q-Network weights" << std::endl;
      }
   }

   /****************************************/
   /****************************************/

   /*
    * This statement notifies ARGoS of the existence of the loop functions.
    */
   REGISTER_LOOP_FUNCTIONS(QSwarmLoopFunctions, "q_swarm_loop_functions")

}
