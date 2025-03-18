#pragma once

#include "debug.h"
#include "defs.h"
#include "slab.h"

void check()
{
  debug("[MP2] Slab size: %lu\n", sizeof(struct slab) / sizeof(void *));
}
