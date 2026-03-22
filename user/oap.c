#include "kernel/types.h"
#include "user/user.h"
#include "user/ok.h"

int main(int argc, char *argv[])
{
  char buf[512];

  read_until_match("Ok", buf, sizeof(buf));
  printfslab();
  printf("Ok");

  exit(0);
}
