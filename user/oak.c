#include "kernel/types.h"
#include "user/user.h"

int main(int argc, char *argv[])
{
  char buf[512];
  int n;
  int pid_to_kill = 0;

  if (!(argc == 2 && !strcmp(argv[1], "end"))) {
    printf("%d", getpid());
  }

  while ((n = read(0, buf, sizeof(buf))) > 0)
  {
    if (!strcmp(buf, "Ok"))
    {
      printf("Ok");
      kill(pid_to_kill);
      break;
    }
    else
    {
      pid_to_kill = atoi(buf);
    }
  }

  exit(0);
}
