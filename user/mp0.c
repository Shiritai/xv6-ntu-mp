#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fs.h"

void mp0(char *root, char key)
{
    // TODO: implement mp0
    // Hint: Use pipe, fork, and walk
    printf("%s [error opening dir]\n", root); // Placeholder behavior
    printf("\n0 directories, 0 files\n");
}

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        printf("usage: mp0 <root_directory> <key>\n");
        exit(1);
    }
    mp0(argv[1], *argv[2]);
    exit(0);
}
