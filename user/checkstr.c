#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fs.h"
#include "kernel/fcntl.h"
#include "user/user.h"

#define MAX_SIZE 1024

int main(int argc, char *argv[])
{
  int fd;
  char buf[MAX_SIZE];
  int n;

  if (argc != 3)
  {
    printf("Usage: %s <filename> <string>\n", argv[0]);
    exit(0);
  }

  fd = open(argv[1], O_RDONLY);
  if (fd < 0)
  {
    printf("Error: cannot open file '%s'\n", argv[1]);
    printf("[MP2] <FAILED> no file %s\n", argv[1]);
    exit(1);
  }

  n = read(fd, buf, MAX_SIZE - 1);
  if (n < 0)
  {
    printf("Error: cannot read file '%s'\n", argv[1]);
    close(fd);
    printf("[MP2] <FAILED> no read\n");
    exit(1);
  }
  buf[n] = '\0';

  close(fd);

  if (n > 0 && buf[n - 1] == '\n')
  {
    buf[n - 1] = '\0';
  }

  if (strcmp(buf, argv[2]) == 0)
  {
    printf("Contents match: '%s' equals '%s'\n", buf, argv[2]);
  }
  else
  {
    printf("Contents differ: '%s' != '%s'\n", buf, argv[2]);
    printf("[MP2] <FAILED> mismatch %s (%s)\n", buf, argv[1]);
    exit(1);
  }

  exit(0);
}
