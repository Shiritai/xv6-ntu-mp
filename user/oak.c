#include "kernel/types.h"
#include "user/user.h"
#include "user/ok.h"

int main(int argc, char *argv[])
{
  char buf[512];
  int pid_to_kill = 0;

  if (!(argc == 2 && !strcmp(argv[1], "end")))
  {
    printf("%d", getpid());
  }

  read_until_match("Ok", buf, sizeof(buf));
  pid_to_kill = atoi(buf);
  kill(pid_to_kill);
  printf("Ok");

  exit(0);
}
