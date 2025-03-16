#include "types.h"
#include "riscv.h"
#include "defs.h"
#include "debug.h"
#include "param.h"

static enum debug_mode_t mode = MP2_DEFAULT_DEBUG_MODE;

void debugswitch(void)
{
  mode = (enum debug_mode_t) !mode;
  printf("Switch debug mode to %d\n", mode);
}

enum debug_mode_t get_mode()
{
  return mode;
}

uint64
sys_debugswitch(void)
{
  debugswitch();
  return 0;
}
