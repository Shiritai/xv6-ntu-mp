#include "kernel/types.h"
#include "user/user.h"

/**
 * Monitor stdin and return until received a `match` (case sensitive).
 * Store the string from stdin in `buf` before receiving a `match`.
 * @param buf: buffer to store received stdin excluding `match`
 * @param buf_sz: buffer size
 */
void read_until_match(const char *match, char *buf, uint buf_sz)
{
  uint bi = 0; // buffer index
  const uint tar_len = strlen(match);
  char cache[512];
  uint n;
  uint has_read = 0;

  buf[buf_sz - 1] = '\0';

  while ((n = read(0, cache, sizeof(cache))) > 0)
  {
    for (uint i = 0; i < n; ++i)
    {
      if (bi < buf_sz)
        buf[bi++] = cache[i];          // if the buffer is not full, store char into buf
      if (cache[i] == match[has_read]) // matched
      {
        ++has_read;
        if (has_read == tar_len)
          break; // fully matched
      }
      else
      {
        has_read = 0;                    // found not matched, reset read index
        if (cache[i] == match[has_read]) // check from start (for single word matching case)
        {
          ++has_read;
          if (has_read == tar_len)
            break; // fully matched
        }
      }
    }
    if (has_read == tar_len)
      break; // fully matched
  }

  buf[bi - tar_len] = '\0';
}
