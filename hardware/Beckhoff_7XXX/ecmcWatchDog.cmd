#- Watchdog configuration: 200 ms default, independent of EtherCAT sample rate.
#- Timeout [ns] = (divider + 2) * 40 * intervals.
#- Override WATCHDOG_DIVIDER or WATCHDOG_INTERVALS for device-specific needs.
ecmcConfigOrDie "Cfg.EcSlaveConfigWatchDog(${ECMC_EC_SLAVE_NUM},${WATCHDOG_DIVIDER=2498},${WATCHDOG_INTERVALS=2000})"
