
#- Watchdog configuration.
#- Default: 100 ms, independent of EtherCAT sample rate.
#- Timeout = (divider + 2) * 40 ns * intervals.

ecmcConfigOrDie "Cfg.EcSlaveConfigWatchDog(${ECMC_EC_SLAVE_NUM},${WATCHDOG_DIVIDER=2498},${WATCHDOG_INTERVALS=1000})"