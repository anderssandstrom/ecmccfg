# General

Most functionalites can be disabled by setting the macro to NA

# Axis

| Macro                     | Default                       | Unit   | Type   | Description |
|--                         |--                             |--      |--      |--           |
|ID                         | Mandatory                     |        | Uint   | Axis Index  | 
|EGU                        |                               |        | string | Unit  | 

# Controller
| Macro                     | Default                       | Unit   | Type   | Description |
|--                         |--                             |--      |--      |--           |
|CTRL_KP                    | 0.0                           |        | double | Position controller proportional gain |
|CTRL_KI                    | 0.0                           |        | double | Position controller integral gain. |
|CTRL_KD                    | 0.0                           |        | double | Position controller derivative gain. |
|CTRL_KFF                   | 1.0                           |        | double | Position controller feed-forward gain. | 
|CTRL_INR_TOL               | MON_AT_TRG_TOL                |  EGU   | double | Position inner controller tolerance (CTRL_INR* will be used when inside this tolerance distance to target position). |
|CTRL_INR_KP                | 0.0                           |        | double | Position inner controller proportinal gain. |
|CTRL_INR_KI                | 0.0                           |        | double | Position inner controller integral gain. |
|CTRL_INR_KD                | 0.0                           |        | double | Position inner controller derivative gain. |
|CTRL_LIM_MIN               |                               |        | double | Minimum output of controller. Function activates if macro is set. |
|CTRL_LIM_MAX               |                               |        | double | Maximum output of controller. Function activates if macro is set. |
|CTRL_LIM_I_MIN             |                               |        | double | Minimum integrator output of controller. Function activates if macro is set. |
|CTRL_LIM_I_MAX             |                               |        | double | Maximum integrator output of controller. Function activates if macro is set. |
|CTRL_DB_TOL                |                               |   EGU  | double | Controller deadband. Control will be active untill within CTRL_DB_TOL from target position. |
|CTRL_DB_TIME               | 0                             | cycles | int    | Controller deadband filter time. Control will be active untill within CTRL_DB_TOL from target position for CTRL_DB_TIME cycles. |


# Drive

| Macro                     | Default                       | Unit   | Type   | Description |
|--                         |--                             |--      |--      |--           |
|DRV_TYPE                   | STEPPER                       | STEPPER/DS402 | string | Drive type: STEPPER=simple stepper; DS402=servo or advanced stepper. |
|DRV_MODE                   | CSV                           | CSV/CSP| string | Drive mode: CSV=Cyclic Sync. Velocity Setpoint, CSP=Cyclic Sync. Position setpoint. |
|DRV_SCL_NUM                | Mandatory for phys axis       |        | double | Output scaling numerator. Scale factor is calc=DRV_SCL_NUM/DRV_SCL_DENOM (CSV: scale velo setpoint; CSP: Scale position setpoint). |
|DRV_SCL_DENOM              | Mandatory for phys axis       |        | double | Output scaling denominator. Scale factor is calc=DRV_SCL_NUM/DRV_SCL_DENOM (CSV: scale velo setpoint; CSP: Scale position setpoint). |
|DRV_EC_CTRL_WD             | Mandatory for phys axis       |        | string | Control word EtherCAT link. |
|DRV_EN_CMD_BIT             | 0                             |        | uint   | Bit index of enable command in DRV_EC_CTRL_WD. Defaults to 0 (suitable for Beckhoff stepper). |
|DRV_EC_STAT_WD             | Mandatory for phys axis       |        | string | Status word EtherCAT link. |
|DRV_EN_STAT_BIT            | 1                             |        | uint   | Bit index of enabled status in DRV_EC_STAT_WD. Defaults to 1 (suitable for Beckhoff stepper). |
|DRV_EC_SETPOS              | Mandatory for phys axis       |        | string | Setpoint EtherCAT link (DRV_MODE=CSV: Velocity setpoint; DRV_MODE=CSP: Position setpoint). |
|DRV_EC_RED_TRQ             |                               |        | string | Reduce torque EtherCAT link (if set then reduce torque functionality will be enabled). |
|DRV_RED_TRQ_BIT            |                               |        | uint   | Bit index of reduce torque command in DRV_EC_CTRL_WD (if set then DRV_EC_RED_TRQ will not be used). |
|DRV_EC_RST                 |                               |        | string | Reset EtherCAT link (if set then any axis reset will also set this bit). |
|DRV_RST_BIT                |                               |        | uint   | Bit index of reset command in DRV_EC_CTRL_WD (if set then DRV_EC_RST will not be used). |
|DRV_EC_WRN                 |                               |        | string | Warning EtherCAT link. |
|DRV_WRN_BIT                |                               |        | uint   | Bit index of warning status in DRV_EC_STAT_WD (if set then DRV_EC_WRN will not be used). |
|DRV_EC_ERR_1               |                               |        | string | Error 1 EtherCAT link. |
|DRV_ERR_1_BIT              |                               |        | uint   | Bit index of error 1 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_1 will not be used). |
|DRV_EC_ERR_2               |                               |        | string | Error 2 EtherCAT link. |
|DRV_ERR_2_BIT              |                               |        | uint   | Bit index of error 2 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_2 will not be used). |
|DRV_EC_ERR_3               |                               |        | string | Error 3 EtherCAT link. |
|DRV_ERR_3_BIT              |                               |        | uint   | Bit index of error 3 status in DRV_EC_STAT_WD (if set then DRV_EC_ERR_3 will not be used). |
|DRV_EC_BRK                 |                               |        | string | Brake EtherCAT link. |
|DRV_BRK_BIT                |                               |        | uint   | Bit index of brake command in DRV_EC_CTRL_WD (if set then DRV_EC_BRK will not be used). |
|DRV_BRK_OPN_DLY            | 0                             | cycles | uint   | Open delay time of brake (will only be applied if DRV_EC_BRK or DRV_BRK_BIT is defined). |
|DRV_BRK_CLS_AHEAD          | 0                             | cycles | uint   | Close ahead time of brake (will only be applied if DRV_EC_BRK or DRV_BRK_BIT is defined). |

# Encoder
| Macro                     | Default                       | Unit   | Type   | Description |
|--                         |--                             |--      |--      |--           |
|ENC_EGU                    | EGU                           |        | string | Unit of encoder actual position |
|ENC_DESC                   |                               |        | string | Description of encoder. |
|ENC_EC_ACTPOS              | Mandatory for internal source |        | string | Actual position EtherCAT link. |
|ENC_EC_CTRL_WD             | Mandatory if any of the ENC*BIT macros are used |        | string | Control word EtherCAT link. |
|ENC_EC_STAT_WD             | Mandatory if any of the ENC*BIT macros are used |        | string | Status word EtherCAT link. |
|ENC_SCL_NUM                | Mandatory for internal source |        | double | Input scaling numerator. |
|ENC_SCL_DENOM              | Mandatory for internal source |        | double | Input scaling denominator. |
|ENC_SRC                    | INT (internal)                | INT/PLC| string | Encoder source. INT = internal source; PLC = External source. |
|ENC_TYPE                   | ABS                           | ABS/INC| string | ABS = Absolute encoder; INC = Incremental encoder. |
|ENC_BITS                   | Mandatory for internal source |        | uint   | Encoder bit count. |
|ENC_ABS_BITS               | ENC_BITS                      |        | uint   | Encoder absoulute bit count. |
|ENC_ABS_OFF                | 0                             | EGU    | double | Encoder absoulute offset. |
|ENC_MASK                   | Applied if set                |        | 64bit hex | Encoder raw mask (0xffff0). |
|ENC_EC_RST                 |                               |        | string | Reset EtherCAT link (if set then any axis reset will also set this bit). |
|ENC_RST_BIT                |                               |        | uint   | Bit index of reset command in ENC_EC_CTRL_WD (if set then ENC_EC_RST will not be used). |
|ENC_EC_WRN                 |                               |        | string | Warning EtherCAT link. |
|ENC_WRN_BIT                |                               |        | uint   | Bit index of warning status in ENC_EC_STAT_WD (if set then ENC_EC_WRN will not be used). |
|ENC_EC_ERR_1               |                               |        | string | Error 1 EtherCAT link. |
|ENC_ERR_1_BIT              |                               |        | uint   | Bit index of error 1 status in ENC_EC_STAT_WD (if set then ENC_EC_ERR_1 will not be used). |
|ENC_EC_ERR_2               |                               |        | string | Error 2 EtherCAT link. |
|ENC_ERR_2_BIT              |                               |        | uint   | Bit index of error 2 status in ENC_EC_STAT_WD (if set then ENC_EC_ERR_2 will not be used). |
|ENC_EC_ERR_3               |                               |        | string | Error 3 EtherCAT link. |
|ENC_ERR_3_BIT              |                               |        | uint   | Bit index of error 3 status in ENC_EC_STAT_WD (if set then ENC_EC_ERR_3 will not be used). |
|ENC_EC_LTCH_POS            |                               |        | string | Latch position EtherCAT link. |
|ENC_EC_ARM_LTCH            |                               |        | string | Arm latch EtherCAT link. |
|ENC_ARM_LTCH_BIT           |                               |        | uint   | Bit index arm latch command in ENC_EC_CTRL_WD (if set then ENC_EC_ARM_LTCH will not be used). |
|ENC_EC_LTCHD               |                               |        | string | Latch status EtherCAT link. |
|ENC_LTCHD_BIT              |                               |        | uint   | Bit index arm latch status in ENC_EC_STAT_WD (if set then ENC_EC_LTCHD will not be used). |
|ENC_FLT_VEL_SIZE           |                               |        | uint   | Encoder velocity filter size |
|ENC_FLT_POS_SIZE           |                               |        | uint   | Encoder position filter size |
|ENC_PRIM                   |                               | YES/NO | string | Use this encoder for control (only one encoder can be used for control) |
|ENC_MAX_DIFF_TO_PRIM       |                               | EGU    | string | Max position difference between this encoder and teh primary encoder. |
|ENC_HME_SEQ                |                               |        | uint   | Homing sequence id. |
|ENC_HME_POS                |                               | EGU    | double | Encoder homing position. |
|ENC_HME_PST_MV_POS         |                               | EGU    | double | Move to this position after successfull homing |
|ENC_HME_LTCH_CNT           | 0                             |        | uint   | Number of latches before homing (for homing incremnetal encoder on index pulse). |
|ENC_HME_VEL_TO_CAM         |                               | EGU/s  | double | Velocity when approaching (first) cam. |
|ENC_HME_VEL_OFF_CAM        |                               | EGU/s  | double | Velocity when leaving (first) cam. |
|ENC_HME_SEQ_TME_OUT        |                               | s      | uint   | Timeout for sequence. |
|ENC_HME_REF_TO_ENC_AT_STRT |                               |        | uint   | Encoder index of master encoder. Ref. this encoder to master/other encoder at startup. |
|ENC_HME_REF_AT_HME         |                               | YES/NO | string | Ref. this encoder when a referecnce seq is successfull (also if other encoder is primary) |
|ENC_HME_EC_EXT_TRG         |                               |        | string | EtherCAT link for trigger external/drive homing seq (example smaract). | |
|ENC_HME_EC_EXT_RDY         |                               |        | string | EtherCAT link for status/ready external/drive homing seq (example smaract). |
|ENC_HME_ACC                |                               | EGU/s/s| double | Acceleration used during homing sequence. |
|ENC_HME_DEC                |                               | EGU/s/s| double | Acceleration used during homing sequence. |

# Trajectory
| Macro                     | Default                       | Unit      | Type   | Description |
|--                         |--                             |--         |--      |--           |
|TRJ_SRC                    | INT                           | INT/PLC   | string | Trajectory source. INT = internal source; PLC = External source. |
|TRJ_VEL                    | Mandatory                     | EGU/s     | double | Trajectory velocity |
|TRJ_JVEL                   | TRJ_VEL                       | EGU/s     | double | Trajectory jog velocity |
|TRJ_ACC                    | Mandatory                     | EGU/s/s   | double | Trajectory acceleration |
|TRJ_DEC                    | Mandatory                     | EGU/s/s   | double | Trajectory deceleration |
|TRJ_EMERG_DEC              | TRJ_DEC *10                   | EGU/s/s   | double | Trajectory emergency deceleration |
|TRJ_JERK                   | TRJ_ACC                       | EGU/s/s/s | double | Trajectory jerk |
|TRJ_MOD_RNG                |                               | EGU       | double | Modulo range (0..TRJ_MOD_RNG)  |
|TRJ_MOD_TYP                |                               |           | uint   | Modulo type |

# Monitor

| Macro                     | Default                       | Unit      | Type   | Description |
|--                         |--                             |--         |--      |--           |
|MON_EC_LIM_FWD             | Mandatory                     |           | string | Ethercat link for forward limit switch. |
|MON_LIM_FWD_POL            | NC                            | NC/NO     | string | Polarity of forward limit switch. |
|MON_EC_LIM_BWD             | Mandatory                     |           | string | Ethercat link for backward limit switch. |
|MON_LIM_BWD_POL            | NC                            | NC/NO     | string | Polarity of Backward limit switch. |
|MON_EC_LIM_BWD             | Mandatory                     |           | string | Ethercat link for backward limit switch. |
|MON_LIM_BWD_POL            | NC                            | NC/NO     | string | Polarity of Backward limit switch. |
|MON_EC_HW_IL               | Mandatory                     |           | string | Ethercat link for hardware interlock. |
|MON_HW_IL_POL              | NC                            | NC/NO     | string | Polarity of hardware interlock. |
|MON_EC_HME                 | Mandatory                     |           | string | Ethercat link for home sensor. |
|MON_HME_POL                | NC                            | NC/NO     | string | Polarity of home sensor. |
|MON_EC_ANA_IL              |                               |           | string | Ethercat link for analog interlock, will disable drive if, for NO polarity, a value of MON_EC_ANA_IL > MON_ANA_IL_RAW_LIM (one usecase is temperature sensors, vacuum motors) |
|MON_ANA_IL_POL             | N0                            | NC/NO   | string | Polarity of analog interlock (NO = High value is bad; NC = Low value is bad) |
|MON_ANA_IL_RAW_LIM         | 0                             |  raw  (as MON_EC_ANA_IL) | string | Raw limit to trigger disable axis. |
|MON_POS_LAG_TOL            |                               |  EGU | double | Position lag tolerance |
|MON_POS_LAG_TIME           | 1                             |  cycles | double | Position lag time (if position error is > MON_POS_LAG_TOL for more than MON_POS_LAG_TIME axis will stop) |
|MON_AT_TRG_TOL             | mandatory for motor record    |  EGU | double | At target tolerance. |
|MON_AT_TRG_TIME            | 1                             |  cycles | double | At target filter time (if actpos-targetpos < MON_AT_TRG_TOL for more than MON_AT_TRG_TIME the axis will be considered to have reached target) |
|MON_MAX_VEL                |                               |  EGU/s  | double | Maximum velocity |
|MON_MAX_VEL_TRJ_IL_TIME    | 1                             |  cycles | uint   | Max velocity filter time for controlled rampdown. If velo > MON_MAX_VEL for more than MON_MAX_VEL_TRJ_IL_TIME then axis will initiate a ramp down |
|MON_MAX_VEL_DRV_IL_TIME    | MON_MAX_VEL_TRJ_IL_TIME       |  cycles | uint   | Max velocity filter time for disabling of axis. If velo > MON_MAX_VEL for more than MON_MAX_VEL_DRV_IL_TIME then axis will be disabled |
|MON_DIFF_VEL               |                               |  EGU/s  | double | Maximum difference between actual velocity and setpoint velocity |
|MON_DIFF_VEL_TRJ_IL_TIME   | 1                             |  cycles | uint   | Diff velocity filter time for controlled rampdown. If abs(veloact-veloset) > MON_DIFF_VEL for more than MON_DIFF_VEL_TRJ_IL_TIME then axis will initiate a ramp down |
|MON_DIFF_VEL_DRV_IL_TIME   | MON_DIFF_VEL_TRJ_IL_TIME      |  cycles | uint   | Diff velocity filter time for disabling of axis. If abs(veloact-veloset) > MON_DIFF_VEL for more than MON_DIFF_VEL_DRV_IL_TIME then axis will be disabled |
|MON_SLIM_FWD               |                               |  EGU    | double | Forward soft limit |
|MON_SLIM_BWD               |                               |  EGU    | double | Baclward soft limit |

# syncs

| Macro                     | Default                       | Unit    | Type   | Description |
|--                         |--                             |--       |--      |--           |
|PLC_EN                     | NO                            | YES/NO  | string | Enable axis PLC |
|PLC_ALLW_CMDS              | NO                            | YES/NO  | string | Axis allowed to take commands from PLC:s |
|PLC_FILE                   |                               |         | string/path | Path to plc code file |
|PLC_MACROS                 |                               |         | string | Macros for PLC file |


ecmcConfigOrDie "Cfg.SetAxisPLCEnable(${ID},${PLC_EN=0})"
ecmcConfigOrDie "Cfg.SetAxisAllowCommandsFromPLC(${ID},${PLC_ALLW_CMDS=0})"

#- PLC code
#- {%- if plc.code %}
#-     {%- for line in plc.code %}
#-         ecmcConfigOrDie "Cfg.AppendAxisPLCExpr(${ID})={{ line|replace(';', '|') }}"
#-     {%- endfor %}
#- {%- endif %}

${SCRIPTEXEC} ${ecmccfg_DIR}loadAxisPLCFile.cmd "AX_ID=${ID}, FILE=${PLC_FILE}, PLC_MACROS='${PLC_MACROS=''}'"


# handle in other files:

HOME_POS = ENC_HME_POS

POST_ENA  if ENC_HME_PST_MV_POS is set
POST_POS  = ENC_HME_PST_MV_POS
REF_STRT  = ENC_HME_REF_TO_ENC_AT_STRTENC_HME_REF_TO_ENC_AT_STRT
HOME_PROC = ENC_HME_SEQ
ACC       = ENC_HME_ACC
DEC       = ENC_HME_DEC

TRJ_MOD_TYP docs
cycles to time!!!

validate homing params

