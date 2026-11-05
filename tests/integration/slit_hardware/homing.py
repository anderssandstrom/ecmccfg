"""Explicitly selected real EL7031 limit homing; no home cam/index required."""
import math
import time
import unittest
from slit_recovery import wait_checked, motor_idle


def check_homing_support(rig):
    cfg = rig.profile['homing']
    if cfg['axis'] != 'TR_HI': raise ValueError('real limit homing is commissioned only for EL7031 TR_HI')
    positive = ('search_velocity', 'edge_velocity', 'acceleration', 'deceleration', 'timeout',
                'max_search_travel', 'max_total_travel', 'raw_counts_per_mm')
    if any(not math.isfinite(cfg[k]) or cfg[k] <= 0 for k in positive):
        raise ValueError('hardware homing speeds, times, scales and travel bounds must be finite and positive')
    if cfg['edge_velocity'] > cfg['search_velocity']: raise ValueError('slow home edge velocity exceeds search velocity')
    if cfg['search_velocity'] > rig.get('TR_HI', '.VMAX'): raise ValueError('home search exceeds motor VMAX')
    if cfg['raw_position'] != 'm0s009-Enc01-PosAct' or cfg['raw_bits'] != 26 or cfg['raw_counts_per_mm'] != 4096:
        raise ValueError('homing raw travel guard must match the commissioned EL5042 channel/scaling')
    if cfg['max_search_travel'] > 100 or cfg['max_total_travel'] < cfg['max_search_travel']:
        raise ValueError('hardware homing travel budget exceeds the commissioned approximately 100 mm stroke')
    if not all(math.isfinite(cfg[k]) for k in ('home_position', 'post_move_position')):
        raise ValueError('finite home and post-home coordinates required')
    if rig.client.get(rig.prefix+'HardwareSlitTest:HomingSchema') != 1:
        raise RuntimeError('restart the hardware IOC with the updated HI homing YAML and marker')
    for field in ('-HomProc', '-HomPos', '-VelToHom', '-VelFrmHom', '-AccHom', '-HomUseHVEL'):
        rig.get('TR_HI', field)
    for suffix in ('', '.ESLO', '.EOFF'): rig.client.get(rig.prefix+cfg['raw_position']+suffix)
    if (rig.client.get(rig.prefix+cfg['raw_position']+'.ESLO') != 1
            or rig.client.get(rig.prefix+cfg['raw_position']+'.EOFF') != 0):
        raise RuntimeError('homing travel guard requires unscaled EL5042 raw counts')
    low, high = rig.get('TR_HI', '-CfgDLLM-RB'), rig.get('TR_HI', '-CfgDHLM-RB')
    if low <= cfg['home_position'] <= high:
        raise RuntimeError('hardware homing test reference must lie outside the configured soft limits')
    if not low < cfg['post_move_position'] < high:
        raise RuntimeError('post-home target must be inside the configured soft limits')
    if not 0 < cfg['post_move_position']-cfg['home_position'] < cfg['max_search_travel']:
        raise RuntimeError('backward-limit post move must move inward within the stage stroke')


class HomingTests(unittest.TestCase):
    def exercise(self, sequence, interface, post=False):
        rig, cfg, axis = self.rig, self.rig.profile['homing'], 'TR_HI'
        number = rig.profile['axes'][axis]
        fields = ('-HomProc.OMSL', '-HomProc', '-HomPos', '-VelToHom', '-VelFrmHom', '-AccHom',
                  '-HomUseHVEL', '-MtnCmd_.DISA', '-MtnCmd_.DISV')
        saved_fields = {field: rig.get(axis, field) for field in fields}
        saved_hold = rig.get(axis, rig.encoder_force_suffix(True))
        complete = None
        with rig.native_configuration(axis):
            transport = rig.open_text_commands()
            saved_cfg = {}
            try:
                query = lambda key: rig.text_command(f'GetAxis{key}({number})', query=True)
                def config(key, value):
                    key = 'HomePostMvPos' if key == 'HomePostMoveTargetPosition' else key
                    rig.text_command(f'Cfg.SetAxis{key}({number},{value:.12g})')
                previous_encoder = query('EncConfigIndex')
                rig.text_command(f'Cfg.SelectAxisEncConfig({number},2)')
                keys = ('HomeSeqId', 'HomePosition', 'HomeVelTowardsCam', 'HomeVelOffCam',
                        'HomeAcc', 'HomeDec', 'HomePostMoveEnable', 'HomePostMoveTargetPosition')
                saved_cfg = {key: query(key) for key in keys}
                for field, value in (('-HomProc.OMSL', 0), ('-MtnCmd_.DISV', 1), ('-MtnCmd_.DISA', 1),
                                     ('-HomUseHVEL', 0), ('-HomProc', sequence),
                                     ('-HomPos', cfg['home_position']), ('-VelToHom', cfg['search_velocity']),
                                     ('-VelFrmHom', cfg['edge_velocity']), ('-AccHom', cfg['acceleration'])):
                    rig.client.put(rig.prefix+axis+field, value)
                for key, value in (('HomeSeqId', sequence), ('HomePosition', cfg['home_position']),
                                   ('HomeVelTowardsCam', cfg['search_velocity']), ('HomeVelOffCam', cfg['edge_velocity']),
                                   ('HomeAcc', cfg['acceleration']), ('HomeDec', cfg['deceleration']),
                                   ('HomePostMoveEnable', int(post)), ('HomePostMoveTargetPosition', cfg['post_move_position'])):
                    config(key, value)
                rig.client.put(rig.prefix+axis+rig.encoder_force_suffix(), 1)
                wait_checked(rig, lambda: rig.get(axis, '-Enc02-Ready') == 1
                             and rig.get(axis, '-SetEncIdCmd-RB') == 2, 'BiSS ready for measured homing travel', 10)
                raw_name = rig.prefix+cfg['raw_position']
                raw = rig.client.get(raw_name)
                travel, displacement = 0., 0.
                other = rig.get('TR_LO', '-PosAct')
                saw_limit, saw_unhomed, saw_post = False, False, False
                post_start_displacement = None
                limit = '-LimBwd' if sequence == 1 else '-LimFwd'
                def watch():
                    nonlocal raw, travel, displacement, saw_limit, saw_unhomed, saw_post, post_start_displacement
                    value = rig.client.get(raw_name)
                    modulus = 2**cfg['raw_bits']
                    delta = ((value-raw+modulus/2) % modulus-modulus/2)/cfg['raw_counts_per_mm']
                    raw = value
                    travel += abs(delta)
                    displacement += delta
                    homed = rig.get(axis, '-Homed')
                    if homed == 0: saw_unhomed = True
                    if not rig.get(axis, limit): saw_limit = True
                    if abs(displacement) > cfg['max_search_travel'] or travel > cfg['max_total_travel']:
                        raise AssertionError('real homing exceeded the measured travel budget')
                    if not math.isfinite(displacement): raise AssertionError('invalid EL5042 homing travel')
                    if abs(rig.get('TR_LO', '-PosAct')-other) > rig.profile['tolerance']:
                        raise AssertionError('LO moved during HI homing')
                    if post and saw_unhomed and homed and post_start_displacement is None:
                        post_start_displacement = displacement
                    if post and saw_unhomed and homed and rig.get(axis, '-Busy'):
                        if rig.get(axis, '-PosAct') > cfg['home_position']+.05:
                            saw_post = True
                            if rig.get(axis, '.DMOV') or (complete is not None and complete.is_set()):
                                raise AssertionError('motor record completed before the post-home move ended')
                rig.homing_watch = watch
                rig.client.put(rig.prefix+axis+'-EnaCmd', 1)
                wait_checked(rig, lambda: rig.get(axis, '-EnaAct') == 1, 'HI enabled for limit homing', 10)
                if interface == 'motor':
                    complete = rig.client.put(rig.prefix+axis+('.HOMR' if sequence == 1 else '.HOMF'), 1, wait=False)
                else:
                    for field, value in (('-ExeCmd', 0), ('-MtnCmd', 10), ('-MtnCmdData', sequence), ('-ExeCmd', 1)):
                        rig.client.put(rig.prefix+axis+field, value)
                wait_checked(rig, lambda: rig.get(axis, '-Busy') == 1 and rig.get(axis, '.DMOV') == 0
                             and rig.get(axis, '.MOVN') == 1 and rig.get(axis, '-Homed') == 0,
                             'real limit homing starts and clears Homed', 5)
                expected = cfg['post_move_position'] if post else cfg['home_position']
                wait_checked(rig, lambda: motor_idle(rig, (axis,)) and rig.get(axis, '-Homed') == 1
                             and rig.get(axis, '-SeqState') == 0 and rig.get(axis, limit) == 1
                             and abs(rig.get(axis, '-PosAct')-expected) <= rig.profile['tolerance']
                             and (complete is None or complete.is_set()),
                             'real limit homing and optional post move complete', cfg['timeout'])
                if not saw_limit or not saw_unhomed: raise AssertionError('homing did not observe the real limit/home transition')
                if post and not saw_post: raise AssertionError('post-home movement was not observed')
                if post:
                    expected_post = cfg['post_move_position']-cfg['home_position']
                    actual_post = displacement-post_start_displacement
                    if not .8*expected_post <= actual_post <= 1.2*expected_post:
                        raise AssertionError('EL5042 raw counts did not confirm the post-home physical displacement')
                rig.trace.append({'action': 'real limit homing completed', 'axis': axis, 'sequence': sequence,
                                  'interface': interface, 'post_move': post, 'home_position': cfg['home_position'],
                                  'expected_final_position': expected, 'travel': travel,
                                  'raw_displacement': displacement, 'post_start_displacement': post_start_displacement, 'snapshot': rig.snapshot()})
            finally:
                # Keep feedback powered if standstill cannot be established.
                errors, stopped = [], False
                try:
                    rig.stop_all(retry=True)
                    rig.wait_configuration(rig.idle, 'homing cleanup standstill')
                    rig.disable_axis(axis)
                    stopped = True
                except Exception as error: errors.append(str(error))
                if stopped:
                    rig.homing_watch = None
                    for field, value in saved_fields.items():
                        try: rig.client.put(rig.prefix+axis+field, value)
                        except Exception as error: errors.append(str(error))
                    for key, value in saved_cfg.items():
                        try: config(key, value)
                        except Exception as error: errors.append(str(error))
                    if saved_cfg:
                        try: rig.text_command(f'Cfg.SelectAxisEncConfig({number},{int(previous_encoder)})')
                        except Exception as error: errors.append(str(error))
                    try: rig.client.put(rig.prefix+axis+rig.encoder_force_suffix(), saved_hold)
                    except Exception as error: errors.append(str(error))
                try: rig.close_text_commands(transport)
                except Exception as error: errors.append(str(error))
                if errors: raise RuntimeError('hardware homing cleanup: '+'; '.join(errors))

    def test_hi_low_limit_native(self): self.exercise(1, 'native')
    def test_hi_high_limit_native(self): self.exercise(2, 'native')
    def test_hi_low_limit_motor(self): self.exercise(1, 'motor')
    def test_hi_high_limit_motor(self): self.exercise(2, 'motor')
    def test_hi_low_limit_postmove_native(self): self.exercise(1, 'native', post=True)
    def test_hi_low_limit_postmove_motor(self): self.exercise(1, 'motor', post=True)


HOMING_NAMES = tuple(name for name in dir(HomingTests) if name.startswith('test_'))
