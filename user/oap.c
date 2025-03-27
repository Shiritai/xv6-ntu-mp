#include "kernel/types.h"
#include "user/user.h"

int main(int argc, char *argv[])
{
  char buf[512];
  int n;

  while ((n = read(0, buf, sizeof(buf))) > 0)
  {
    if (!strcmp(buf, "Ok"))
    {
      printfslab();
      sleep(2);
      printf("Ok");
      break;
    }
  }

  exit(0);
}
