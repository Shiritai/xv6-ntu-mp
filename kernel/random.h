#pragma once

#include "types.h"

static uint rand_seed = 123;

uint rand(void)
{
  rand_seed = (109 * rand_seed + 1) & 0xfff;
  return rand_seed;
}
