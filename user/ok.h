#include "kernel/types.h"
#include "user/user.h"

#define READ_CACHE_SIZE 512

/**
 * Monitor stdin and return until received a `match` (case sensitive).
 * Store the string from stdin in `buf` before receiving a `match`.
 * @param match: String to match
 * @param buf: Buffer to store received stdin excluding `match`
 * @param buf_sz: Buffer size
 * @return: 0 on success (match found), -1 on error or EOF without match
 */
int read_until_match(const char *match, char *buf, uint buf_sz)
{
  if (!match || buf_sz == 0)
  {
    if (buf && buf_sz > 0)
      buf[0] = '\0';
    return -1;
  }

  uint buf_idx = 0;
  const uint match_len = strlen(match);
  char cache[READ_CACHE_SIZE];
  int bytes_read;
  uint match_pos = 0;

  if (buf_sz <= match_len)
  {
    buf[0] = '\0';
    return -1; // Buffer too small
  }

  buf[buf_sz - 1] = '\0';

  while ((bytes_read = read(0, cache, sizeof(cache))) > 0)
  {
    for (uint i = 0; i < (uint)bytes_read; ++i)
    {
      if (buf_idx < buf_sz - 1)
      {
        buf[buf_idx++] = cache[i];
      }
      if (cache[i] == match[match_pos])
      {
        ++match_pos;
        if (match_pos == match_len)
          break;
      }
      else
      {
        match_pos = 0;
        if (cache[i] == match[0])
        {
          match_pos = 1;
          if (match_pos == match_len)
            break;
        }
      }
    }
    if (match_pos == match_len)
      break;
  }

  if (bytes_read < 0)
  {
    buf[0] = '\0';
    return -1; // Read error
  }
  if (match_pos < match_len)
  {
    buf[buf_idx] = '\0';
    return -1; // EOF without match
  }
  buf[buf_idx - match_len] = '\0';
  return 0; // Success
}
