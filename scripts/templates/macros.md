# Axis

| Macro         | Default    | Unit   | Type  | Description |
|--             |--          |--      |--     |--           |
|ID             | Mandatory  |        | Uint  | Axis Index  | 

# Controller
| Macro         | Default         | Unit   | Type   | Description |
|--             |--               |--      |--      |--           |
|CTRL_KP        | 0.0             |        | double | Position controller proportinal gain |
|CTRL_KI        | 0.0             |        | double | Position controller integral gain    |
|CTRL_KD        | 0.0             |        | double | Position controller derivative gain  |
|CTRL_KFF       | 1.0             |        | double | Position controller feed-forward gain| 
|CTRL_IN_TOL    | MON_AT_TARG_TOL |  EGU   | double | Position inner controller tolerance (CTRL_IN* will be used when inside this tolerance distance to target position)  |
|CTRL_IN_KP     | 0.0             |        | double | Position inner controller proportinal gain |
|CTRL_IN_KI     | 0.0             |        | double | Position inner controller integral gain    |
|CTRL_IN_KD     | 0.0             |        | double | Position inner controller derivative gain  |
|CTRL_LIM_MIN   | Active if set   |        | double | Minimum output of controller               |
|CTRL_LIM_MAX   | Active if set   |        | double | Maximum output of controller               |
|CTRL_LIM_I_MIN | Active if set   |        | double | Minimum integrator output of controller    |
|CTRL_LIM_I_MAX | Active if set   |        | double | Maximum integrator output of controller    |
|CTRL_DB_TOL    | Active if set   |   EGU  | double | Controller deadband. Control will be active untill within CTRL_DB_TOL from target position      |
|CTRL_DB_TIME   | 0               | cycles | int    | Controller deadband filter time. Control will be active untill within CTRL_DB_TOL from target position for CTRL_DB_TIME cycles |

# Monitor

| Macro           | Default   | Unit   | Type   | Description |
|--               |--         |--      |--      |--           |
|MON_AT_TARG_TOL  | Mandatory | EGU    | double | At target monitoring tolerance | 

# Drive

| Macro           | Default                 | Unit   | Type   | Description |
|--               |--                       |--      |--      |--           |
|DRV_TYPE         | STEPPER                 |        | string | Drive type: STEPPER=simple stepper, 1=DS402 (servo, advanced stepper) |
|DRV_MODE         | CSV                     |        | string | Drive mode: CSV=Cyclic Sync. Velocity Setpoint, CSP=Cyclic Sync. Position setpoint|
|DRV_SCL_NUM      | Mandatory for phys axis |        | double | Output scaling numerator. Scale factor is calc=DRV_SCL_NUM/DRV_SCL_DENOM (CSV: scale velo setpoint; CSP: Scale position setpoint) |
|DRV_SCL_DENOM    | Mandatory for phys axis |        | double | Output scaling denominator. Scale factor is calc=DRV_SCL_NUM/DRV_SCL_DENOM (CSV: scale velo setpoint; CSP: Scale position setpoint) |
|DRV_EC_CTRL_WD   | Mandatory for phys axis |        | string | Control word Ethercat link |
|DRV_EN_CMD_BIT   | 0                       |        | uint   | Bit index of enable command in DRV_EC_CTRL_WD. Defaults to 0 (for Beckhoff stepper) |
|DRV_EC_STAT_WD   | Mandatory for phys axis |        | string | Status word Ethercat link |
|DRV_EN_STAT_BIT  | 1                       |        | uint   | Bit index of enabled status in DRV_EC_STAT_WD. Defaults to 1 (for Beckhoff stepper) |
|DRV_EC_SET       | Mandatory for phys axis |        | string | Setpoint ethercat link (DRV_MODE=CSV: Velocity setpoint; DRV_MODE=CSP: Position setpoint) |
|DRV_EC_RED_TRQ   |                         |        | string | Reduce torque ethercat link (if set then reduce torque functionality will be enabled) |
|DRV_RED_TRQ_BIT  |                         |        | uint   | Bit index of reduce torque command in DRV_EC_CTRL_WD (if set then DRV_EC_RED_TRQ will not be used)|
|DRV_EC_RST       |                         |        | string | Reset ethercat link (if set then any axis reset will also set this bit) |
|DRV_RST_BIT      |                         |        | uint   | Bit index of reset command in DRV_EC_CTRL_WD (if set then DRV_EC_RST will not be used)|
|DRV_EC_WRN       |                         |        | string | Warning ethercat link |
|DRV_WRN_BIT      |                         |        | uint   | Bit index of warning status in DRV_EC_STAT_WD (if set then DRV_EC_WRN will not be used)|
|DRV_EC_ERR_1     |                         |        | string | Error 1 ethercat link |
|DRV_ERR_1_BIT    |                         |        | uint   | Bit index of error 1 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_1 will not be used)|
|DRV_EC_ERR_2     |                         |        | string | Error 2 ethercat link |
|DRV_ERR_2_BIT    |                         |        | uint   | Bit index of error 2 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_2 will not be used)|
|DRV_EC_ERR_3     |                         |        | string | Error 3 ethercat link |
|DRV_ERR_3_BIT    |                         |        | uint   | Bit index of error 3 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_3 will not be used)|
|DRV_EC_BRK       |                         |        | string | Brake ethercat link |
|DRV_BRK_BIT      |                         |        | uint   | Bit index of brake command in DRV_EC_CTRL_WD (if set then DRV_EC_BRK will not be used)|
|DRV_BRK_OPN_DLY  | 0                       | cycles | uint   | Open delay time of brake (will only be applied if DRV_EC_BRK or DRV_BRK_BIT is defined)|
|DRV_BRK_CLS_AHEAD| 0                       | cycles | uint   | Close ahead time of brake (will only be applied if DRV_EC_BRK or DRV_BRK_BIT is defined)|
