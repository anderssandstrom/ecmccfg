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
|CTRL_DB_TIME   | 0               | cycles | int    | Controller deadband filter time. Control will be active untill within CTRL_DB_TOL from target position  for CTRL_DB_TIME cycles |

# Monitor

| Macro           | Default   | Unit   | Type   | Description |
|--               |--         |--      |--      |--           |
|MON_AT_TARG_TOL  | Mandatory | EGU    | double | At target monitoring tolerance | 
