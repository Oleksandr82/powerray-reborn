"""One-off generator for param_dictionary.json.

Builds the static parameter dictionary used by the cockpit's Parameters
panel. Run manually whenever the dictionary needs regenerating from scratch
(normally you should just hand-edit param_dictionary.json directly instead).
"""
import json

# type/range are informational only (best-effort, from PX4 ~2017-2019 vintage
# docs and firmware source around the time PowerVision likely forked it).
d = {}

def add(name, desc, type_='FLOAT', minv=None, maxv=None, unit=None, source='px4', values=None):
    entry = {'desc': desc, 'type': type_, 'source': source}
    if minv is not None: entry['min'] = minv
    if maxv is not None: entry['max'] = maxv
    if unit: entry['unit'] = unit
    if values: entry['values'] = values
    d[name] = entry

# --- ATT_* : legacy PX4 attitude estimator (Q-filter / complementary filter) ---
add('ATT_ACC_COMP', 'Enable/disable acceleration compensation in attitude estimation (centripetal, tangential).', 'BOOL', 0, 1)
add('ATT_BIAS_MAX', 'Gyro bias limit for the attitude estimator.', 'FLOAT', unit='rad/s')
add('ATT_EXT_HDG_M', 'External heading usage mode (0=none, 1=vision, 2=motion capture).', 'ENUM', 0, 2)
add('ATT_MAG_DECL', 'Magnetic declination, set automatically if ATT_MAG_DECL_A is enabled.', 'FLOAT', unit='deg')
add('ATT_MAG_DECL_A', 'Automatic magnetic declination lookup from GPS position.', 'BOOL', 0, 1)
add('ATT_VIBE_THRESH', 'Vibration threshold that triggers a warning/failsafe reaction.', 'FLOAT')
add('ATT_W_ACC', 'Complementary filter accelerometer weight.', 'FLOAT', 0, 1)
add('ATT_W_EXT_HDG', 'Complementary filter external heading weight.', 'FLOAT', 0, 1)
add('ATT_W_GYRO_BIAS', 'Complementary filter gyro bias weight.', 'FLOAT', 0, 1)
add('ATT_W_MAG', 'Complementary filter magnetometer weight.', 'FLOAT', 0, 1)

# --- BAT_* : battery estimation ---
add('BAT_CAPACITY', 'Battery capacity; -1 disables capacity-based remaining-charge estimation.', 'FLOAT', unit='mAh')
add('BAT_CRIT_THR', 'Critical battery threshold (fraction of full charge that triggers critical failsafe).', 'FLOAT', 0, 1)
add('BAT_C_OFFSET', 'Battery current sensor analog offset/calibration; -1 = use board default.', 'FLOAT')
add('BAT_C_SCALING', 'Battery current sensor analog scaling factor; -1 = use board default.', 'FLOAT', unit='A/V')
add('BAT_LOW_THR', 'Low battery threshold (fraction of full charge that triggers low-battery failsafe).', 'FLOAT', 0, 1)
add('BAT_N_CELLS', 'Number of battery cells in series.', 'INT', 0, 24)
add('BAT_V_CHARGED', 'Full/charged voltage per battery cell.', 'FLOAT', unit='V')
add('BAT_V_EMPTY', 'Empty voltage per battery cell.', 'FLOAT', unit='V')
add('BAT_V_LOAD_DROP', 'Voltage drop compensation per battery cell under full load.', 'FLOAT', unit='V')
add('BAT_V_SCALING', 'Battery voltage sensor analog scaling factor; -1 = use board default.', 'FLOAT', unit='V/V')

# --- CAL_* : sensor calibration (per-run values, not tunables) ---
add('CAL_ACC0_ID', 'Device ID of accelerometer #0 used for the stored calibration below.', 'INT')
add('CAL_ACC0_XOFF', 'Accelerometer #0 X-axis offset.', 'FLOAT', unit='m/s^2')
add('CAL_ACC0_XSCALE', 'Accelerometer #0 X-axis scale factor.', 'FLOAT')
add('CAL_ACC0_YOFF', 'Accelerometer #0 Y-axis offset.', 'FLOAT', unit='m/s^2')
add('CAL_ACC0_YSCALE', 'Accelerometer #0 Y-axis scale factor.', 'FLOAT')
add('CAL_ACC0_ZOFF', 'Accelerometer #0 Z-axis offset.', 'FLOAT', unit='m/s^2')
add('CAL_ACC0_ZSCALE', 'Accelerometer #0 Z-axis scale factor.', 'FLOAT')
add('CAL_ACC_PRIME', 'Device ID of the primary (preferred) accelerometer.', 'INT')
add('CAL_GYRO0_ID', 'Device ID of gyroscope #0 used for the stored calibration below.', 'INT')
add('CAL_GYRO0_XOFF', 'Gyroscope #0 X-axis offset.', 'FLOAT', unit='rad/s')
add('CAL_GYRO0_XSCALE', 'Gyroscope #0 X-axis scale factor.', 'FLOAT')
add('CAL_GYRO0_YOFF', 'Gyroscope #0 Y-axis offset.', 'FLOAT', unit='rad/s')
add('CAL_GYRO0_YSCALE', 'Gyroscope #0 Y-axis scale factor.', 'FLOAT')
add('CAL_GYRO0_ZOFF', 'Gyroscope #0 Z-axis offset.', 'FLOAT', unit='rad/s')
add('CAL_GYRO0_ZSCALE', 'Gyroscope #0 Z-axis scale factor.', 'FLOAT')
add('CAL_GYRO_PRIME', 'Device ID of the primary (preferred) gyroscope.', 'INT')
add('CAL_MAG0_ID', 'Device ID of magnetometer #0.', 'INT')
add('CAL_MAG0_ROT', 'Rotation of magnetometer #0 relative to the airframe/hull (-1 = use board default).', 'INT', -1, 35)
add('CAL_MAG1_ID', 'Device ID of magnetometer #1 (if present).', 'INT')
add('CAL_MAG1_ROT', 'Rotation of magnetometer #1 relative to the airframe/hull.', 'INT', -1, 35)
add('CAL_MAG2_ID', 'Device ID of magnetometer #2 (if present).', 'INT')
add('CAL_MAG2_ROT', 'Rotation of magnetometer #2 relative to the airframe/hull.', 'INT', -1, 35)
add('CAL_MAG_SIDES', 'Bitmask of which of the 6 cube sides were completed during onboard mag calibration.', 'INT', 0, 63)

# --- CBRK_* : safety "circuit breakers" (disable specific pre-arm/failsafe checks) ---
add('CBRK_AIRSPD_CHK', 'Circuit breaker: disable airspeed sensor check (irrelevant underwater; fixed-wing leftover).', 'INT', values={0:'Check enabled', 162128:'Check disabled'})
add('CBRK_BUZZER', 'Circuit breaker: disable the buzzer/tone alarm.', 'INT', values={0:'Buzzer enabled', 782090:'Buzzer disabled'})
add('CBRK_ENGINEFAIL', 'Circuit breaker: disable the engine/motor failure detection check.', 'INT', values={0:'Check enabled', 284953:'Check disabled'})
add('CBRK_GPSFAIL', 'Circuit breaker: disable the GPS failure check (expected to be disabled — no GPS underwater).', 'INT', values={0:'Check enabled', 240024:'Check disabled'})
add('CBRK_IO_SAFETY', 'Circuit breaker: disable the IO safety switch requirement before arming.', 'INT', values={0:'Check enabled', 22027:'Check disabled'})
add('CBRK_NO_VISION', 'Circuit breaker: disable the requirement for vision/optical-flow position source.', 'INT', values={0:'Check enabled', 328754:'Check disabled'})
add('CBRK_RATE_CTRL', 'Circuit breaker: disable the rate controller (dangerous — motors would run open-loop).', 'INT', values={0:'Check enabled', 140253:'Check disabled'})
add('CBRK_SUPPLY_CHK', 'Circuit breaker: disable the power supply health check.', 'INT', values={0:'Check enabled', 894281:'Check disabled'})
add('CBRK_USB_CHK', 'Circuit breaker: disable the "USB connected, refuse to arm" safety check.', 'INT', values={0:'Check enabled', 197848:'Check disabled'})

# --- COM_* : commander (arming, failsafe reactions) ---
add('COM_AUTOS_PAR', 'Parachute deployment on auto mission failure (fixed-wing feature, likely unused).', 'BOOL', 0, 1)
add('COM_DISARM_LAND', 'Time after landing detection before auto-disarm; 0 disables.', 'FLOAT', unit='s')
add('COM_DL_LOSS_T', 'Data link (telemetry) loss timeout before triggering failsafe.', 'FLOAT', unit='s')
add('COM_DL_REG_T', 'Data link regain time required before clearing the data-link-lost failsafe.', 'FLOAT', unit='s')
add('COM_EF_C2T', 'Engine failure: current-to-throttle ratio threshold used for failure detection.', 'FLOAT')
add('COM_EF_THROT', 'Engine failure: throttle threshold above which the check is active.', 'FLOAT', 0, 1)
add('COM_EF_TIME', 'Engine failure: time above threshold before it is flagged as failed.', 'FLOAT', unit='s')
add('COM_HOME_H_T', 'Horizontal threshold for accepting a new home position.', 'FLOAT', unit='m')
add('COM_HOME_V_T', 'Vertical threshold for accepting a new home position.', 'FLOAT', unit='m')
add('COM_LOW_BAT_ACT', 'Action to take when the low-battery threshold is crossed.', 'ENUM', 0, 2, values={0:'Warning only', 1:'Return to launch', 2:'Land'})
add('COM_RC_IN_MODE', 'RC input source selection.', 'ENUM', 0, 2, values={0:'RC transmitter required', 1:'Joystick/no-RC OK', 2:'Both'})
add('COM_RC_LOSS_T', 'RC signal loss timeout before the RC-lost failsafe triggers.', 'FLOAT', unit='s')

# --- Misc single-off params (likely PowerVision-added or forked-in for the sub) ---
add('DEEP_SENSOR_ID', 'Device ID of the depth/pressure sensor in use.', 'INT', source='guess')
add('DRIVE_DEEP_P', 'P-gain of the depth-hold ("drive to target depth") controller.', 'FLOAT', source='guess')
add('EKF2_REC_RPL', 'EKF2 replay logging mode (this drone appears to use the legacy INAV estimator, so likely unused/vestigial).', 'INT', 0, 2)
add('FW_AIRSPD_TRIM', 'Fixed-wing trim airspeed — vestigial parameter from the shared PX4 codebase, not applicable to a sub.', 'FLOAT', unit='m/s')

# --- GF_* : geofence ---
add('GF_ACTION', 'Action to take on geofence breach.', 'ENUM', 0, 4, values={0:'None', 1:'Warning', 2:'Hold', 3:'Return', 4:'Terminate'})
add('GF_ALTMODE', 'Geofence altitude reference mode.', 'ENUM', 0, 1, values={0:'WGS84', 1:'AMSL'})
add('GF_COUNT', 'Number of geofence polygon points loaded (NaN = none loaded).', 'INT')
add('GF_MAX_HOR_DIST', 'Max horizontal distance from home before geofence breach (NaN = disabled).', 'FLOAT', unit='m')
add('GF_MAX_VER_DIST', 'Max vertical distance from home before geofence breach (NaN = disabled).', 'FLOAT', unit='m')
add('GF_SOURCE', 'Geofence source selection (0=global position, 1=GPS directly).', 'ENUM', 0, 1)

# --- INAV_* : legacy PX4 "LPE" local position estimator (predates EKF2) ---
add('INAV_DELAY_GPS', 'Assumed GPS measurement delay compensation.', 'FLOAT', unit='s')
add('INAV_DISAB_MOCAP', 'Disable use of motion-capture position input.', 'BOOL', 0, 1)
add('INAV_FLOW_DIST_X', 'Optical flow sensor X offset from vehicle center of gravity.', 'FLOAT', unit='m')
add('INAV_FLOW_DIST_Y', 'Optical flow sensor Y offset from vehicle center of gravity.', 'FLOAT', unit='m')
add('INAV_FLOW_K', 'Optical flow scale/gain factor.', 'FLOAT')
add('INAV_FLOW_Q_MIN', 'Minimum optical flow quality accepted as valid.', 'FLOAT', 0, 1)
add('INAV_LAND_DISP', 'Landing detector: displacement threshold.', 'FLOAT', unit='m')
add('INAV_LAND_T', 'Landing detector: time threshold.', 'FLOAT', unit='s')
add('INAV_LAND_THR', 'Landing detector: throttle threshold.', 'FLOAT', 0, 1)
add('INAV_LIDAR_ERR', 'Expected rangefinder/lidar (altimeter) measurement error/noise.', 'FLOAT', unit='m')
add('INAV_LIDAR_EST', 'Enable rangefinder-based altitude estimation.', 'BOOL', 0, 1)
add('INAV_LIDAR_OFF', 'Rangefinder offset from ground/expected reading at zero altitude.', 'FLOAT', unit='m')
add('INAV_W_ACC_BIAS', 'Estimator weight: accelerometer bias correction.', 'FLOAT')
add('INAV_W_GPS_FLOW', 'Estimator weight: blending GPS with optical flow velocity.', 'FLOAT')
add('INAV_W_MOC_P', 'Estimator weight: motion-capture position.', 'FLOAT')
add('INAV_W_XY_FLOW', 'Estimator weight: horizontal position/velocity from optical flow.', 'FLOAT')
add('INAV_W_XY_GPS_P', 'Estimator weight: horizontal position from GPS.', 'FLOAT')
add('INAV_W_XY_GPS_V', 'Estimator weight: horizontal velocity from GPS.', 'FLOAT')
add('INAV_W_XY_RES_V', 'Estimator weight: horizontal velocity residual/reset gain.', 'FLOAT')
add('INAV_W_XY_VIS_P', 'Estimator weight: horizontal position from vision.', 'FLOAT')
add('INAV_W_XY_VIS_V', 'Estimator weight: horizontal velocity from vision.', 'FLOAT')
add('INAV_W_Z_BARO', 'Estimator weight: vertical position from barometer (repurposed for depth/pressure on this sub).', 'FLOAT')
add('INAV_W_Z_GPS_P', 'Estimator weight: vertical position from GPS.', 'FLOAT')
add('INAV_W_Z_GPS_V', 'Estimator weight: vertical velocity from GPS.', 'FLOAT')
add('INAV_W_Z_LIDAR', 'Estimator weight: vertical position from rangefinder.', 'FLOAT')
add('INAV_W_Z_VIS_P', 'Estimator weight: vertical position from vision.', 'FLOAT')

# --- MAV_* : MAVLink link config ---
add('MAV_COMP_ID', 'MAVLink component ID this system reports itself as.', 'INT', 0, 255)
add('MAV_FWDEXTSP', 'Forward external setpoint messages over MAVLink.', 'BOOL', 0, 1)
add('MAV_RADIO_ID', 'ID of a specific radio/telemetry system to bind MAVLink handling to (0 = any/none).', 'INT')
add('MAV_SYS_ID', 'MAVLink system ID (matches "target_system" used throughout the cockpit).', 'INT', 1, 255)
add('MAV_TEST_PAR', 'Internal test parameter, no functional effect.', 'FLOAT')
add('MAV_TYPE', 'MAVLink MAV_TYPE reported in HEARTBEAT (numeric vehicle type code).', 'INT')
add('MAV_USEHILGPS', 'Use simulated (Hardware-In-the-Loop) GPS instead of a real GPS receiver.', 'BOOL', 0, 1)

# --- MC_* : multicopter attitude/rate controller (repurposed for thruster attitude control) ---
add('MC_ACRO_P_MAX', 'Max pitch rate commanded by the stick in ACRO/manual-rate mode.', 'FLOAT', unit='deg/s')
add('MC_ACRO_R_MAX', 'Max roll rate commanded by the stick in ACRO/manual-rate mode.', 'FLOAT', unit='deg/s')
add('MC_ACRO_Y_MAX', 'Max yaw rate commanded by the stick in ACRO/manual-rate mode.', 'FLOAT', unit='deg/s')
add('MC_PITCHRATE_D', 'Pitch rate controller D gain.', 'FLOAT')
add('MC_PITCHRATE_FF', 'Pitch rate controller feed-forward gain.', 'FLOAT')
add('MC_PITCHRATE_I', 'Pitch rate controller I gain.', 'FLOAT')
add('MC_PITCHRATE_MAX', 'Max commanded pitch rate.', 'FLOAT', unit='deg/s')
add('MC_PITCHRATE_P', 'Pitch rate controller P gain.', 'FLOAT')
add('MC_PITCH_P', 'Pitch angle controller P gain (outer loop).', 'FLOAT')
add('MC_PITCH_TC', 'Pitch angle controller time constant.', 'FLOAT', unit='s')
add('MC_RATT_TH', 'Threshold between manual rate mode and attitude-stabilized mode.', 'FLOAT', 0, 1)
add('MC_ROLLRATE_D', 'Roll rate controller D gain.', 'FLOAT')
add('MC_ROLLRATE_FF', 'Roll rate controller feed-forward gain.', 'FLOAT')
add('MC_ROLLRATE_I', 'Roll rate controller I gain.', 'FLOAT')
add('MC_ROLLRATE_MAX', 'Max commanded roll rate.', 'FLOAT', unit='deg/s')
add('MC_ROLLRATE_P', 'Roll rate controller P gain.', 'FLOAT')
add('MC_ROLL_P', 'Roll angle controller P gain (outer loop). 0.0 here likely means roll-hold is disabled on this hull.', 'FLOAT')
add('MC_ROLL_TC', 'Roll angle controller time constant.', 'FLOAT', unit='s')
add('MC_YAWRATE_D', 'Yaw rate controller D gain.', 'FLOAT')
add('MC_YAWRATE_FF', 'Yaw rate controller feed-forward gain.', 'FLOAT')
add('MC_YAWRATE_I', 'Yaw rate controller I gain.', 'FLOAT')
add('MC_YAWRATE_MAX', 'Max commanded yaw rate.', 'FLOAT', unit='deg/s')
add('MC_YAWRATE_P', 'Yaw rate controller P gain.', 'FLOAT')
add('MC_YAWRAUTO_MAX', 'Max yaw rate during autonomous/auto-heading control.', 'FLOAT', unit='deg/s')
add('MC_YAW_FF', 'Yaw angle controller feed-forward gain.', 'FLOAT')
add('MC_YAW_P', 'Yaw angle controller P gain (outer loop).', 'FLOAT')

# --- MIS_* : mission / auto behavior ---
add('MIS_ALTMODE', 'Mission altitude reference mode.', 'ENUM', 0, 2)
add('MIS_DIST_1WP', 'Max allowed distance to the first waypoint (sanity check).', 'FLOAT', unit='m')
add('MIS_LTRMIN_ALT', 'Minimum loiter altitude used during auto missions.', 'FLOAT', unit='m')
add('MIS_ONBOARD_EN', 'Enable onboard (companion computer) mission control.', 'BOOL', 0, 1)
add('MIS_TAKEOFF_ALT', 'Default takeoff altitude for auto missions.', 'FLOAT', unit='m')
add('MIS_YAWMODE', 'Mission yaw behavior mode.', 'ENUM', 0, 4)
add('MIS_YAW_ERR', 'Max yaw error accepted before considering a waypoint yaw achieved.', 'FLOAT', unit='deg')
add('MIS_YAW_TMT', 'Max time allowed to reach the desired mission yaw; -1 disables the timeout.', 'FLOAT', unit='s')
add('MPC_XY_CRUISE', 'Cruise (auto mode) horizontal speed setpoint.', 'FLOAT', unit='m/s')

# --- NAV_* : navigator (RTL, geofence failsafe, loiter) ---
add('NAV_ACC_RAD', 'Acceptance radius for waypoints (distance considered "reached").', 'FLOAT', unit='m')
add('NAV_AH_ALT', 'Altitude used for the "safe/rally" auto home point.', 'FLOAT', unit='m')
add('NAV_AH_LAT', 'Latitude of the "safe/rally" auto home point (irrelevant underwater — no GPS).', 'FLOAT', unit='deg')
add('NAV_AH_LON', 'Longitude of the "safe/rally" auto home point (irrelevant underwater — no GPS).', 'FLOAT', unit='deg')
add('NAV_DLL_ACT', 'Action on datalink loss.', 'ENUM', 0, 3)
add('NAV_DLL_AH_T', 'Time before datalink-loss failsafe switches to the auto/safe home point.', 'FLOAT', unit='s')
add('NAV_DLL_CHSK', 'Datalink-loss: use "critical" home point instead of standard home.', 'BOOL', 0, 1)
add('NAV_DLL_CH_ALT', 'Altitude of the critical/emergency home point for datalink loss.', 'FLOAT', unit='m')
add('NAV_DLL_CH_LAT', 'Latitude of the critical/emergency home point for datalink loss.', 'FLOAT', unit='deg')
add('NAV_DLL_CH_LON', 'Longitude of the critical/emergency home point for datalink loss.', 'FLOAT', unit='deg')
add('NAV_DLL_CH_T', 'Time before switching to the critical/emergency home point.', 'FLOAT', unit='s')
add('NAV_DLL_N', 'Number of datalink-loss cycles/attempts before final action.', 'INT')
add('NAV_GPSF_LT', 'GPS-failure failsafe: loiter time before further action.', 'FLOAT', unit='s')
add('NAV_GPSF_P', 'GPS-failure failsafe: manual throttle/pitch used during descent.', 'FLOAT')
add('NAV_GPSF_R', 'GPS-failure failsafe: roll angle used during the fallback maneuver.', 'FLOAT', unit='deg')
add('NAV_GPSF_TR', 'GPS-failure failsafe: throttle used during the fallback maneuver.', 'FLOAT', 0, 1)
add('NAV_LOITER_RAD', 'Loiter/circle radius used in auto modes.', 'FLOAT', unit='m')
add('NAV_RCL_ACT', 'Action on RC signal loss.', 'ENUM', 0, 6)
add('NAV_RCL_LT', 'Time before RC-loss failsafe switches to the auto/safe home point.', 'FLOAT', unit='s')

# --- PARK_* : likely PowerVision "parking"/hover-in-place controller for the sub ---
add('PARK_DEEP_I', 'I-gain of the depth-hold ("park at depth") controller.', 'FLOAT', source='guess')
add('PARK_DEEP_P', 'P-gain of the depth-hold ("park at depth") controller.', 'FLOAT', source='guess')
add('PARK_DEEP_THRUST', 'Thrust limit/authority allotted to the depth-hold ("park") controller.', 'FLOAT', 0, 1, source='guess')

# --- PV_* : PowerVision-specific (all *guessed*, no public documentation exists) ---
add('PV_BOARD_ID', 'Identifier of the specific PV flight-controller board/hardware revision.', 'INT', source='guess')
add('PV_DEEPTEST', 'Depth-sensor self-test flag/result.', 'BOOL', 0, 1, source='guess')
add('PV_INTOWATER', 'Water-immersion/leak sensor state or threshold (config-side twin of PV_V_INTOWATER).', 'BOOL', 0, 1, source='guess')
add('PV_SD_SIZE', 'Detected SD card size (GB) in the camera/logging unit.', 'FLOAT', unit='GB', source='guess')
add('PV_SPEEDADJUST', 'Global speed-scaling factor applied on top of the L/M/H gear selection.', 'FLOAT', source='guess')
add('PV_THRUST_D', 'Thrust/motor controller D gain.', 'FLOAT', source='guess')
add('PV_THRUST_I', 'Thrust/motor controller I gain.', 'FLOAT', source='guess')
add('PV_THRUST_P', 'Thrust/motor controller P gain.', 'FLOAT', source='guess')
add('PV_VERSION', 'PowerVision firmware/config version number.', 'INT', source='guess')
add('PV_V_ESC1COUNT', 'Usage/error counter reported by ESC #1 (thruster 1 motor controller).', 'INT', source='guess')
add('PV_V_ESC2COUNT', 'Usage/error counter reported by ESC #2 (thruster 2 motor controller).', 'INT', source='guess')
add('PV_V_ESC3COUNT', 'Usage/error counter reported by ESC #3 (thruster 3 motor controller).', 'INT', source='guess')
add('PV_V_ESCVER1', 'Firmware version reported by ESC #1.', 'INT', source='guess')
add('PV_V_ESCVER2', 'Firmware version reported by ESC #2.', 'INT', source='guess')
add('PV_V_ESCVER3', 'Firmware version reported by ESC #3.', 'INT', source='guess')
add('PV_V_FISHING', 'Fish-finder / fishing-mode feature toggle.', 'BOOL', 0, 1, source='guess')
add('PV_V_INTOWATER', 'Water-immersion/leak sensor live state (0=dry, 1=water detected).', 'BOOL', 0, 1, source='guess')
add('PV_V_KEY_FLAG', 'Activation flag checked at startup — confirmed this session as the account-activation unlock bit.', 'BOOL', 0, 1, source='confirmed')
add('PV_V_LASTARM', 'Timestamp/counter of the last successful arm event.', 'INT', source='guess')
add('PV_V_LOGCOUNT', 'Number of log files stored / log session counter.', 'INT', source='guess')
add('PV_V_PARAMVER', 'Parameter set/schema version (used to detect parameter migrations across firmware updates).', 'INT', source='guess')
add('PV_V_RC_MODE', 'RC stick-mode configuration (Mode 1-4 stick layout selection, confirmed reading integer 4 this session).', 'INT', 1, 4, source='confirmed')
add('PV_V_RC_UPDATE', 'Flag/counter indicating an RC firmware or binding update event.', 'BOOL', 0, 1, source='guess')
add('PV_V_SD_FMT', 'SD card format status/request flag for the camera unit.', 'BOOL', 0, 1, source='guess')
add('PV_V_STARTCOUNT', 'Total power-on/boot cycle counter.', 'INT', source='guess')
add('PV_V_STAT', 'General device status/error bitmask.', 'INT', source='guess')
add('PV_V_VER', 'Overall system/firmware version number.', 'INT', source='guess')
add('PV_YAW_DELAY', 'Delay applied to yaw response (seen in STATUSTEXT as "pv_yaw_delay"), likely damping for yaw thruster response.', 'FLOAT', unit='us', source='guess')
add('PV_YIELDTEST', 'Manufacturing/production yield self-test flag.', 'BOOL', 0, 1, source='guess')

# --- PWM_* : output PWM ranges ---
add('PWM_AUX_DISARMED', 'PWM output value on AUX channels while disarmed.', 'INT', unit='us')
add('PWM_AUX_MAX', 'Max PWM output value on AUX channels.', 'INT', unit='us')
add('PWM_AUX_MIN', 'Min PWM output value on AUX channels.', 'INT', unit='us')
add('PWM_AUX_REV1', 'Reverse direction of AUX PWM output channel 1.', 'BOOL', 0, 1)
add('PWM_AUX_REV2', 'Reverse direction of AUX PWM output channel 2.', 'BOOL', 0, 1)
add('PWM_AUX_REV3', 'Reverse direction of AUX PWM output channel 3.', 'BOOL', 0, 1)
add('PWM_AUX_REV4', 'Reverse direction of AUX PWM output channel 4.', 'BOOL', 0, 1)
add('PWM_AUX_REV5', 'Reverse direction of AUX PWM output channel 5.', 'BOOL', 0, 1)
add('PWM_AUX_REV6', 'Reverse direction of AUX PWM output channel 6.', 'BOOL', 0, 1)
add('PWM_DISARMED', 'PWM output value on main outputs while disarmed.', 'INT', unit='us')
add('PWM_MAX', 'Max PWM output value on main outputs.', 'INT', unit='us')
add('PWM_MIN', 'Min PWM output value on main outputs.', 'INT', unit='us')

# --- RC1..RC18_* : per-channel RC calibration (repeat for 18 channels) ---
for ch in range(1, 19):
    add(f'RC{ch}_DZ', f'Dead-zone around center/trim for RC input channel {ch}.', 'FLOAT', unit='us')
    add(f'RC{ch}_MAX', f'Max calibrated PWM value for RC input channel {ch}.', 'FLOAT', unit='us')
    add(f'RC{ch}_MIN', f'Min calibrated PWM value for RC input channel {ch}.', 'FLOAT', unit='us')
    add(f'RC{ch}_REV', f'Reverse/invert RC input channel {ch} (1=normal, -1=reversed).', 'FLOAT', values={1:'Normal', -1:'Reversed'})
    add(f'RC{ch}_TRIM', f'Center/trim PWM value for RC input channel {ch}.', 'FLOAT', unit='us')

add('RC_ACRO_TH', 'RC switch threshold for engaging ACRO (manual rate) mode.', 'FLOAT', 0, 1)
add('RC_ASSIST_TH', 'RC switch threshold for engaging assisted flight mode.', 'FLOAT', 0, 1)
add('RC_AUTO_TH', 'RC switch threshold for engaging auto/mission mode.', 'FLOAT', 0, 1)
add('RC_CHAN_CNT', 'Detected number of active RC input channels.', 'INT')
add('RC_DSM_BIND', 'Spektrum DSM satellite receiver bind command trigger (NaN = idle).', 'INT')
add('RC_FAILS_THR', 'RC failsafe throttle threshold used to detect signal loss.', 'FLOAT')
add('RC_KILLSWITCH_TH', 'RC switch threshold for engaging the kill switch (immediate motor stop).', 'FLOAT', 0, 1)
add('RC_LOITER_TH', 'RC switch threshold for engaging loiter mode.', 'FLOAT', 0, 1)
add('RC_MAP_ACRO_SW', 'RC channel mapped to the ACRO mode switch (0 = unassigned).', 'INT', 0, 18)
add('RC_MAP_AUX1', 'RC channel mapped to AUX passthrough output 1.', 'INT', 0, 18)
add('RC_MAP_AUX2', 'RC channel mapped to AUX passthrough output 2.', 'INT', 0, 18)
add('RC_MAP_AUX3', 'RC channel mapped to AUX passthrough output 3.', 'INT', 0, 18)
add('RC_MAP_AUX4', 'RC channel mapped to AUX passthrough output 4.', 'INT', 0, 18)
add('RC_MAP_AUX5', 'RC channel mapped to AUX passthrough output 5.', 'INT', 0, 18)
add('RC_MAP_FAILSAFE', 'RC channel used to explicitly signal failsafe from the transmitter.', 'INT', 0, 18)
add('RC_MAP_FLAPS', 'RC channel mapped to flaps (fixed-wing leftover, unused on this sub).', 'INT', 0, 18)
add('RC_MAP_FLTMODE', 'RC channel mapped to the flight-mode selector switch.', 'INT', 0, 18)
add('RC_MAP_KILL_SW', 'RC channel mapped to the kill switch.', 'INT', 0, 18)
add('RC_MAP_LOITER_SW', 'RC channel mapped to the loiter-mode switch.', 'INT', 0, 18)
add('RC_MAP_MODE_SW', 'RC channel mapped to the nav mode switch — likely the button whose state we surfaced as HEARTBEAT.base_mode bit 0 (Stable Image/Depth-Fixed).', 'INT', 0, 18)
add('RC_MAP_OFFB_SW', 'RC channel mapped to the offboard-control-enable switch.', 'INT', 0, 18)
add('RC_MAP_PARAM1', 'RC channel mapped to tunable parameter 1 (in-flight parameter tuning knob).', 'INT', 0, 18)
add('RC_MAP_PARAM2', 'RC channel mapped to tunable parameter 2 (in-flight parameter tuning knob).', 'INT', 0, 18)
add('RC_MAP_PARAM3', 'RC channel mapped to tunable parameter 3 (in-flight parameter tuning knob).', 'INT', 0, 18)
add('RC_MAP_PITCH', 'RC channel mapped to pitch stick input.', 'INT', 0, 18)
add('RC_MAP_POSCTL_SW', 'RC channel mapped to the position-control-mode switch.', 'INT', 0, 18)
add('RC_MAP_RATT_SW', 'RC channel mapped to the rate/attitude-mode switch.', 'INT', 0, 18)
add('RC_MAP_RETURN_SW', 'RC channel mapped to the return-to-launch switch.', 'INT', 0, 18)
add('RC_MAP_ROLL', 'RC channel mapped to roll stick input.', 'INT', 0, 18)
add('RC_MAP_THROTTLE', 'RC channel mapped to throttle stick input.', 'INT', 0, 18)
add('RC_MAP_YAW', 'RC channel mapped to yaw stick input.', 'INT', 0, 18)
add('RC_OFFB_TH', 'RC switch threshold for engaging offboard control mode.', 'FLOAT', 0, 1)
add('RC_POSCTL_TH', 'RC switch threshold for engaging position-control mode.', 'FLOAT', 0, 1)
add('RC_RATT_TH', 'RC switch threshold for engaging rate-control (manual) mode.', 'FLOAT', 0, 1)
add('RC_RETURN_TH', 'RC switch threshold for engaging return-to-launch.', 'FLOAT', 0, 1)
add('RC_TH_USER', 'User-selectable throttle curve/threshold mode.', 'INT')

# --- RTL_* : return-to-launch ---
add('RTL_DESCEND_ALT', 'Altitude at which RTL switches from cruise to final descent.', 'FLOAT', unit='m')
add('RTL_LAND_DELAY', 'Delay before landing once RTL reaches home; -1 disables auto-land (loiter instead).', 'FLOAT', unit='s')
add('RTL_MIN_DIST', 'Minimum distance from home below which RTL climbs directly instead of cruising.', 'FLOAT', unit='m')
add('RTL_RETURN_ALT', 'Altitude used during the RTL cruise/return leg.', 'FLOAT', unit='m')

# --- SDLOG_* : onboard logging ---
add('SDLOG_EXT', 'Extended/verbose logging profile toggle.', 'BOOL', 0, 1)
add('SDLOG_GPSTIME', 'Wait for a valid GPS time before starting a new log file.', 'BOOL', 0, 1)
add('SDLOG_PRIO_BOOST', 'Priority boost given to the logging thread.', 'INT')
add('SDLOG_RATE', 'Maximum onboard logging rate.', 'FLOAT', unit='Hz')
add('SDLOG_UTC_OFFSET', 'UTC time offset applied to log file timestamps.', 'FLOAT', unit='min')

# --- SENS_* / SYS_* : sensor hub & system ---
add('SENS_BARO_QNH', 'Barometer sea-level pressure reference (irrelevant underwater; fixed-wing/altitude leftover).', 'FLOAT', unit='hPa')
add('SENS_BOARD_ROT', 'Rotation of the flight-controller board relative to the vehicle body/hull.', 'ENUM', 0, 35)
add('SENS_BOARD_X_OFF', 'Board mounting X-axis offset correction, in degrees.', 'FLOAT', unit='deg')
add('SENS_BOARD_Y_OFF', 'Board mounting Y-axis offset correction, in degrees.', 'FLOAT', unit='deg')
add('SENS_BOARD_Z_OFF', 'Board mounting Z-axis offset correction, in degrees.', 'FLOAT', unit='deg')
add('SENS_DPRES_ANSC', 'Differential pressure sensor analog scale (airspeed sensor, fixed-wing leftover).', 'FLOAT')
add('SENS_DPRES_OFF', 'Differential pressure sensor offset (airspeed sensor, fixed-wing leftover).', 'FLOAT')
add('SYS_AUTOCONFIG', 'Trigger automatic reset of all parameters to airframe defaults.', 'BOOL', 0, 1)
add('SYS_AUTOSTART', 'Airframe/vehicle configuration preset ID applied at first boot.', 'INT')
add('SYS_MC_EST_GROUP', 'Selected position/attitude estimator group (0 = legacy INAV/LPE estimator, matching the INAV_* params seen here).', 'ENUM', 0, 2)
add('SYS_PARAM_VER', 'Parameter definition schema version, used to detect/convert outdated parameter sets.', 'INT')
add('SYS_RESTART_TYPE', 'Type of the most recent restart (0=normal power-cycle, 1=in-air, 2=data-loss).', 'ENUM', 0, 2)

# --- VT_* : VTOL (fixed-wing/multicopter hybrid) — entirely vestigial on a sub ---
add('VT_NAV_FORCE_VT', 'VTOL: force multicopter mode during RTL/mission regardless of transition state (vestigial, VTOL-only feature).', 'BOOL', 0, 1)
add('VT_OPT_RECOV_EN', 'VTOL: enable optimal recovery during back-transition (vestigial, VTOL-only feature).', 'BOOL', 0, 1)
add('VT_TYPE', 'VTOL airframe type (vestigial, VTOL-only feature — this sub is neither a plane nor VTOL).', 'ENUM', 0, 2)
add('VT_WV_LND_EN', 'VTOL: enable wind-vane weathervaning during landing (vestigial, VTOL-only feature).', 'BOOL', 0, 1)
add('VT_WV_LTR_EN', 'VTOL: enable wind-vane weathervaning during loiter (vestigial, VTOL-only feature).', 'BOOL', 0, 1)
add('VT_WV_YAWR_SCL', 'VTOL: weathervaning yaw rate scale (vestigial, VTOL-only feature).', 'FLOAT')

add('_HASH_CHECK', 'Internal parameter-file integrity hash used by PX4 to detect out-of-sync parameter definitions; not user-meaningful.', 'FLOAT')

# Preserve any 'default' values (captured from the live drone via
# dump_live_params.py / Playwright + merge) already present in an existing
# param_dictionary.json, so re-running this generator doesn't wipe them out.
try:
    with open('param_dictionary.json') as f:
        existing = json.load(f)
    for name, entry in existing.items():
        if name in d and 'default' in entry:
            d[name]['default'] = entry['default']
except FileNotFoundError:
    pass

with open('param_dictionary.json', 'w') as f:
    json.dump(d, f, indent=2, sort_keys=True)
print(f'Wrote {len(d)} entries to param_dictionary.json')
