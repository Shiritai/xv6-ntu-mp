#pragma once

#include <stdarg.h>
#include "defs.h"

/**
 * enum debug_mode_t - Debug mode states
 * @OFF: Debug mode is disabled (value: 0)
 * @ON: Debug mode is enabled (value: 1)
 *
 * Enumeration defining the possible states of the debug mode.
 */
enum debug_mode_t
{
  OFF,
  ON
};

/**
 * debugswitch - Switch debug mode on or off
 *
 * Toggles the current debug mode between %OFF and %ON states.
 * This function does not take any parameters and has no return value.
 */
void debugswitch(void);

/**
 * get_mode - Retrieve the current debug mode
 *
 * Returns the current state of the debug mode as defined by &enum debug_mode_t.
 *
 * Return: %OFF (0) if debug mode is off, %ON (1) if debug mode is on
 */
enum debug_mode_t get_mode(void);

/**
 * sys_debugswitch - System call to switch debug mode
 *
 * Provides the system call interface to toggle the debug mode.
 * This function is intended to be invoked via a syscall mechanism.
 *
 * Return: 0 on success, or an error code on failure
 */
uint64 sys_debugswitch(void);

/**
 * debug - Print a debug message if debug mode is enabled
 * @fmt: Format string (same as printf)
 * @...: Variable arguments corresponding to the format string
 *
 * Prints a debug message to the console if get_mode() returns %ON (1).
 * If debug mode is %OFF (0), no output occurs and the macro evaluates to 0.
 * The usage mirrors that of printf(), supporting the same format specifiers
 * and variable arguments.
 *
 * Return: Number of characters printed, or 0 if debug mode is off
 */
#define debug(fmt, ...) \
    ((get_mode()) == OFF ? 0 : printf(fmt, ##__VA_ARGS__))

