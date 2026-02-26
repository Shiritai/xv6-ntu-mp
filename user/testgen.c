#include "kernel/types.h"
#include "kernel/fcntl.h"
#include "kernel/stat.h"
#include "user/user.h"

void mkfile(char *filename) {
    int fd = open(filename, O_CREATE | O_RDWR);
    write(fd, "hi", 3);
    close(fd);
}

void mkd(char *dirname) {
    if (mkdir(dirname) < 0) {
        fprintf(2, "mkdir %s failed.", dirname);
        exit(1);
    }
}
void test0() {
    mkd("os2023");

    mkd("os2023/d1");
    mkd("os2023/d2");
    mkd("os2023/d3");

    mkd("os2023/d2/a");
    mkd("os2023/d2/b");
    mkfile("os2023/d2/c");

    mkd("os2023/d3/a");
    mkfile("os2023/d3/b");
}

void test1() {
    mkd("a");
    mkd("a/0");
    mkd("a/1");
    mkd("a/2");
    mkd("a/3");
    mkd("a/4");
    mkd("a/5");
    mkd("a/6");
    mkd("a/7");
    mkd("a/8");
    mkd("a/9");
    mkd("a/10");
}

void test2() {
    mkd("sdnjk2nj18");
    mkd("sdnjk2nj18/aaaaaaaa01");
    mkd("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02");
    mkd("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03");
    mkd("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/aaaaaaaa04");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz00");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz01");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz02");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz03");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz04");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz05");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz06");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz07");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz08");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz09");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz11");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz12");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz13");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz14");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz15");
    mkfile("sdnjk2nj18/aaaaaaaa01/aaaaaaaa02/aaaaaaaa03/zzzzzzzz16");
}
void test3() {
    mkd("b24dd5eac6");
    mkd("b24dd5eac6/cd938f3100");
    mkd("b24dd5eac6/cc938f3101");
    mkd("b24dd5eac6/ccc38f3102");
    mkd("b24dd5eac6/cccc8f3103");
    mkd("b24dd5eac6/cccccf3104");
    mkd("b24dd5eac6/cccccc3105");
    mkd("b24dd5eac6/ccccccc106");
    mkd("b24dd5eac6/cccccccc07");
    mkd("b24dd5eac6/bd938f3108");
    mkd("b24dd5eac6/bd938f3109");
    mkd("b24dd5eac6/bd938f3110");
    mkd("b24dd5eac6/bd938f3111");
    mkd("b24dd5eac6/bd938f3112");
    mkd("b24dd5eac6/bd938f3113");
    mkd("b24dd5eac6/bd938f3114");
    mkd("b24dd5eac6/bd938f3115");
    mkd("b24dd5eac6/bd938f3116");
    mkd("b24dd5eac6/bd938f3117");
    mkd("b24dd5eac6/bd938f3118");
    mkd("b24dd5eac6/bd938f3119");
}

int main(int argc, char *argv[]) {
    test0();
    test1();
    test2();
    test3();
    exit(0);
}
