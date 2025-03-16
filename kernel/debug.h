#pragma once

#include <stdarg.h>
#include "defs.h"

enum debug_mode_t
{
  OFF,
  ON
};

void debugswitch(void);
enum debug_mode_t get_mode(void);
uint64 sys_debugswitch(void);

#define debug(fmt, ...) \
    ((get_mode()) == OFF ? 0 : printf(fmt, ##__VA_ARGS__))

