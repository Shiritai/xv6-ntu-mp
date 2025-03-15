#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

#define BUF_SIZE 512

int main(int argc, char *argv[])
{
  if (argc < 2)
  {
    fprintf(2, "Usage: tee <file>\n");
    exit(1);
  }

  int fd = open(argv[1], O_CREATE | O_WRONLY);
  if (fd < 0)
  {
    fprintf(2, "tee: cannot open %s\n", argv[1]);
    exit(1);
  }

  char buf[BUF_SIZE];
  int n;
  while ((n = read(0, buf, sizeof(buf))) > 0)
  {
    // write stdout
    write(1, buf, n);
    // write file
    write(fd, buf, n);
  }

  if (n < 0)
  {
    fprintf(2, "tee: read error\n");
  }

  close(fd);
  exit(0);
}
