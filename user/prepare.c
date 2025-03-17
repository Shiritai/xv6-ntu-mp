#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fs.h"
#include "kernel/fcntl.h"
#include "user/user.h"

void makedir(char *dirname)
{
  if (mkdir(dirname) < 0)
  {
    fprintf(2, "mkdir %s failed.", dirname);
    exit(1);
  }
}

int main(int argc, char *argv[])
{
  makedir("os");
  makedir("os2025");
  makedir("meow");
  makedir("test");
  makedir("dir");
  
  printf("Ok");
  exit(0);
}
