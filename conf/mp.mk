# MP-specific Makefile configurations
# Add your user programs here, e.g.:
# CFLAGS += -DMP_ID
CFLAGS += -DMP2_DEFAULT_DEBUG_MODE=0

OBJS += $K/slab.o

UPROGS += \
	$U/_mp2\
	$U/_oak\
	$U/_oap\
	$U/_prepare\
	$U/_tee\
	$U/_checkstr\
	$U/_gah
