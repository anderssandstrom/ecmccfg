/*************************************************************************\
* Copyright (c) 2026 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution.
*
*  main.cpp
*
*  Minimal example for the additive C++ logic interface in ecmc.
*
\*************************************************************************/

#include "ecmcCppLogic.hpp"

struct NativeBounceLogic : public ecmcCpp::LogicBase {
  static constexpr uint16_t lower_turnaround_position {100};
  static constexpr uint16_t upper_turnaround_position {12800};

  uint16_t actual_position {0};
  uint16_t drive_control {0};
  int16_t velocity_setpoint {1000};
  int32_t cycle_counter {0};

  NativeBounceLogic() {
    ecmc.input("ec.s14.positionActual01", actual_position)
        .output("ec.s14.driveControl01", drive_control)
        .output("ec.s14.velocitySetpoint01", velocity_setpoint);

    ecmcCpp::setEnableDbg(true);

    epics.readOnly("main.actual_position", actual_position)
         .readOnly("main.cycle_counter", cycle_counter)
         .writable("main.velocity_setpoint", velocity_setpoint);
  }

  void run() override {
    cycle_counter += 1;
    drive_control = 0x0001;

    if (velocity_setpoint == 0) {
      velocity_setpoint = 1000;
    }
    if (actual_position <= lower_turnaround_position) {
      velocity_setpoint = 1000;
    } else if (actual_position >= upper_turnaround_position) {
      velocity_setpoint = -1000;
    }

    if ((cycle_counter % 1000) == 0) {
      ecmcCpp::publishDebugText("cpp logic example running");
    }
  }
};

ECMC_CPP_LOGIC_REGISTER_DEFAULT(NativeBounceLogic)
